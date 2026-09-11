#!/usr/bin/env python3
"""Build a clean, reproducible mathematical-modeling support package.

The source tree is read-only.  All removals are limited to an unoccupied staging
directory, and only unambiguous machine caches or build auxiliaries are removed
automatically.  Semantic deletion remains a ``simplify-codebase`` proof task.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable

from audit_competition_anonymity import (
    AUDIT_NAME,
    DEFAULT_MAIN_PAGE_LIMIT,
    AnonymityAuditError,
    audit_archive,
    audit_formal_paper,
    audit_label,
    audit_tree,
    build_report,
    load_identity_ledger,
)
from audit_competition_latex_format import (
    AUDIT_NAME as LATEX_AUDIT_NAME,
    LatexFormatAuditError,
    audit_latex,
)
from integrated_review_gate import (
    GATE_NAME as INTEGRATED_REVIEW_GATE_NAME,
    IntegratedReviewGateError,
    require_ready_gate,
)


MANIFEST_NAME = "SUPPORT_PACKAGE_MANIFEST.json"
CHECKSUM_NAME = "SHA256SUMS.txt"
PAPER_BINDING_NAME = "PAPER_BINDING.json"
CLEANUP_REPORT_NAME = "SUPPORT_PACKAGE_CLEANUP_REPORT.md"
REPRODUCTION_REPORT_NAME = "REPRODUCTION_RUN.json"

IGNORED_DIR_NAMES = {
    ".git",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
}
IGNORED_FILE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
}
IGNORED_SUFFIXES = {
    ".aux",
    ".fdb_latexmk",
    ".fls",
    ".lof",
    ".lot",
    ".nav",
    ".pyo",
    ".pyc",
    ".snm",
    ".synctex.gz",
    ".tmp",
    ".toc",
    ".vrb",
    ".xdv",
}
METADATA_NAMES = {MANIFEST_NAME, CHECKSUM_NAME}


class FinalizationError(ValueError):
    """Raised before a partial delivery can be mistaken for a final package."""


@dataclass(frozen=True)
class FileRecord:
    path: str
    size: int
    sha256: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _md5(path: Path) -> str:
    """Return MD5 for submission-platform correspondence, never for security."""

    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(value: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    relative = PurePosixPath(normalized)
    if (
        not normalized
        or relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or ":" in relative.parts[0]
    ):
        raise FinalizationError(f"path must be relative and remain inside the package: {value}")
    return relative


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _source_snapshot(root: Path) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise FinalizationError(f"source contains a symbolic link: {path.relative_to(root)}")
        if path.is_file():
            stat = path.stat()
            snapshot[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return snapshot


def _ignore_reason(relative: PurePosixPath) -> str | None:
    if any(part in IGNORED_DIR_NAMES for part in relative.parts[:-1]):
        return "machine cache or environment directory"
    if relative.name in IGNORED_FILE_NAMES:
        return "operating-system metadata"
    name = relative.name.lower()
    if any(name.endswith(suffix) for suffix in IGNORED_SUFFIXES):
        return "regenerable cache or build auxiliary"
    return None


def _collect_source_files(root: Path) -> tuple[list[tuple[Path, PurePosixPath]], list[dict[str, str]]]:
    included: list[tuple[Path, PurePosixPath]] = []
    excluded: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise FinalizationError(f"source contains a symbolic link: {path.relative_to(root)}")
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(root).as_posix())
        reason = _ignore_reason(relative)
        if reason:
            excluded.append({"path": relative.as_posix(), "reason": reason})
        else:
            included.append((path, relative))
    return included, excluded


def _remove_regenerable_artifacts(root: Path) -> list[dict[str, str]]:
    removed: list[dict[str, str]] = []
    for path in sorted(root.rglob("*"), reverse=True):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if path.is_symlink():
            raise FinalizationError(f"reproduction created a symbolic link: {relative}")
        if path.is_file():
            reason = _ignore_reason(relative)
            if reason:
                path.unlink()
                removed.append({"path": relative.as_posix(), "reason": reason})
        elif path.is_dir() and path.name in IGNORED_DIR_NAMES:
            shutil.rmtree(path)
            removed.append(
                {"path": relative.as_posix() + "/", "reason": "machine cache or environment directory"}
            )
    return removed


def _records(root: Path, *, exclude: set[str] | None = None) -> list[FileRecord]:
    skipped = exclude or set()
    records: list[FileRecord] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise FinalizationError(f"staging contains a symbolic link: {path.relative_to(root)}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in skipped:
            continue
        records.append(FileRecord(relative, path.stat().st_size, _sha256(path)))
    return records


def _ensure_required(root: Path, required: Iterable[PurePosixPath]) -> None:
    missing = [item.as_posix() for item in required if not (root / Path(*item.parts)).exists()]
    if missing:
        raise FinalizationError("required evidence is missing: " + ", ".join(missing))


def _sanitize_output(text: str, source: Path, staging: Path) -> str:
    sanitized = text.replace(str(source), "<SOURCE>").replace(str(staging), "<STAGING>")
    return sanitized[-12000:]


def _run_reproduction(staging: Path, entry: PurePosixPath, timeout: int) -> dict[str, object]:
    entry_path = staging / Path(*entry.parts)
    if not entry_path.is_file():
        raise FinalizationError(f"reproduction entry is missing from staging: {entry.as_posix()}")
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, entry.as_posix()],
        cwd=staging,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    result = {
        "entry": entry.as_posix(),
        "interpreter": "python",
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "stdout_tail": _sanitize_output(completed.stdout, staging, staging),
        "stderr_tail": _sanitize_output(completed.stderr, staging, staging),
        "status": "passed" if completed.returncode == 0 else "failed",
    }
    (staging / REPRODUCTION_REPORT_NAME).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if completed.returncode != 0:
        raise FinalizationError(
            f"reproduction failed with exit code {completed.returncode}; staging retained for diagnosis"
        )
    return result


def _write_cleanup_report(
    staging: Path,
    *,
    source_name: str,
    excluded: list[dict[str, str]],
    required: list[PurePosixPath],
    reproduction: dict[str, object] | None,
) -> None:
    lines = [
        "# 支撑材料最终化回执",
        "",
        f"- 来源目录：`{source_name}`（只读）",
        "- 清理边界：新建 staging 副本",
        "- 自动删除范围：操作系统元数据、解释器缓存、虚拟环境和可再生编译辅助文件",
        "- 语义删除：未自动执行；需由 `$simplify-codebase` 逐项形成消费者与行为证明",
        f"- 必需证据：{', '.join(f'`{item.as_posix()}`' for item in required) or '未指定'}",
        f"- 复现入口：`{reproduction['entry']}`" if reproduction else "- 复现入口：未执行",
        f"- 复现状态：{reproduction['status']}" if reproduction else "- 复现状态：未执行",
        "",
        "## 自动排除项",
        "",
    ]
    if excluded:
        lines.extend(f"- `{item['path']}`：{item['reason']}" for item in excluded)
    else:
        lines.append("- 无。")
    lines.extend(
        [
            "",
            "## 保留原则",
            "",
            "原始数据、数据契约、异常账本、清洗谱系、正式源码、权威 CSV/JSON、图表源、",
            "LaTeX/PDF、AI 声明、复现说明与环境锁定文件均按源目录保留，除非另有逐项证明。",
            "",
        ]
    )
    (staging / CLEANUP_REPORT_NAME).write_text("\n".join(lines), encoding="utf-8")


def _paper_record(paper: Path) -> dict[str, object]:
    return {
        "filename": paper.name,
        "size": paper.stat().st_size,
        "md5": _md5(paper),
        "sha256": _sha256(paper),
    }


def _gate_record(path: Path) -> dict[str, object]:
    return {
        "filename": path.name,
        "size": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _write_paper_binding(
    staging: Path,
    paper: Path,
    integrated_review_gate: Path,
) -> dict[str, object]:
    record = _paper_record(paper)
    payload = {
        "format": "modickx-paper-binding",
        "schema_version": 1,
        "paper": record,
        "integrated_review_gate": _gate_record(integrated_review_gate),
        "hash_roles": {
            "md5": "submission-platform-correspondence",
            "sha256": "integrity-and-readback",
        },
    }
    (staging / PAPER_BINDING_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


def _write_manifest(
    staging: Path,
    *,
    source_name: str,
    required: list[PurePosixPath],
    excluded: list[dict[str, str]],
    reproduction: dict[str, object] | None,
) -> list[FileRecord]:
    records = _records(staging, exclude=METADATA_NAMES)
    payload = {
        "format": "modickx-modeling-support-package",
        "schema_version": 1,
        "created_at": _utc_now(),
        "source_name": source_name,
        "source_was_modified": False,
        "required_evidence": [item.as_posix() for item in required],
        "reproduction": reproduction or {"status": "not_run"},
        "excluded": excluded,
        "files": [record.__dict__ for record in records],
    }
    (staging / MANIFEST_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (staging / CHECKSUM_NAME).write_text(
        "".join(f"{record.sha256}  {record.path}\n" for record in records), encoding="utf-8"
    )
    return records


def _build_and_verify_archive(
    staging: Path,
    archive: Path,
    records: list[FileRecord],
    *,
    identity_terms,
) -> dict[str, object]:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, allowZip64=True) as bundle:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(staging).as_posix())

    record_map = {record.path: record for record in records}
    with zipfile.ZipFile(archive) as bundle:
        corrupt = bundle.testzip()
        if corrupt is not None:
            raise FinalizationError(f"ZIP CRC check failed at {corrupt}")
        names = {info.filename for info in bundle.infolist() if not info.is_dir()}
        expected = set(record_map) | METADATA_NAMES
        if names != expected:
            raise FinalizationError("ZIP contents do not match the staging manifest")
        for relative, record in record_map.items():
            digest = hashlib.sha256(bundle.read(relative)).hexdigest()
            if digest != record.sha256:
                raise FinalizationError(f"ZIP readback hash mismatch: {relative}")
    archive_findings, archive_members = audit_archive(archive, identity_terms)
    if archive_findings:
        raise FinalizationError(
            f"post-build ZIP anonymity audit found {len(archive_findings)} blocking item(s)"
        )
    return {
        "crc": "passed",
        "readback": "passed",
        "archive_md5": _md5(archive),
        "archive_sha256": _sha256(archive),
        "archive_size": archive.stat().st_size,
        "archive_anonymity": "passed",
        "archive_anonymity_members_scanned": archive_members,
    }


def _submission_sidecars(archive: Path) -> dict[str, Path]:
    prefix = archive.with_suffix("")
    return {
        "manifest": prefix.with_name(prefix.name + ".SUBMISSION_PAIR_MANIFEST.json"),
        "md5": prefix.with_name(prefix.name + ".MD5SUMS.txt"),
        "sha256": prefix.with_name(prefix.name + ".SHA256SUMS.txt"),
    }


def _build_submission_pair(
    paper: Path,
    archive: Path,
    *,
    archive_result: dict[str, object],
) -> dict[str, object]:
    sidecars = _submission_sidecars(archive)
    occupied = [path for path in sidecars.values() if path.exists()]
    if occupied:
        raise FinalizationError(
            "submission pair sidecar already exists; refusing to overwrite: "
            + ", ".join(str(path) for path in occupied)
        )

    paper_record = _paper_record(paper)
    archive_record = {
        "filename": archive.name,
        "size": archive.stat().st_size,
        "md5": str(archive_result["archive_md5"]),
        "sha256": str(archive_result["archive_sha256"]),
    }
    with zipfile.ZipFile(archive) as bundle:
        corrupt = bundle.testzip()
        if corrupt is not None:
            raise FinalizationError(f"ZIP CRC check failed at {corrupt}")
        try:
            binding = json.loads(bundle.read(PAPER_BINDING_NAME).decode("utf-8"))
            gate_bytes = bundle.read(INTEGRATED_REVIEW_GATE_NAME)
        except KeyError as exc:
            raise FinalizationError(
                "support archive is missing paper binding or integrated review gate"
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FinalizationError("support archive has an invalid PAPER_BINDING.json") from exc
    if binding.get("paper") != paper_record:
        raise FinalizationError("paper binding does not match the formal electronic paper")
    gate_record = {
        "filename": INTEGRATED_REVIEW_GATE_NAME,
        "size": len(gate_bytes),
        "sha256": hashlib.sha256(gate_bytes).hexdigest(),
    }
    if binding.get("integrated_review_gate") != gate_record:
        raise FinalizationError("integrated review gate does not match the embedded binding")

    pair_id = (
        "submission-pair-v1-"
        f"{paper_record['sha256'][:12]}-{archive_record['sha256'][:12]}"
    )
    payload = {
        "format": "modickx-submission-pair",
        "schema_version": 1,
        "created_at": _utc_now(),
        "pair_id": pair_id,
        "paper": paper_record,
        "support_archive": archive_record,
        "integrated_review_gate": gate_record,
        "embedded_binding": PAPER_BINDING_NAME,
        "checksum_sidecars": {
            "md5": sidecars["md5"].name,
            "sha256": sidecars["sha256"].name,
        },
        "hash_roles": {
            "md5": "submission-platform-correspondence",
            "sha256": "integrity-and-readback",
        },
        "checks": {
            "one_paper_one_support_archive": "passed",
            "paper_binding_readback": "passed",
            "integrated_review_gate_hash_readback": "passed",
            "checksum_sidecars_written": "passed",
            "zip_crc": "passed",
        },
    }
    sidecars["manifest"].write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    sidecars["md5"].write_text(
        f"{paper_record['md5']}  {paper_record['filename']}\n"
        f"{archive_record['md5']}  {archive_record['filename']}\n",
        encoding="utf-8",
    )
    sidecars["sha256"].write_text(
        f"{paper_record['sha256']}  {paper_record['filename']}\n"
        f"{archive_record['sha256']}  {archive_record['filename']}\n",
        encoding="utf-8",
    )
    return {
        "submission_pair_check": "passed",
        "submission_pair_id": pair_id,
        "paper_md5": paper_record["md5"],
        "paper_sha256": paper_record["sha256"],
        "submission_pair_manifest": str(sidecars["manifest"]),
        "submission_pair_md5s": str(sidecars["md5"]),
        "submission_pair_sha256s": str(sidecars["sha256"]),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--require", action="append", default=[])
    parser.add_argument("--reproduction-entry")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--paper",
        required=True,
        type=Path,
        help="formal electronic paper PDF; audited but not copied automatically",
    )
    parser.add_argument(
        "--identity-ledger",
        required=True,
        type=Path,
        help="external JSON ledger of team identity literals; never copied into delivery",
    )
    parser.add_argument("--main-page-limit", type=int, default=DEFAULT_MAIN_PAGE_LIMIT)
    parser.add_argument("--appendix-start-page", type=int)
    parser.add_argument("--abstract-pages-excluded", type=int, default=1)
    parser.add_argument(
        "--latex-main",
        required=True,
        help="relative path to the formal LaTeX entry inside the support source",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        source = args.source.resolve()
        staging = args.staging.resolve()
        archive = args.archive.resolve()
        paper = args.paper.resolve()
        identity_ledger = args.identity_ledger.resolve()
        required = [_relative(item) for item in args.require]
        integrated_review_relative = _relative(INTEGRATED_REVIEW_GATE_NAME)
        if integrated_review_relative not in required:
            required.append(integrated_review_relative)
        reproduction_entry = _relative(args.reproduction_entry) if args.reproduction_entry else None
        latex_main = _relative(args.latex_main)

        if not source.is_dir():
            raise FinalizationError(f"source directory does not exist: {source}")
        if not paper.is_file():
            raise FinalizationError(f"formal electronic paper does not exist: {paper}")
        if not identity_ledger.is_file():
            raise FinalizationError(f"identity ledger does not exist: {identity_ledger}")
        if args.main_page_limit < 1:
            raise FinalizationError("main page limit must be positive")
        if args.abstract_pages_excluded != 1:
            raise FinalizationError("competition paper audit requires exactly one abstract page")
        if staging.exists():
            raise FinalizationError(f"staging already exists; refusing to overwrite: {staging}")
        if archive.exists():
            raise FinalizationError(f"archive already exists; refusing to overwrite: {archive}")
        occupied_sidecars = [
            path for path in _submission_sidecars(archive).values() if path.exists()
        ]
        if occupied_sidecars:
            raise FinalizationError(
                "submission pair sidecar already exists; refusing to overwrite: "
                + ", ".join(str(path) for path in occupied_sidecars)
            )
        if _inside(staging, source) or _inside(archive, source):
            raise FinalizationError("staging and archive must be outside the read-only source directory")
        if _inside(identity_ledger, source) or _inside(identity_ledger, staging):
            raise FinalizationError(
                "identity ledger must remain outside source and delivery staging directories"
            )
        identity_terms, identity_category_counts = load_identity_ledger(identity_ledger)
        source_label_findings = audit_label(source.name, identity_terms)
        if source_label_findings:
            raise FinalizationError("source directory name contains a blocked team-identity marker")
        _ensure_required(source, required)
        _ensure_required(source, [latex_main])
        before = _source_snapshot(source)
        source_files, excluded = _collect_source_files(source)

        staging.mkdir(parents=True)
        for path, relative in source_files:
            destination = staging / Path(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)

        reproduction = None
        if reproduction_entry is not None:
            reproduction = _run_reproduction(staging, reproduction_entry, max(1, args.timeout))
            excluded.extend(_remove_regenerable_artifacts(staging))

        _ensure_required(staging, required)
        integrated_review_gate = staging / INTEGRATED_REVIEW_GATE_NAME
        integrated_review_result = require_ready_gate(
            integrated_review_gate,
            expected_profile="competition-cn",
        )
        latex_path = staging / Path(*latex_main.parts)
        latex_findings, latex_report = audit_latex(latex_path)
        (staging / LATEX_AUDIT_NAME).write_text(
            json.dumps(latex_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if latex_findings:
            raise FinalizationError(
                f"competition LaTeX format audit found {len(latex_findings)} blocking item(s); "
                f"see staging/{LATEX_AUDIT_NAME}"
            )
        paper_findings, paper_pages, counted_paper_pages, appendix_start_page = audit_formal_paper(
            paper,
            identity_terms,
            main_page_limit=args.main_page_limit,
            appendix_start_page=args.appendix_start_page,
            abstract_pages_excluded=args.abstract_pages_excluded,
        )
        _write_paper_binding(staging, paper, integrated_review_gate)
        staging_findings, staging_files = audit_tree(
            staging, identity_terms, exclude=(identity_ledger,)
        )
        anonymity_findings = paper_findings + staging_findings
        anonymity_report = build_report(
            ledger_path=identity_ledger,
            category_counts=identity_category_counts,
            paper=paper,
            paper_pages=paper_pages,
            counted_paper_pages=counted_paper_pages,
            main_page_limit=args.main_page_limit,
            appendix_start_page=appendix_start_page,
            abstract_pages_excluded=args.abstract_pages_excluded,
            staging_files=staging_files,
            archive_files=None,
            findings=anonymity_findings,
        )
        (staging / AUDIT_NAME).write_text(
            json.dumps(anonymity_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if anonymity_findings:
            raise FinalizationError(
                f"competition anonymity audit found {len(anonymity_findings)} blocking item(s); "
                f"see staging/{AUDIT_NAME}"
            )
        _write_cleanup_report(
            staging,
            source_name=source.name,
            excluded=excluded,
            required=required,
            reproduction=reproduction,
        )
        records = _write_manifest(
            staging,
            source_name=source.name,
            required=required,
            excluded=excluded,
            reproduction=reproduction,
        )
        archive_result = _build_and_verify_archive(
            staging,
            archive,
            records,
            identity_terms=identity_terms,
        )
        submission_pair_result = _build_submission_pair(
            paper,
            archive,
            archive_result=archive_result,
        )
        source_unchanged = before == _source_snapshot(source)
        if not source_unchanged:
            raise FinalizationError("source changed during finalization")

        receipt = {
            "status": "ready",
            "source_unchanged": True,
            "staging": str(staging),
            "archive": str(archive),
            "included_file_count": len(records),
            "excluded_item_count": len(excluded),
            "anonymity_audit": "passed",
            "latex_format_audit": "passed",
            "integrated_review_gate": "passed",
            "integrated_review_gate_sha256": integrated_review_result["gate_sha256"],
            "counted_pages_including_references_excluding_abstract": counted_paper_pages,
            "page_limit_including_references_excluding_abstract": args.main_page_limit,
            "abstract_pages_excluded": args.abstract_pages_excluded,
            "appendix_start_page": appendix_start_page,
            **archive_result,
            **submission_pair_result,
        }
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except (
        AnonymityAuditError,
        IntegratedReviewGateError,
        LatexFormatAuditError,
        FinalizationError,
        OSError,
        subprocess.TimeoutExpired,
        zipfile.BadZipFile,
    ) as exc:
        print(f"finalization blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
