#!/usr/bin/env python3
"""Verify that one paper PDF and one support ZIP are the frozen submission pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


PAPER_BINDING_NAME = "PAPER_BINDING.json"
INTEGRATED_REVIEW_GATE_NAME = "INTEGRATED_FINAL_REVIEW.json"


class SubmissionPairError(ValueError):
    """Raised when the selected paper and support archive are not the frozen pair."""


def _digest(path: Path, algorithm: str) -> str:
    if algorithm == "md5":
        digest = hashlib.md5(usedforsecurity=False)
    else:
        digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _record(path: Path) -> dict[str, object]:
    return {
        "filename": path.name,
        "size": path.stat().st_size,
        "md5": _digest(path, "md5"),
        "sha256": _digest(path, "sha256"),
    }


def _submission_sidecars(archive: Path) -> dict[str, Path]:
    prefix = archive.with_suffix("")
    return {
        "md5": prefix.with_name(prefix.name + ".MD5SUMS.txt"),
        "sha256": prefix.with_name(prefix.name + ".SHA256SUMS.txt"),
    }


def _verify_checksum_sidecar(
    path: Path,
    *,
    label: str,
    expected_text: str,
) -> None:
    if not path.is_file():
        raise SubmissionPairError(f"{label} checksum sidecar does not exist: {path}")
    try:
        actual = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SubmissionPairError(f"{label} checksum sidecar is not valid UTF-8") from exc
    if actual != expected_text:
        raise SubmissionPairError(f"{label} checksum sidecar does not match the selected pair")


def verify(paper: Path, archive: Path, manifest: Path) -> dict[str, object]:
    for path, label in ((paper, "paper"), (archive, "support archive"), (manifest, "manifest")):
        if not path.is_file():
            raise SubmissionPairError(f"{label} does not exist: {path}")
    if paper.suffix.lower() != ".pdf":
        raise SubmissionPairError("paper must be a PDF")
    if archive.suffix.lower() != ".zip":
        raise SubmissionPairError("support archive must be a ZIP")

    try:
        expected = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SubmissionPairError("submission pair manifest is invalid") from exc
    if expected.get("format") != "modickx-submission-pair" or expected.get("schema_version") != 1:
        raise SubmissionPairError("submission pair manifest has an unsupported schema")

    paper_record = _record(paper)
    archive_record = _record(archive)
    if expected.get("paper") != paper_record:
        raise SubmissionPairError("paper hash does not match the submission pair manifest")
    if expected.get("support_archive") != archive_record:
        raise SubmissionPairError("support archive hash does not match the submission pair manifest")

    sidecars = _submission_sidecars(archive)
    declared_sidecars = expected.get("checksum_sidecars")
    expected_sidecar_names = {
        "md5": sidecars["md5"].name,
        "sha256": sidecars["sha256"].name,
    }
    if declared_sidecars != expected_sidecar_names:
        raise SubmissionPairError("checksum sidecar names do not match the selected support archive")
    _verify_checksum_sidecar(
        sidecars["md5"],
        label="MD5",
        expected_text=(
            f"{paper_record['md5']}  {paper_record['filename']}\n"
            f"{archive_record['md5']}  {archive_record['filename']}\n"
        ),
    )
    _verify_checksum_sidecar(
        sidecars["sha256"],
        label="SHA-256",
        expected_text=(
            f"{paper_record['sha256']}  {paper_record['filename']}\n"
            f"{archive_record['sha256']}  {archive_record['filename']}\n"
        ),
    )

    try:
        with zipfile.ZipFile(archive) as bundle:
            corrupt = bundle.testzip()
            if corrupt is not None:
                raise SubmissionPairError(f"ZIP CRC check failed at {corrupt}")
            binding = json.loads(bundle.read(PAPER_BINDING_NAME).decode("utf-8"))
            gate_bytes = bundle.read(INTEGRATED_REVIEW_GATE_NAME)
    except KeyError as exc:
        raise SubmissionPairError(
            "support archive is missing paper binding or integrated review gate"
        ) from exc
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SubmissionPairError("support archive or PAPER_BINDING.json is invalid") from exc
    if binding.get("paper") != paper_record:
        raise SubmissionPairError("paper hash does not match the embedded support-package binding")
    gate_record = {
        "filename": INTEGRATED_REVIEW_GATE_NAME,
        "size": len(gate_bytes),
        "sha256": hashlib.sha256(gate_bytes).hexdigest(),
    }
    try:
        gate_payload = json.loads(gate_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SubmissionPairError("integrated final review gate is invalid") from exc
    if (
        gate_payload.get("format") != "modickx-integrated-final-review"
        or gate_payload.get("schema_version") != 3
        or gate_payload.get("final_disposition") != "ready"
    ):
        raise SubmissionPairError("integrated final review gate is not ready")
    if binding.get("integrated_review_gate") != gate_record:
        raise SubmissionPairError("review gate hash does not match the embedded paper binding")
    if expected.get("integrated_review_gate") != gate_record:
        raise SubmissionPairError("review gate hash does not match the submission pair manifest")

    return {
        "status": "ready",
        "pair_id": expected.get("pair_id"),
        "paper": paper_record,
        "support_archive": archive_record,
        "integrated_review_gate": gate_record,
        "checks": {
            "one_paper_one_support_archive": "passed",
            "manifest_hashes": "passed",
            "paper_binding_readback": "passed",
            "integrated_review_gate_hash_readback": "passed",
            "md5_sidecar_readback": "passed",
            "sha256_sidecar_readback": "passed",
            "zip_crc": "passed",
        },
        "hash_roles": {
            "md5": "submission-platform-correspondence",
            "sha256": "integrity-and-readback",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = verify(args.paper.resolve(), args.archive.resolve(), args.manifest.resolve())
    except SubmissionPairError as exc:
        print(f"submission pair blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
