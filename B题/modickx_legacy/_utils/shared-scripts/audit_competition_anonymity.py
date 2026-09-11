#!/usr/bin/env python3
"""Fail-closed anonymity audit for competition papers and support packages.

The identity ledger is an external input.  Its literal values are never copied
to the audit report, staging tree, or archive.  Findings expose only category,
location, and a one-way fingerprint of the matched value.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
from xml.etree import ElementTree


AUDIT_NAME = "ANONYMITY_AUDIT.json"
DEFAULT_MAIN_PAGE_LIMIT = 30
MAX_NESTED_ARCHIVE_DEPTH = 2
MAX_MEMBER_BYTES = 64 * 1024 * 1024
TEXT_SUFFIXES = {
    ".bib",
    ".cfg",
    ".csv",
    ".ini",
    ".json",
    ".log",
    ".md",
    ".py",
    ".r",
    ".rmd",
    ".tex",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
OOXML_SUFFIXES = {".docx", ".pptx", ".xlsx", ".xlsm"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
UNINSPECTABLE_ARCHIVE_SUFFIXES = {".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"}

PLEDGE_MARKERS = (
    "承诺书",
    "诚信承诺",
    "参赛承诺",
    "honor pledge",
    "honour pledge",
    "commitment form",
)
NUMBER_PAGE_MARKERS = (
    "参赛编号",
    "队伍编号",
    "团队编号",
    "team control number",
    "team number page",
)
GENERIC_AUTHOR_VALUES = {
    "",
    "anonymous",
    "anonymous author",
    "anonymous authors",
    "none",
    "unknown",
    "匿名",
}
PERSONAL_PATH_PATTERNS = (
    re.compile(r"(?i)[a-z]:[\\/]users[\\/][^\\/\s]+"),
    re.compile(r"/Users/[^/\s]+"),
    re.compile(r"/home/[^/\s]+"),
)
LABELED_ID_PATTERNS = (
    re.compile(r"(?:参赛编号|队伍编号|团队编号)\s*[:：]\s*[A-Za-z0-9_-]{3,}"),
    re.compile(r"(?i)team\s+(?:control\s+)?number\s*[:：]\s*[A-Za-z0-9_-]{3,}"),
)
APPENDIX_HEADING = re.compile(
    r"(?im)^\s*(?:附录(?:\s*[A-Z一二三四五六七八九十0-9])?|appendix(?:\s+[A-Z0-9])?)\s*(?:[:：].*)?$"
)
ABSTRACT_MARKER = re.compile(r"(?i)(?:摘\s*要|abstract|summary\s+sheet)")


class AnonymityAuditError(ValueError):
    """Raised when the audit cannot prove a clean anonymous delivery."""


@dataclass(frozen=True)
class IdentityTerm:
    category: str
    value: str
    fingerprint: str


@dataclass(frozen=True)
class Finding:
    code: str
    location: str
    category: str | None = None
    fingerprint: str | None = None
    page: int | None = None
    field: str | None = None

    def public(self) -> dict[str, object]:
        payload: dict[str, object] = {"code": self.code, "location": self.location}
        if self.category is not None:
            payload["category"] = self.category
        if self.fingerprint is not None:
            payload["term_fingerprint"] = self.fingerprint
        if self.page is not None:
            payload["page"] = self.page
        if self.field is not None:
            payload["field"] = self.field
        return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def load_identity_ledger(path: Path) -> tuple[list[IdentityTerm], dict[str, int]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AnonymityAuditError(f"identity ledger is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise AnonymityAuditError("identity ledger must use schema_version 1")
    categories = payload.get("identity_categories")
    if not isinstance(categories, dict) or not categories:
        raise AnonymityAuditError("identity ledger requires a non-empty identity_categories object")

    terms: list[IdentityTerm] = []
    counts: dict[str, int] = {}
    for category, values in sorted(categories.items()):
        if not isinstance(category, str) or not category.strip():
            raise AnonymityAuditError("identity ledger categories must be non-empty strings")
        if not isinstance(values, list):
            raise AnonymityAuditError(f"identity category must be a list: {category}")
        unique: set[str] = set()
        for value in values:
            if not isinstance(value, str) or len(value.strip()) < 2:
                raise AnonymityAuditError(
                    f"identity values must contain at least two visible characters: {category}"
                )
            normalized = value.strip()
            if normalized in unique:
                continue
            unique.add(normalized)
            terms.append(IdentityTerm(category, normalized, _fingerprint(normalized)))
        counts[category] = len(unique)
    if not terms:
        raise AnonymityAuditError("identity ledger contains no forbidden identity values")
    return terms, counts


def _decode_text(data: bytes) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return None


def _identity_findings(text: str, location: str, terms: Iterable[IdentityTerm]) -> list[Finding]:
    findings: list[Finding] = []
    folded = text.casefold()
    for term in terms:
        if term.value.casefold() in folded:
            findings.append(
                Finding("identity_literal", location, term.category, term.fingerprint)
            )
    for pattern in PERSONAL_PATH_PATTERNS:
        if pattern.search(text):
            findings.append(Finding("personal_home_path", location))
            break
    for pattern in LABELED_ID_PATTERNS:
        if pattern.search(text):
            findings.append(Finding("labeled_team_identifier", location))
            break
    return findings


def _forbidden_page_findings(
    text: str,
    location: str,
    page: int,
    *,
    formal_paper: bool,
) -> list[Finding]:
    folded = text.casefold()
    findings: list[Finding] = []
    pledge_marker = any(marker.casefold() in folded for marker in PLEDGE_MARKERS)
    pledge_structure = any(
        marker in folded
        for marker in ("签名", "签字", "承诺人", "参赛队员", "signature", "date:")
    )
    if pledge_marker and (formal_paper or pledge_structure):
        findings.append(Finding("pledge_page_forbidden", location, page=page))
    number_marker = any(marker.casefold() in folded for marker in NUMBER_PAGE_MARKERS)
    number_structure_hits = sum(
        marker in folded
        for marker in ("题号", "所属类别", "组别", "学校", "队员", "problem", "school")
    )
    if number_marker and (formal_paper or number_structure_hits >= 2):
        findings.append(Finding("number_page_forbidden", location, page=page))
    return findings


def _path_findings(location: str, terms: Iterable[IdentityTerm]) -> list[Finding]:
    findings = _identity_findings(location, location, terms)
    folded = location.casefold()
    if any(marker.casefold() in folded for marker in PLEDGE_MARKERS):
        findings.append(Finding("pledge_artifact_forbidden", location))
    if any(marker.casefold() in folded for marker in NUMBER_PAGE_MARKERS):
        findings.append(Finding("number_page_artifact_forbidden", location))
    return findings


def audit_label(label: str, terms: Iterable[IdentityTerm]) -> list[Finding]:
    """Audit a filename or directory label that may be copied into a report."""

    return _path_findings(label, terms)


def _require_pypdf():
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - exercised only in deficient runtimes
        raise AnonymityAuditError("pypdf is required to inspect PDF text and metadata") from exc
    return PdfReader


def _audit_pdf_bytes(
    data: bytes,
    location: str,
    terms: Iterable[IdentityTerm],
    *,
    formal_paper: bool,
) -> tuple[list[Finding], int, list[str]]:
    PdfReader = _require_pypdf()
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise AnonymityAuditError(f"cannot inspect PDF: {location}") from exc
    findings: list[Finding] = []
    metadata = reader.metadata or {}
    for key, raw_value in metadata.items():
        value = "" if raw_value is None else str(raw_value)
        field = str(key).lstrip("/")
        findings.extend(
            Finding(item.code, item.location, item.category, item.fingerprint, field=field)
            for item in _identity_findings(value, location, terms)
        )
        if field.casefold() == "author" and value.strip().casefold() not in GENERIC_AUTHOR_VALUES:
            findings.append(Finding("nonanonymous_document_author", location, field=field))

    pages = list(reader.pages)
    page_texts: list[str] = []
    for index, page in enumerate(pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise AnonymityAuditError(f"cannot extract PDF page {index}: {location}") from exc
        page_texts.append(text)
        page_location = f"{location}#page={index}"
        findings.extend(_identity_findings(text, page_location, terms))
        findings.extend(
            _forbidden_page_findings(
                text,
                location,
                index,
                formal_paper=formal_paper,
            )
        )
        if formal_paper and index == 1 and len(re.sub(r"\s+", "", text)) < 20:
            findings.append(Finding("paper_first_page_not_verifiably_content_page", location, page=1))
    if formal_paper and not pages:
        findings.append(Finding("paper_has_no_pages", location))
    return findings, len(pages), page_texts


def _xml_text(data: bytes) -> str:
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
        decoded = _decode_text(data)
        return decoded or ""
    return "\n".join(value for value in root.itertext() if value)


def _audit_ooxml_bytes(
    data: bytes, location: str, terms: Iterable[IdentityTerm]
) -> list[Finding]:
    findings: list[Finding] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            if package.testzip() is not None:
                raise AnonymityAuditError(f"OOXML CRC check failed: {location}")
            for info in package.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".xml"):
                    continue
                if info.file_size > MAX_MEMBER_BYTES:
                    raise AnonymityAuditError(f"OOXML member is too large to inspect: {location}")
                text = _xml_text(package.read(info))
                member_location = f"{location}!/{info.filename}"
                findings.extend(_identity_findings(text, member_location, terms))
                if info.filename in {"docProps/core.xml", "docProps/app.xml"}:
                    try:
                        root = ElementTree.fromstring(package.read(info))
                    except ElementTree.ParseError:
                        continue
                    for node in root.iter():
                        field = node.tag.rsplit("}", 1)[-1]
                        value = (node.text or "").strip()
                        if field.casefold() in {"creator", "lastmodifiedby", "company", "manager"}:
                            if value.casefold() not in GENERIC_AUTHOR_VALUES:
                                findings.append(
                                    Finding(
                                        "nonanonymous_document_property",
                                        location,
                                        field=field,
                                    )
                                )
    except zipfile.BadZipFile as exc:
        raise AnonymityAuditError(f"cannot inspect OOXML package: {location}") from exc
    return findings


def _audit_image_bytes(
    data: bytes, location: str, terms: Iterable[IdentityTerm]
) -> list[Finding]:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - exercised only in deficient runtimes
        raise AnonymityAuditError("Pillow is required to inspect image metadata") from exc
    findings: list[Finding] = []
    try:
        with Image.open(io.BytesIO(data)) as image:
            metadata_values = [str(value) for value in image.info.values()]
            exif = image.getexif()
            metadata_values.extend(str(value) for value in exif.values())
            if 34853 in exif:  # GPSInfo
                findings.append(Finding("image_gps_metadata", location, field="GPSInfo"))
    except Exception as exc:
        raise AnonymityAuditError(f"cannot inspect image metadata: {location}") from exc
    findings.extend(_identity_findings("\n".join(metadata_values), location, terms))
    return findings


def _audit_zip_bytes(
    data: bytes,
    location: str,
    terms: list[IdentityTerm],
    *,
    depth: int,
) -> tuple[list[Finding], int]:
    if depth > MAX_NESTED_ARCHIVE_DEPTH:
        raise AnonymityAuditError(f"nested ZIP depth exceeds audit limit: {location}")
    findings: list[Finding] = []
    inspected = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            if bundle.testzip() is not None:
                raise AnonymityAuditError(f"ZIP CRC check failed: {location}")
            for info in bundle.infolist():
                member_location = f"{location}!/{info.filename}"
                findings.extend(_path_findings(member_location, terms))
                if info.is_dir():
                    continue
                if info.file_size > MAX_MEMBER_BYTES:
                    raise AnonymityAuditError(f"ZIP member is too large to inspect: {member_location}")
                member_data = bundle.read(info)
                nested, nested_count = _audit_bytes(
                    member_data,
                    member_location,
                    PurePosixPath(info.filename).suffix.lower(),
                    terms,
                    formal_paper=False,
                    depth=depth,
                )
                findings.extend(nested)
                inspected += 1 + nested_count
    except zipfile.BadZipFile as exc:
        raise AnonymityAuditError(f"cannot inspect ZIP: {location}") from exc
    return findings, inspected


def _audit_bytes(
    data: bytes,
    location: str,
    suffix: str,
    terms: list[IdentityTerm],
    *,
    formal_paper: bool,
    depth: int,
) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    if suffix == ".pdf":
        pdf_findings, _, _ = _audit_pdf_bytes(
            data, location, terms, formal_paper=formal_paper
        )
        findings.extend(pdf_findings)
    elif suffix in OOXML_SUFFIXES:
        findings.extend(_audit_ooxml_bytes(data, location, terms))
    elif suffix == ".zip":
        nested, nested_count = _audit_zip_bytes(data, location, terms, depth=depth + 1)
        findings.extend(nested)
        return findings, nested_count
    elif suffix in UNINSPECTABLE_ARCHIVE_SUFFIXES:
        findings.append(Finding("uninspectable_nested_archive", location))
    elif suffix in IMAGE_SUFFIXES:
        findings.extend(_audit_image_bytes(data, location, terms))
    elif suffix in TEXT_SUFFIXES or not suffix:
        decoded = _decode_text(data)
        if decoded is not None:
            findings.extend(_identity_findings(decoded, location, terms))
    return findings, 0


def audit_tree(
    root: Path,
    terms: list[IdentityTerm],
    *,
    exclude: Iterable[Path] = (),
) -> tuple[list[Finding], int]:
    excluded = {item.resolve() for item in exclude}
    findings: list[Finding] = []
    inspected = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise AnonymityAuditError(f"symbolic links cannot be audited safely: {path}")
        if not path.is_file() or path.resolve() in excluded:
            continue
        location = path.relative_to(root).as_posix()
        findings.extend(_path_findings(location, terms))
        nested, nested_count = _audit_bytes(
            path.read_bytes(),
            location,
            path.suffix.lower(),
            terms,
            formal_paper=False,
            depth=0,
        )
        findings.extend(nested)
        inspected += 1 + nested_count
    return findings, inspected


def _paper_page_budget(
    page_texts: list[str],
    *,
    main_page_limit: int,
    appendix_start_page: int | None,
    abstract_pages_excluded: int,
) -> tuple[list[Finding], int, int | None]:
    findings: list[Finding] = []
    total_pages = len(page_texts)
    detected_start = appendix_start_page
    if detected_start is None:
        for index, text in enumerate(page_texts, start=1):
            if APPENDIX_HEADING.search(text):
                detected_start = index
                break
    if detected_start is not None and not 1 <= detected_start <= total_pages:
        findings.append(Finding("invalid_appendix_start_page", "formal-paper.pdf"))
        return findings, total_pages, detected_start
    pages_before_appendix = total_pages if detected_start is None else detected_start - 1
    counted_pages = pages_before_appendix - abstract_pages_excluded
    if counted_pages < 0:
        findings.append(Finding("invalid_abstract_page_exclusion", "formal-paper.pdf"))
        counted_pages = 0
    if counted_pages > main_page_limit:
        findings.append(Finding("main_paper_page_limit_exceeded", "formal-paper.pdf"))
    return findings, counted_pages, detected_start


def audit_formal_paper(
    path: Path,
    terms: list[IdentityTerm],
    *,
    main_page_limit: int = DEFAULT_MAIN_PAGE_LIMIT,
    appendix_start_page: int | None = None,
    abstract_pages_excluded: int = 1,
) -> tuple[list[Finding], int, int, int | None]:
    findings = _path_findings(path.name, terms)
    if path.suffix.lower() != ".pdf":
        findings.append(Finding("formal_paper_must_be_pdf", path.name))
        return findings, 0, 0, None
    nested, page_count, page_texts = _audit_pdf_bytes(
        path.read_bytes(), path.name, terms, formal_paper=True
    )
    findings.extend(nested)
    if page_texts and not ABSTRACT_MARKER.search(page_texts[0]):
        findings.append(Finding("paper_first_page_is_not_verifiably_abstract", path.name, page=1))
    budget_findings, counted_pages, detected_start = _paper_page_budget(
        page_texts,
        main_page_limit=main_page_limit,
        appendix_start_page=appendix_start_page,
        abstract_pages_excluded=abstract_pages_excluded,
    )
    findings.extend(budget_findings)
    return findings, page_count, counted_pages, detected_start


def audit_archive(path: Path, terms: list[IdentityTerm]) -> tuple[list[Finding], int]:
    findings = _path_findings(path.name, terms)
    nested, inspected = _audit_zip_bytes(path.read_bytes(), path.name, terms, depth=0)
    findings.extend(nested)
    return findings, inspected


def build_report(
    *,
    ledger_path: Path,
    category_counts: dict[str, int],
    paper: Path,
    paper_pages: int,
    counted_paper_pages: int,
    main_page_limit: int,
    appendix_start_page: int | None,
    abstract_pages_excluded: int,
    staging_files: int,
    archive_files: int | None,
    findings: list[Finding],
) -> dict[str, object]:
    identity_codes = {
        "identity_literal",
        "personal_home_path",
        "labeled_team_identifier",
        "nonanonymous_document_author",
        "nonanonymous_document_property",
        "image_gps_metadata",
    }
    return {
        "format": "modickx-competition-anonymity-audit",
        "schema_version": 1,
        "status": "ready" if not findings else "blocked",
        "identity_ledger": {
            "sha256": sha256_file(ledger_path),
            "category_counts": category_counts,
            "copied_into_delivery": False,
        },
        "formal_paper": {
            "name": paper.name,
            "total_pages": paper_pages,
            "counted_pages_including_references_excluding_abstract": counted_paper_pages,
            "page_limit_including_references_excluding_abstract": main_page_limit,
            "abstract_pages_excluded": abstract_pages_excluded,
            "appendix_start_page": appendix_start_page,
        },
        "scanned": {
            "paper_files": 1,
            "staging_files_and_nested_members": staging_files,
            "archive_files_and_nested_members": archive_files,
        },
        "hard_gates": {
            "team_identity_in_content_paths_or_properties": "passed"
            if not any(item.code in identity_codes for item in findings)
            else "failed",
            "pledge_page_absent": "passed"
            if not any("pledge" in item.code for item in findings)
            else "failed",
            "contest_number_page_absent": "passed"
            if not any("number_page" in item.code for item in findings)
            else "failed",
            "main_paper_including_references_within_page_limit": "passed"
            if not any(item.code == "main_paper_page_limit_exceeded" for item in findings)
            else "failed",
        },
        "findings": [item.public() for item in findings],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--identity-ledger", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--main-page-limit", type=int, default=DEFAULT_MAIN_PAGE_LIMIT)
    parser.add_argument("--appendix-start-page", type=int)
    parser.add_argument("--abstract-pages-excluded", type=int, default=1)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        paper = args.paper.resolve()
        staging = args.staging.resolve()
        ledger = args.identity_ledger.resolve()
        output = args.output.resolve()
        archive = args.archive.resolve() if args.archive else None
        if not paper.is_file():
            raise AnonymityAuditError(f"formal paper does not exist: {paper}")
        if not staging.is_dir():
            raise AnonymityAuditError(f"staging directory does not exist: {staging}")
        if not ledger.is_file():
            raise AnonymityAuditError(f"identity ledger does not exist: {ledger}")
        if ledger == output or staging in ledger.parents:
            raise AnonymityAuditError("identity ledger must remain outside the delivery staging tree")
        if args.main_page_limit < 1:
            raise AnonymityAuditError("main page limit must be positive")
        if args.abstract_pages_excluded != 1:
            raise AnonymityAuditError("competition paper audit requires exactly one abstract page")
        terms, category_counts = load_identity_ledger(ledger)
        paper_findings, pages, counted_pages, appendix_start_page = audit_formal_paper(
            paper,
            terms,
            main_page_limit=args.main_page_limit,
            appendix_start_page=args.appendix_start_page,
            abstract_pages_excluded=args.abstract_pages_excluded,
        )
        staging_findings, staging_count = audit_tree(staging, terms, exclude=(output, ledger))
        archive_findings: list[Finding] = []
        archive_count: int | None = None
        if archive is not None:
            if not archive.is_file():
                raise AnonymityAuditError(f"archive does not exist: {archive}")
            archive_findings, archive_count = audit_archive(archive, terms)
        findings = paper_findings + staging_findings + archive_findings
        report = build_report(
            ledger_path=ledger,
            category_counts=category_counts,
            paper=paper,
            paper_pages=pages,
            counted_paper_pages=counted_pages,
            main_page_limit=args.main_page_limit,
            appendix_start_page=appendix_start_page,
            abstract_pages_excluded=args.abstract_pages_excluded,
            staging_files=staging_count,
            archive_files=archive_count,
            findings=findings,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if findings:
            raise AnonymityAuditError(
                f"anonymity audit found {len(findings)} blocking item(s); see {output.name}"
            )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (AnonymityAuditError, OSError, zipfile.BadZipFile) as exc:
        print(f"anonymity audit blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
