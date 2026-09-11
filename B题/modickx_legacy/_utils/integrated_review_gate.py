#!/usr/bin/env python3
"""Validate the hash-bound Modickx + BZD + Nature final review gate."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


GATE_NAME = "INTEGRATED_FINAL_REVIEW.json"
GATE_FORMAT = "modickx-integrated-final-review"
SCHEMA_VERSION = 3
CONFLICT_AUDIT_NAME = "FINAL_REVIEW_CONFLICTS.json"
CONFLICT_AUDIT_FORMAT = "modickx-final-review-conflicts"
CONFLICT_AUDIT_SCHEMA_VERSION = 3
COMPONENT_IDS = ("modickx", "bzd", "nature")
REQUIRED_CONFLICT_COMPARISONS = {
    "modickx:bzd",
    "modickx:nature",
    "bzd:nature",
}
PAIRWISE_OUTCOMES = {"no-conflict", "conflicts-recorded"}
REQUIRED_BZD_AUDITS = {
    "bzd-review-paper",
    "bzd-abstract-checker",
    "bzd-reference-appendix-checker",
}
REQUIRED_NATURE_SPECIALISTS = {
    "nature-reviewer",
    "nature-statistics",
    "nature-data",
    "nature-ref-verifier",
    "nature-figure",
    "nature-writing",
}
AUTHORITY_ORDER = [
    "official-and-user-nonnegotiable-constraints",
    "current-data-and-reproducible-results",
    "modickx-hard-gates",
    "user-decision-among-ablation-survivors",
]
REVIEW_PERSPECTIVES = {
    "modickx": "deterministic execution, rendering, and delivery evidence",
    "bzd": "independent competition-reader and compliance evidence",
    "nature": "independent scientific-method and publication evidence",
}
CONFLICT_RESOLUTION_POLICY = {
    "minimum_ablation_rounds": 2,
    "minimum_variants_per_round": 2,
    "minimum_surviving_variants_for_user_decision": 2,
    "requires_control_variant_each_round": True,
    "single_controlled_change_per_non_control_variant": True,
    "final_decider": "user",
    "automatic_domain_precedence": "forbidden",
    "stale_checkpoint_resolution": "reject",
    "selection_rule": (
        "user-selects-from-hard-gate-eligible-variants-after-side-by-side-results"
    ),
}
CONFLICT_STATUSES = {"awaiting-user", "resolved"}
VARIANT_ELIGIBILITY = {"eligible", "ineligible"}
ABLATION_RESULT_FORMAT = "modickx-ablation-variant-result"
HARD_GATE_ASSESSMENT_FORMAT = "modickx-variant-hard-gate-assessment"
HARD_GATE_AUTHORITIES = tuple(AUTHORITY_ORDER[:3])
CHECKPOINT_RECEIPT_FORMAT = "modickx-final-review-checkpoint-receipt"
RUNTIME_CHECKPOINT_ACCEPTANCE_PATH = "stage-acceptance/manuscript-qa.json"
RUNTIME_CHECKPOINT_ATTESTATION_ROLE = "runtime-user-decision-acceptance"
REQUIRED_ROLES = {
    "modickx": {
        "quality-report",
        "manuscript-qa-report",
        "adversarial-review",
        "judge-readiness",
        "contradiction-audit",
    },
    "bzd": {"judge-review-summary"},
    "nature": {"post-review-synthesis"},
}
MODICKX_ARTIFACTS = (
    ("QUALITY_REPORT.md", "quality-report"),
    ("MANUSCRIPT_QA_REPORT.md", "manuscript-qa-report"),
    ("ADVERSARIAL_REVIEW.json", "adversarial-review"),
    ("JUDGE_READINESS_AUDIT.json", "judge-readiness"),
)
FORBIDDEN_RELEASE_SCORE_KEYS = {
    "aggregate_score",
    "combined_score",
    "release_score",
    "weighted_score",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class IntegratedReviewGateError(ValueError):
    """Raised when a final review gate is missing or not ready."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _artifact(root: Path, path: Path, role: str, **extra: object) -> dict[str, Any]:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    return {
        "path": relative,
        "sha256": _sha256(path),
        "role": role,
        **extra,
    }


def _required_file(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise IntegratedReviewGateError(f"required review artifact is missing: {relative}")
    return path


def _read_required_object(path: Path, label: str) -> dict[str, Any]:
    errors: list[str] = []
    payload = _load_json(path, errors, label)
    if payload is None:
        raise IntegratedReviewGateError("; ".join(errors))
    return payload


def _component_disposition(
    label: str,
    payload: dict[str, Any],
    blocking_fields: tuple[str, ...],
) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if payload.get("final_disposition") != "ready":
        blockers.append(f"{label} final_disposition is not ready")
    for field in blocking_fields:
        value = payload.get(field)
        if not isinstance(value, list):
            blockers.append(f"{label} {field} is not a list")
        else:
            blockers.extend(f"{label}: {item}" for item in value)
    return ("ready" if not blockers else "blocked", blockers)


def _load_conflict_audit(
    root: Path,
    conflict_ledger: str | Path | None,
    review_artifacts: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], Path]:
    candidate = Path(conflict_ledger) if conflict_ledger else Path(CONFLICT_AUDIT_NAME)
    path = candidate if candidate.is_absolute() else root / candidate
    path = path.resolve()
    try:
        relative = path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise IntegratedReviewGateError(
            "conflict audit must stay inside the review workspace"
        ) from exc
    _required_file(root, relative)

    payload = _read_required_object(path, "cross-review conflict audit")
    if (
        payload.get("format") != CONFLICT_AUDIT_FORMAT
        or payload.get("schema_version") != CONFLICT_AUDIT_SCHEMA_VERSION
    ):
        raise IntegratedReviewGateError("cross-review conflict audit has an unsupported schema")
    coverage = payload.get("comparison_coverage")
    if not isinstance(coverage, list):
        raise IntegratedReviewGateError("cross-review comparison coverage must be a list")
    coverage_values = [str(item) for item in coverage]
    coverage_set = set(coverage_values)
    missing_comparisons = REQUIRED_CONFLICT_COMPARISONS - coverage_set
    unexpected_comparisons = coverage_set - REQUIRED_CONFLICT_COMPARISONS
    if missing_comparisons or unexpected_comparisons or len(coverage_values) != len(coverage_set):
        details = []
        if missing_comparisons:
            details.append("missing " + ", ".join(sorted(missing_comparisons)))
        if unexpected_comparisons:
            details.append("unexpected " + ", ".join(sorted(unexpected_comparisons)))
        if len(coverage_values) != len(coverage_set):
            details.append("duplicate pair entries")
        raise IntegratedReviewGateError(
            "cross-review comparison coverage is invalid: " + "; ".join(details)
        )

    conflicts = payload.get("conflicts")
    if not isinstance(conflicts, list) or any(
        not isinstance(item, dict) for item in conflicts
    ):
        raise IntegratedReviewGateError(
            "cross-review conflict audit must contain a list of conflict objects"
        )

    comparison_records = payload.get("pairwise_comparisons")
    if not isinstance(comparison_records, list):
        raise IntegratedReviewGateError(
            "cross-review pairwise_comparisons must be a list"
        )
    comparison_map: dict[str, dict[str, Any]] = {}
    component_paths = {
        component: {str(item["path"]) for item in artifacts}
        for component, artifacts in review_artifacts.items()
    }
    for index, record in enumerate(comparison_records):
        label = f"cross-review pairwise_comparisons[{index}]"
        if not isinstance(record, dict):
            raise IntegratedReviewGateError(f"{label} must be an object")
        pair = record.get("pair")
        if pair not in REQUIRED_CONFLICT_COMPARISONS:
            raise IntegratedReviewGateError(f"{label}.pair is invalid")
        if pair in comparison_map:
            raise IntegratedReviewGateError(
                f"cross-review pairwise_comparisons repeats {pair}"
            )
        outcome = record.get("outcome")
        if outcome not in PAIRWISE_OUTCOMES:
            raise IntegratedReviewGateError(f"{label}.outcome is invalid")
        evidence_paths = record.get("evidence_paths")
        if not isinstance(evidence_paths, list):
            raise IntegratedReviewGateError(f"{label}.evidence_paths must be a list")
        normalized_evidence: set[str] = set()
        for evidence_index, value in enumerate(evidence_paths):
            relative = _relative_path(
                value,
                [],
                f"{label}.evidence_paths[{evidence_index}]",
            )
            if relative is None:
                raise IntegratedReviewGateError(
                    f"{label}.evidence_paths[{evidence_index}] is invalid"
                )
            normalized_evidence.add(relative.as_posix())
        left, right = str(pair).split(":", 1)
        for component in (left, right):
            if not (normalized_evidence & component_paths.get(component, set())):
                raise IntegratedReviewGateError(
                    f"{label} must cite at least one current {component} review artifact"
                )
        conflict_ids = record.get("conflict_ids")
        if not isinstance(conflict_ids, list) or any(
            not isinstance(item, str) or not item.strip() for item in conflict_ids
        ):
            raise IntegratedReviewGateError(f"{label}.conflict_ids must be a list of IDs")
        if len(conflict_ids) != len(set(conflict_ids)):
            raise IntegratedReviewGateError(f"{label}.conflict_ids contains duplicates")
        if outcome == "no-conflict" and conflict_ids:
            raise IntegratedReviewGateError(
                f"{label} cannot declare no-conflict while naming conflicts"
            )
        if outcome == "conflicts-recorded" and not conflict_ids:
            raise IntegratedReviewGateError(
                f"{label} must name at least one recorded conflict"
            )
        comparison_map[str(pair)] = record
    if set(comparison_map) != REQUIRED_CONFLICT_COMPARISONS:
        missing = REQUIRED_CONFLICT_COMPARISONS - set(comparison_map)
        raise IntegratedReviewGateError(
            "cross-review pairwise comparison records are missing: "
            + ", ".join(sorted(missing))
        )

    conflict_map: dict[str, dict[str, Any]] = {}
    for index, conflict in enumerate(conflicts):
        conflict_id = conflict.get("id")
        if not isinstance(conflict_id, str) or not conflict_id.strip():
            raise IntegratedReviewGateError(
                f"cross-review conflicts[{index}].id must be non-empty"
            )
        if conflict_id in conflict_map:
            raise IntegratedReviewGateError(
                f"cross-review conflicts repeats id {conflict_id}"
            )
        pair = conflict.get("pair")
        if pair not in REQUIRED_CONFLICT_COMPARISONS:
            raise IntegratedReviewGateError(
                f"cross-review conflicts[{index}].pair is invalid"
            )
        if conflict_id not in comparison_map[str(pair)].get("conflict_ids", []):
            raise IntegratedReviewGateError(
                f"cross-review conflict {conflict_id} is not linked from its pairwise comparison"
            )
        conflict_map[conflict_id] = conflict
    linked_pairs: dict[str, list[str]] = {}
    for pair, record in comparison_map.items():
        for conflict_id in record.get("conflict_ids", []):
            linked_pairs.setdefault(str(conflict_id), []).append(pair)
    multiply_linked = {
        conflict_id: pairs
        for conflict_id, pairs in linked_pairs.items()
        if len(pairs) != 1
    }
    if multiply_linked:
        details = ", ".join(
            f"{conflict_id} ({'/'.join(sorted(pairs))})"
            for conflict_id, pairs in sorted(multiply_linked.items())
        )
        raise IntegratedReviewGateError(
            "conflict IDs must belong to exactly one review pair: " + details
        )
    linked_conflicts = set(linked_pairs)
    unbound_ids = linked_conflicts - set(conflict_map)
    if unbound_ids:
        raise IntegratedReviewGateError(
            "pairwise comparisons reference missing conflicts: "
            + ", ".join(sorted(unbound_ids))
        )

    declared_inputs = payload.get("review_inputs")
    if not isinstance(declared_inputs, list):
        raise IntegratedReviewGateError("cross-review review_inputs must be a list")
    declared_map: dict[str, str] = {}
    for index, item in enumerate(declared_inputs):
        if not isinstance(item, dict):
            raise IntegratedReviewGateError(
                f"cross-review review_inputs[{index}] must be an object"
            )
        input_path = _relative_path(
            item.get("path"), [], f"cross-review review_inputs[{index}].path"
        )
        digest = item.get("sha256")
        if input_path is None or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise IntegratedReviewGateError(
                f"cross-review review_inputs[{index}] has an invalid path or SHA-256"
            )
        normalized = input_path.as_posix()
        if normalized in declared_map:
            raise IntegratedReviewGateError(
                f"cross-review review_inputs repeats {normalized}"
            )
        declared_map[normalized] = digest

    expected_map = {
        str(item["path"]): str(item["sha256"])
        for artifacts in review_artifacts.values()
        for item in artifacts
    }
    if declared_map != expected_map:
        raise IntegratedReviewGateError(
            "cross-review conflict audit is not bound to the current frozen review inputs"
        )
    return conflicts, path


def build_gate(
    workspace_root: str | Path,
    *,
    publication_profile: str = "competition-cn",
    overwrite: bool = False,
    conflict_ledger: str | Path | None = None,
) -> dict[str, Any]:
    """Build the final gate from frozen review artifacts, then validate it."""

    root = Path(workspace_root).resolve()
    if not root.is_dir():
        raise IntegratedReviewGateError(f"review workspace is missing: {root}")
    gate = root / GATE_NAME
    if gate.exists() and not overwrite:
        raise IntegratedReviewGateError(
            f"{GATE_NAME} already exists; set overwrite=True to rebuild it"
        )
    if not isinstance(publication_profile, str) or not publication_profile.strip():
        raise IntegratedReviewGateError("publication_profile must be non-empty")

    modickx_artifacts = [
        _artifact(root, _required_file(root, relative), role)
        for relative, role in MODICKX_ARTIFACTS
    ]
    contradiction_path = next(
        (
            root / name
            for name in ("CONTRADICTION_AUDIT.json", "CONTRADICTION_AUDIT.md")
            if (root / name).is_file() and not (root / name).is_symlink()
        ),
        None,
    )
    if contradiction_path is None:
        raise IntegratedReviewGateError(
            "required review artifact is missing: CONTRADICTION_AUDIT.json or CONTRADICTION_AUDIT.md"
        )
    modickx_artifacts.append(_artifact(root, contradiction_path, "contradiction-audit"))

    modickx_blockers: list[str] = []
    for filename in (
        "ADVERSARIAL_REVIEW.json",
        "JUDGE_READINESS_AUDIT.json",
    ):
        report = _read_required_object(root / filename, filename)
        if report.get("final_disposition") != "ready":
            modickx_blockers.append(f"{filename} final_disposition is not ready")
    if contradiction_path.suffix.lower() == ".json":
        report = _read_required_object(contradiction_path, contradiction_path.name)
        if report.get("final_disposition") not in (None, "ready"):
            modickx_blockers.append(
                f"{contradiction_path.name} final_disposition is not ready"
            )

    bzd_path = _required_file(root, "BZD_REVIEW_SUMMARY.json")
    bzd_payload = _read_required_object(bzd_path, "BZD review summary")
    bzd_status, bzd_blockers = _component_disposition(
        "BZD",
        bzd_payload,
        ("eligibility_blockers", "unresolved_central_risks"),
    )
    if bzd_payload.get("format") != "bzd-review-summary" or bzd_payload.get(
        "schema_version"
    ) != 1:
        bzd_blockers.append("BZD review summary has an unsupported schema")
    if bzd_payload.get("score_is_release_gate") is not False:
        bzd_blockers.append("BZD score is incorrectly configured as a release gate")
    bzd_coverage = bzd_payload.get("audit_coverage")
    if not isinstance(bzd_coverage, list):
        bzd_blockers.append("BZD audit_coverage is not a list")
    else:
        missing_bzd = REQUIRED_BZD_AUDITS - {str(item) for item in bzd_coverage}
        if missing_bzd:
            bzd_blockers.append(
                "BZD audits are missing: " + ", ".join(sorted(missing_bzd))
            )
    bzd_status = "ready" if not bzd_blockers else "blocked"

    nature_synthesis_path = _required_file(root, "NATURE_REVIEW_SYNTHESIS.json")
    nature_payload = _read_required_object(
        nature_synthesis_path, "Nature review synthesis"
    )
    nature_status, nature_blockers = _component_disposition(
        "Nature",
        nature_payload,
        ("consensus_blocking_concerns", "unresolved_concerns"),
    )
    reviewer_paths = nature_payload.get("reviewer_reports")
    if not isinstance(reviewer_paths, list) or len(set(map(str, reviewer_paths))) < 3:
        raise IntegratedReviewGateError(
            "Nature synthesis must name at least three distinct frozen reviewer reports"
        )
    nature_artifacts: list[dict[str, Any]] = []
    reviewer_ids: set[str] = set()
    for index, relative_value in enumerate(reviewer_paths):
        relative = _relative_path(
            relative_value,
            nature_blockers,
            f"Nature reviewer_reports[{index}]",
        )
        if relative is None:
            continue
        report_path = _required_file(root, relative.as_posix())
        report = _read_required_object(report_path, f"Nature reviewer report {index + 1}")
        reviewer_id = report.get("reviewer_id")
        if not isinstance(reviewer_id, str) or not reviewer_id.strip():
            nature_blockers.append(f"Nature reviewer report {index + 1} has no reviewer_id")
            reviewer_id = f"missing-{index + 1}"
        if report.get("format") != "nature-review-report" or report.get("schema_version") != 1:
            nature_blockers.append(
                f"Nature reviewer report {index + 1} has an unsupported schema"
            )
        if report.get("frozen") is not True:
            nature_blockers.append(f"Nature reviewer report {index + 1} is not frozen")
        reviewer_ids.add(reviewer_id)
        nature_artifacts.append(
            _artifact(
                root,
                report_path,
                "reviewer-report",
                reviewer_id=reviewer_id,
                frozen=report.get("frozen") is True,
            )
        )
    if len(reviewer_ids) < 3:
        nature_blockers.append("Nature review does not contain three distinct reviewers")
    if nature_payload.get("format") != "nature-review-synthesis" or nature_payload.get(
        "schema_version"
    ) != 1:
        nature_blockers.append("Nature review synthesis has an unsupported schema")
    if nature_payload.get("reviewer_count") != len(reviewer_ids):
        nature_blockers.append("Nature reviewer_count does not match the frozen reports")
    nature_coverage = nature_payload.get("specialist_coverage")
    if not isinstance(nature_coverage, list):
        nature_blockers.append("Nature specialist_coverage is not a list")
    else:
        missing_nature = REQUIRED_NATURE_SPECIALISTS - {
            str(item) for item in nature_coverage
        }
        if missing_nature:
            nature_blockers.append(
                "Nature specialist coverage is missing: "
                + ", ".join(sorted(missing_nature))
            )
    nature_artifacts.append(
        _artifact(root, nature_synthesis_path, "post-review-synthesis")
    )
    nature_status = "ready" if not nature_blockers else "blocked"

    frozen_review_artifacts = {
        "modickx": modickx_artifacts,
        "bzd": [_artifact(root, bzd_path, "judge-review-summary")],
        "nature": nature_artifacts,
    }
    conflicts, conflict_audit_path = _load_conflict_audit(
        root,
        conflict_ledger,
        frozen_review_artifacts,
    )
    conflict_audit_payload = _read_required_object(
        conflict_audit_path, "cross-review conflict audit"
    )
    unresolved_conflicts = [
        f"review conflict {index + 1} is unresolved"
        for index, conflict in enumerate(conflicts)
        if conflict.get("status") != "resolved"
    ]
    runtime_attestation: dict[str, Any] | None = None
    runtime_attestation_blockers: list[str] = []
    if conflicts and not unresolved_conflicts:
        acceptance_path = root / RUNTIME_CHECKPOINT_ACCEPTANCE_PATH
        if acceptance_path.is_file() and not acceptance_path.is_symlink():
            runtime_attestation = _artifact(
                root,
                acceptance_path,
                RUNTIME_CHECKPOINT_ATTESTATION_ROLE,
            )
            _validate_runtime_checkpoint_attestation(
                root,
                conflict_audit_path,
                conflict_audit_payload,
                conflicts,
                runtime_attestation,
                runtime_attestation_blockers,
            )
        else:
            runtime_attestation_blockers.append(
                "resolved review conflicts are missing the runtime manuscript checkpoint acceptance"
            )
    unresolved = [
        *modickx_blockers,
        *bzd_blockers,
        *nature_blockers,
        *unresolved_conflicts,
        *runtime_attestation_blockers,
    ]
    payload = {
        "format": GATE_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "publication_profile": publication_profile.strip(),
        "decision_policy": {
            "authority_order": list(AUTHORITY_ORDER),
            "review_perspectives": dict(REVIEW_PERSPECTIVES),
            "conflict_resolution": dict(CONFLICT_RESOLUTION_POLICY),
            "score_aggregation": "forbidden",
            "release_rule": "all_applicable_hard_gates_ready",
            "waiver_policy": "downstream_review_cannot_waive_upstream",
        },
        "components": {
            "modickx": {
                "status": "ready" if not modickx_blockers else "blocked",
                "artifacts": modickx_artifacts,
                "blocking_items": modickx_blockers,
            },
            "bzd": {
                "status": bzd_status,
                "score_is_release_gate": False,
                "artifacts": [_artifact(root, bzd_path, "judge-review-summary")],
                "blocking_items": bzd_blockers,
            },
            "nature": {
                "status": nature_status,
                "reviewer_count": len(reviewer_ids),
                "artifacts": nature_artifacts,
                "blocking_items": nature_blockers,
            },
        },
        "conflict_audit": _artifact(
            root,
            conflict_audit_path,
            "cross-review-conflict-audit",
        ),
        "conflicts": conflicts,
        "unresolved_blocking_items": unresolved,
        "final_disposition": "ready" if not unresolved else "blocked",
    }
    if runtime_attestation is not None:
        payload["runtime_checkpoint_attestation"] = runtime_attestation
    _write_json(gate, payload)
    result = validate_gate(gate, expected_profile=publication_profile.strip())
    result["built"] = True
    return result


def _load_json(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        errors.append(f"{label} is not valid UTF-8 JSON")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label} must be a JSON object")
        return None
    return payload


def _relative_path(value: object, errors: list[str], label: str) -> PurePosixPath | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty relative path")
        return None
    normalized = value.replace("\\", "/").strip()
    relative = PurePosixPath(normalized)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or ":" in relative.parts[0]
    ):
        errors.append(f"{label} escapes the gate directory")
        return None
    return relative


def _resolved_local_file(
    root: Path,
    value: object,
    errors: list[str],
    label: str,
) -> Path | None:
    relative = _relative_path(value, errors, label)
    if relative is None:
        return None
    candidate = (root / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label} escapes the gate directory")
        return None
    if not candidate.is_file() or candidate.is_symlink():
        errors.append(f"{label} is missing: {relative.as_posix()}")
        return None
    return candidate


def _find_forbidden_release_scores(value: object, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in FORBIDDEN_RELEASE_SCORE_KEYS:
                found.append(current)
            found.extend(_find_forbidden_release_scores(item, current))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_find_forbidden_release_scores(item, f"{prefix}[{index}]"))
    return found


def _validate_bzd_summary(path: Path, errors: list[str]) -> None:
    payload = _load_json(path, errors, "BZD review summary")
    if payload is None:
        return
    if payload.get("format") != "bzd-review-summary" or payload.get("schema_version") != 1:
        errors.append("BZD review summary has an unsupported schema")
    if payload.get("score_is_release_gate") is not False:
        errors.append("BZD contest score must be diagnostic, not a release gate")
    coverage = payload.get("audit_coverage")
    if not isinstance(coverage, list):
        errors.append("BZD review summary audit_coverage must be a list")
    else:
        missing = REQUIRED_BZD_AUDITS - {str(item) for item in coverage}
        if missing:
            errors.append(
                "BZD review summary is missing audits: " + ", ".join(sorted(missing))
            )
    for field in ("eligibility_blockers", "unresolved_central_risks"):
        if not isinstance(payload.get(field), list):
            errors.append(f"BZD review summary {field} must be a list")
        elif payload.get("final_disposition") == "ready" and payload[field]:
            errors.append(f"ready BZD review cannot retain {field}")
    if payload.get("final_disposition") != "ready":
        errors.append("BZD review summary is not ready")


def _validate_nature_synthesis(path: Path, errors: list[str]) -> None:
    payload = _load_json(path, errors, "Nature review synthesis")
    if payload is None:
        return
    if payload.get("format") != "nature-review-synthesis" or payload.get("schema_version") != 1:
        errors.append("Nature review synthesis has an unsupported schema")
    count = payload.get("reviewer_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 3:
        errors.append("Nature review synthesis must combine at least three frozen reviewers")
    reports = payload.get("reviewer_reports")
    if not isinstance(reports, list) or len({str(item) for item in reports}) < 3:
        errors.append("Nature review synthesis must list at least three distinct reviewer reports")
    coverage = payload.get("specialist_coverage")
    if not isinstance(coverage, list):
        errors.append("Nature review synthesis specialist_coverage must be a list")
    else:
        missing = REQUIRED_NATURE_SPECIALISTS - {str(item) for item in coverage}
        if missing:
            errors.append(
                "Nature review synthesis is missing specialist coverage: "
                + ", ".join(sorted(missing))
            )
    for field in ("consensus_blocking_concerns", "unresolved_concerns"):
        if not isinstance(payload.get(field), list):
            errors.append(f"Nature review synthesis {field} must be a list")
        elif payload.get("final_disposition") == "ready" and payload[field]:
            errors.append(f"ready Nature synthesis cannot retain {field}")
    if payload.get("final_disposition") != "ready":
        errors.append("Nature review synthesis is not ready")


def _validate_nature_report(
    path: Path,
    artifact: dict[str, Any],
    errors: list[str],
    label: str,
) -> str | None:
    payload = _load_json(path, errors, label)
    if payload is None:
        return None
    if payload.get("format") != "nature-review-report" or payload.get("schema_version") != 1:
        errors.append(f"{label} has an unsupported schema")
    reviewer_id = artifact.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        errors.append(f"{label}.reviewer_id must be non-empty")
        return None
    if payload.get("reviewer_id") != reviewer_id:
        errors.append(f"{label}.reviewer_id does not match its report")
    if artifact.get("frozen") is not True or payload.get("frozen") is not True:
        errors.append(f"{label} must be frozen before synthesis")
    if not isinstance(payload.get("blocking_concerns"), list):
        errors.append(f"{label}.blocking_concerns must be a list")
    return reviewer_id


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_ablation_evidence(
    root: Path,
    value: object,
    errors: list[str],
    label: str,
    *,
    expected_identity: dict[str, object],
) -> str | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return None
    evidence_path = _resolved_local_file(root, value.get("path"), errors, f"{label}.path")
    digest = value.get("sha256")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        errors.append(f"{label}.sha256 must be a lowercase SHA-256 digest")
        return None
    if evidence_path is None:
        return None
    if _sha256(evidence_path) != digest:
        errors.append(f"{label} hash mismatch")
        return None
    evidence_payload = _load_json(evidence_path, errors, label)
    if evidence_payload is None:
        return None
    for field, expected in expected_identity.items():
        if evidence_payload.get(field) != expected:
            errors.append(f"{label}.{field} does not match its ablation variant")
    return evidence_path.relative_to(root).as_posix()


def _validate_hash_bound_file(
    root: Path,
    value: object,
    errors: list[str],
    label: str,
) -> str | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return None
    evidence_path = _resolved_local_file(root, value.get("path"), errors, f"{label}.path")
    digest = value.get("sha256")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        errors.append(f"{label}.sha256 must be a lowercase SHA-256 digest")
        return None
    if evidence_path is None:
        return None
    if _sha256(evidence_path) != digest:
        errors.append(f"{label} hash mismatch")
        return None
    return evidence_path.relative_to(root).as_posix()


def _parse_utc_timestamp(value: object, errors: list[str], label: str) -> datetime | None:
    if not _non_empty_string(value):
        errors.append(f"{label} must be a non-empty ISO timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} must be a valid ISO timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def _validate_runtime_checkpoint_attestation(
    root: Path,
    ledger_path: Path,
    ledger_payload: dict[str, Any],
    conflicts: list[dict[str, Any]],
    attestation: object,
    errors: list[str],
) -> int:
    """Bind resolved conflicts to the runtime-written manuscript acceptance record."""

    resolved_conflicts = [
        item for item in conflicts if isinstance(item, dict) and item.get("status") == "resolved"
    ]
    if not conflicts:
        if ledger_payload.get("decision_checkpoint") not in (None, {}):
            errors.append("conflict audit must not contain decision_checkpoint without conflicts")
        if attestation not in (None, {}):
            errors.append("runtime_checkpoint_attestation is not allowed without conflicts")
        return 0
    if len(resolved_conflicts) != len(conflicts):
        if attestation not in (None, {}):
            errors.append(
                "runtime_checkpoint_attestation cannot be accepted while conflicts await user review"
            )
        return 0

    checkpoint = ledger_payload.get("decision_checkpoint")
    if not isinstance(checkpoint, dict):
        errors.append("conflict audit decision_checkpoint must be an object")
        checkpoint = {}
    checkpoint_id = checkpoint.get("checkpoint_id")
    if not _non_empty_string(checkpoint_id):
        errors.append("conflict audit decision_checkpoint.checkpoint_id must be non-empty")
        checkpoint_id = ""
    else:
        checkpoint_id = str(checkpoint_id)
    if checkpoint.get("checkpoint_skill") != "manuscript-qa":
        errors.append("conflict audit decision_checkpoint.checkpoint_skill is invalid")

    opened_at = checkpoint.get("opened_at")
    recorded_at = checkpoint.get("recorded_at")
    opened_time = _parse_utc_timestamp(
        opened_at, errors, "conflict audit decision_checkpoint.opened_at"
    )
    recorded_time = _parse_utc_timestamp(
        recorded_at, errors, "conflict audit decision_checkpoint.recorded_at"
    )
    if opened_time is not None and recorded_time is not None and opened_time > recorded_time:
        errors.append("conflict audit decision checkpoint was recorded before it opened")

    request_path = _validate_hash_bound_file(
        root,
        checkpoint.get("request_snapshot"),
        errors,
        "conflict audit decision_checkpoint.request_snapshot",
    )
    receipt_path = _validate_hash_bound_file(
        root,
        checkpoint.get("checkpoint_receipt"),
        errors,
        "conflict audit decision_checkpoint.checkpoint_receipt",
    )
    ledger_relative = ledger_path.resolve().relative_to(root.resolve()).as_posix()
    expected_sources: dict[str, str] = {
        f"workspace:{ledger_relative}": _sha256(ledger_path)
    }
    for reference, verified_path in (
        (checkpoint.get("request_snapshot"), request_path),
        (checkpoint.get("checkpoint_receipt"), receipt_path),
    ):
        if verified_path is not None and isinstance(reference, dict):
            expected_sources[f"workspace:{verified_path}"] = str(reference.get("sha256", ""))

    for index, conflict in enumerate(resolved_conflicts):
        label = f"conflicts[{index}]"
        decision = conflict.get("user_decision")
        if not isinstance(decision, dict):
            errors.append(f"{label}.user_decision must be an object")
            continue
        if decision.get("checkpoint_id") != checkpoint_id:
            errors.append(f"{label}.user_decision.checkpoint_id does not match decision_checkpoint")
        decision_ref = decision.get("decision_evidence")
        decision_path = _validate_hash_bound_file(
            root,
            decision_ref,
            errors,
            f"{label}.user_decision.decision_evidence",
        )
        if decision_path is None or not isinstance(decision_ref, dict):
            continue
        expected_sources[f"workspace:{decision_path}"] = str(decision_ref.get("sha256", ""))
        decision_payload = _load_json(
            root / decision_path,
            errors,
            f"{label}.user_decision.decision_evidence",
        )
        if decision_payload is None:
            continue
        if decision_payload.get("checkpoint_opened_at") != opened_at:
            errors.append(
                f"{label}.user_decision.decision_evidence.checkpoint_opened_at "
                "does not match decision_checkpoint"
            )
        if decision_payload.get("recorded_at") != recorded_at:
            errors.append(
                f"{label}.user_decision.decision_evidence.recorded_at "
                "does not match decision_checkpoint"
            )
        if decision_payload.get("request_snapshot") != checkpoint.get("request_snapshot"):
            errors.append(
                f"{label}.user_decision.decision_evidence.request_snapshot "
                "does not match decision_checkpoint"
            )
        if decision_payload.get("checkpoint_receipt") != checkpoint.get("checkpoint_receipt"):
            errors.append(
                f"{label}.user_decision.decision_evidence.checkpoint_receipt "
                "does not match decision_checkpoint"
            )

    if not isinstance(attestation, dict):
        errors.append("runtime_checkpoint_attestation must be an object for resolved conflicts")
        return 0
    if attestation.get("role") != RUNTIME_CHECKPOINT_ATTESTATION_ROLE:
        errors.append("runtime_checkpoint_attestation.role is invalid")
    if attestation.get("path") != RUNTIME_CHECKPOINT_ACCEPTANCE_PATH:
        errors.append("runtime_checkpoint_attestation.path is invalid")
    acceptance_path = _validate_hash_bound_file(
        root,
        attestation,
        errors,
        "runtime_checkpoint_attestation",
    )
    if acceptance_path is None:
        return 0
    acceptance = _load_json(
        root / acceptance_path,
        errors,
        "runtime_checkpoint_attestation",
    )
    if acceptance is None:
        return 0
    if acceptance.get("schema_version") != 1:
        errors.append("runtime checkpoint acceptance has an unsupported schema")
    if acceptance.get("stage_id") != "manuscript-qa":
        errors.append("runtime checkpoint acceptance.stage_id is invalid")
    if acceptance.get("status") != "ready":
        errors.append("runtime checkpoint acceptance.status must be ready")
    if acceptance.get("validator") != "validate_modeling_stage_evidence":
        errors.append("runtime checkpoint acceptance.validator is invalid")
    if acceptance.get("review_checkpoint_id") != checkpoint_id:
        errors.append("runtime checkpoint acceptance.review_checkpoint_id does not match")

    blocking_checks = acceptance.get("blocking_checks")
    if not isinstance(blocking_checks, dict):
        errors.append("runtime checkpoint acceptance.blocking_checks must be an object")
    elif blocking_checks.get("failed") != []:
        errors.append("runtime checkpoint acceptance retains failed blocking checks")

    source_hashes = acceptance.get("source_sha256")
    source_ids = acceptance.get("source_artifact_ids")
    if not isinstance(source_hashes, dict):
        errors.append("runtime checkpoint acceptance.source_sha256 must be an object")
        source_hashes = {}
    if not isinstance(source_ids, list) or any(not isinstance(item, str) for item in source_ids):
        errors.append("runtime checkpoint acceptance.source_artifact_ids must be a list")
        source_ids = []
    if set(source_ids) != set(source_hashes):
        errors.append("runtime checkpoint acceptance source ids and hashes do not match")
    for source_id, expected_hash in expected_sources.items():
        if source_hashes.get(source_id) != expected_hash:
            errors.append(
                f"runtime checkpoint acceptance does not bind the current {source_id}"
            )
            continue
        relative = source_id.removeprefix("workspace:")
        source_path = root / relative
        if not source_path.is_file() or source_path.is_symlink() or _sha256(source_path) != expected_hash:
            errors.append(f"runtime checkpoint acceptance source drifted: {relative}")

    accepted_time = _parse_utc_timestamp(
        acceptance.get("accepted_at"), errors, "runtime checkpoint acceptance.accepted_at"
    )
    validated_time = _parse_utc_timestamp(
        acceptance.get("validated_at"), errors, "runtime checkpoint acceptance.validated_at"
    )
    if accepted_time is not None and validated_time is not None and accepted_time != validated_time:
        errors.append("runtime checkpoint acceptance timestamps do not match")
    if recorded_time is not None and accepted_time is not None and recorded_time > accepted_time:
        errors.append("runtime checkpoint acceptance predates the recorded user decision")
    if accepted_time is not None and accepted_time > datetime.now(timezone.utc):
        errors.append("runtime checkpoint acceptance cannot be future-dated")
    return 1


def _ablation_snapshot_sha256(conflict: dict[str, Any]) -> str:
    snapshot = {
        "conflict_id": conflict.get("id"),
        "candidate_variants": conflict.get("candidate_variants"),
        "ablation_rounds": conflict.get("ablation_rounds"),
    }
    encoded = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_hard_gate_assessment(
    root: Path,
    value: object,
    errors: list[str],
    label: str,
    *,
    expected_identity: dict[str, object],
    expected_eligibility: object,
) -> str | None:
    verified = _validate_ablation_evidence(
        root,
        value,
        errors,
        label,
        expected_identity=expected_identity,
    )
    if verified is None:
        return None
    payload = _load_json(root / verified, errors, label)
    if payload is None:
        return None
    if (
        payload.get("format") != HARD_GATE_ASSESSMENT_FORMAT
        or payload.get("schema_version") != 1
    ):
        errors.append(f"{label} has an unsupported hard-gate schema")
    if payload.get("eligibility") != expected_eligibility:
        errors.append(f"{label}.eligibility does not match the variant result")
    gate_results = payload.get("gate_results")
    if not isinstance(gate_results, list):
        errors.append(f"{label}.gate_results must be a list")
        gate_results = []
    authorities: list[str] = []
    statuses: list[str] = []
    for gate_index, gate_result in enumerate(gate_results):
        gate_label = f"{label}.gate_results[{gate_index}]"
        if not isinstance(gate_result, dict):
            errors.append(f"{gate_label} must be an object")
            continue
        authority = gate_result.get("authority")
        status = gate_result.get("status")
        if authority not in HARD_GATE_AUTHORITIES:
            errors.append(f"{gate_label}.authority is invalid")
        else:
            authorities.append(str(authority))
        if status not in {"pass", "fail"}:
            errors.append(f"{gate_label}.status is invalid")
        else:
            statuses.append(str(status))
        sources = gate_result.get("evidence")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{gate_label}.evidence must be a non-empty list")
            sources = []
        for source_index, source in enumerate(sources):
            _validate_hash_bound_file(
                root,
                source,
                errors,
                f"{gate_label}.evidence[{source_index}]",
            )
    if set(authorities) != set(HARD_GATE_AUTHORITIES) or len(authorities) != len(
        HARD_GATE_AUTHORITIES
    ):
        errors.append(f"{label}.gate_results must cover each hard-gate authority exactly once")
    derived_eligibility = "eligible" if statuses and all(
        status == "pass" for status in statuses
    ) and len(statuses) == len(HARD_GATE_AUTHORITIES) else "ineligible"
    if derived_eligibility != expected_eligibility:
        errors.append(
            f"{label}.eligibility is not derived from the independent hard-gate results"
        )
    return verified


def _validate_conflict(
    root: Path,
    conflict: dict[str, Any],
    index: int,
    errors: list[str],
    *,
    require_user_decision: bool = True,
) -> None:
    label = f"conflicts[{index}]"
    status = conflict.get("status")
    if status not in CONFLICT_STATUSES:
        errors.append(f"{label}.status is invalid")
    if require_user_decision and status != "resolved":
        errors.append(f"{label} must be resolved")
    if not require_user_decision and status != "awaiting-user":
        errors.append(f"{label} must await the current user decision")
    conflict_id = conflict.get("id")
    if not _non_empty_string(conflict_id):
        errors.append(f"{label}.id must be non-empty")
        conflict_id = ""
    else:
        conflict_id = str(conflict_id)
    if conflict.get("pair") not in REQUIRED_CONFLICT_COMPARISONS:
        errors.append(f"{label}.pair is invalid")
    if not _non_empty_string(conflict.get("issue")):
        errors.append(f"{label}.issue must be non-empty")
    for legacy_field in ("authority_basis", "deciding_component"):
        if legacy_field in conflict:
            errors.append(
                f"{label}.{legacy_field} is forbidden because automatic domain precedence is forbidden"
            )

    variants = conflict.get("candidate_variants")
    candidate_ids: list[str] = []
    if not isinstance(variants, list) or len(variants) < 2:
        errors.append(f"{label}.candidate_variants must contain at least 2 variants")
        variants = []
    for variant_index, variant in enumerate(variants):
        variant_label = f"{label}.candidate_variants[{variant_index}]"
        if not isinstance(variant, dict):
            errors.append(f"{variant_label} must be an object")
            continue
        variant_id = variant.get("variant_id")
        if not _non_empty_string(variant_id):
            errors.append(f"{variant_label}.variant_id must be non-empty")
            continue
        candidate_ids.append(str(variant_id))
        if not _non_empty_string(variant.get("label")):
            errors.append(f"{variant_label}.label must be non-empty")
    candidate_set = set(candidate_ids)
    if len(candidate_ids) != len(candidate_set):
        errors.append(f"{label}.candidate_variants repeats variant_id")

    rounds = conflict.get("ablation_rounds")
    if not isinstance(rounds, list):
        errors.append(f"{label}.ablation_rounds must be a list")
        rounds = []
    if len(rounds) < CONFLICT_RESOLUTION_POLICY["minimum_ablation_rounds"]:
        errors.append(f"{label}.ablation_rounds must contain at least 2 ablation rounds")
    round_ids: list[str] = []
    controlled_changes: list[str] = []
    round_evidence_sets: list[frozenset[str]] = []
    selected_eligibility = {variant_id: True for variant_id in candidate_set}
    for round_index, round_payload in enumerate(rounds):
        round_label = f"{label}.ablation_rounds[{round_index}]"
        if not isinstance(round_payload, dict):
            errors.append(f"{round_label} must be an object")
            continue
        round_id = round_payload.get("round_id")
        if not _non_empty_string(round_id):
            errors.append(f"{round_label}.round_id must be non-empty")
        else:
            round_ids.append(str(round_id))
        controlled_change = round_payload.get("controlled_change")
        if not _non_empty_string(controlled_change):
            errors.append(f"{round_label}.controlled_change must be non-empty")
        else:
            controlled_changes.append(str(controlled_change).strip().casefold())
        axes = round_payload.get("evaluation_axes")
        if not isinstance(axes, list) or not axes or any(
            not _non_empty_string(axis) for axis in axes
        ):
            errors.append(f"{round_label}.evaluation_axes must be a non-empty list")

        results = round_payload.get("variant_results")
        if not isinstance(results, list) or len(results) < 2:
            errors.append(f"{round_label}.variant_results must contain at least 2 variants")
            results = []
        result_ids: list[str] = []
        round_evidence: set[str] = set()
        control_variant_id = round_payload.get("control_variant_id")
        if not _non_empty_string(control_variant_id) or control_variant_id not in candidate_set:
            errors.append(f"{round_label}.control_variant_id is invalid")
        for result_index, result in enumerate(results):
            result_label = f"{round_label}.variant_results[{result_index}]"
            if not isinstance(result, dict):
                errors.append(f"{result_label} must be an object")
                continue
            variant_id = result.get("variant_id")
            if not _non_empty_string(variant_id):
                errors.append(f"{result_label}.variant_id must be non-empty")
                continue
            variant_id = str(variant_id)
            result_ids.append(variant_id)
            changed_axes = result.get("changed_axes")
            if not isinstance(changed_axes, list) or any(
                not _non_empty_string(axis) for axis in changed_axes
            ):
                errors.append(f"{result_label}.changed_axes must be a list")
            elif variant_id == control_variant_id and changed_axes:
                errors.append(f"{result_label}.changed_axes must be empty for the control")
            elif variant_id != control_variant_id and len(changed_axes) != 1:
                errors.append(
                    f"{result_label}.changed_axes must identify exactly one ablated factor"
                )
            eligibility = result.get("eligibility")
            if eligibility not in VARIANT_ELIGIBILITY:
                errors.append(f"{result_label}.eligibility is invalid")
            elif eligibility == "ineligible" and variant_id in selected_eligibility:
                selected_eligibility[variant_id] = False
            if not _non_empty_string(result.get("result_summary")):
                errors.append(f"{result_label}.result_summary must be non-empty")
            metrics = result.get("metrics")
            if not isinstance(metrics, dict) or not metrics:
                errors.append(f"{result_label}.metrics must be a non-empty object")
            evidence = result.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{result_label}.evidence must be a non-empty list")
                evidence = []
            for evidence_index, item in enumerate(evidence):
                verified = _validate_ablation_evidence(
                    root,
                    item,
                    errors,
                    f"{result_label}.evidence[{evidence_index}]",
                    expected_identity={
                        "conflict_id": conflict_id,
                        "round_id": str(round_id or ""),
                        "variant_id": variant_id,
                    },
                )
                if verified:
                    round_evidence.add(verified)
                    evidence_payload = _load_json(
                        root / verified,
                        errors,
                        f"{result_label}.evidence[{evidence_index}]",
                    )
                    if evidence_payload is not None:
                        if (
                            evidence_payload.get("format") != ABLATION_RESULT_FORMAT
                            or evidence_payload.get("schema_version") != 1
                        ):
                            errors.append(
                                f"{result_label}.evidence[{evidence_index}] has an unsupported result schema"
                            )
                        expected_result_fields = {
                            "controlled_change": controlled_change,
                            "evaluation_axes": axes,
                            "changed_axes": changed_axes,
                            "metrics": metrics,
                        }
                        for field, expected in expected_result_fields.items():
                            if evidence_payload.get(field) != expected:
                                errors.append(
                                    f"{result_label}.evidence[{evidence_index}].{field} "
                                    "does not match the recorded ablation result"
                                )
            hard_gate_verified = _validate_hard_gate_assessment(
                root,
                result.get("hard_gate_assessment"),
                errors,
                f"{result_label}.hard_gate_assessment",
                expected_identity={
                    "conflict_id": conflict_id,
                    "round_id": str(round_id or ""),
                    "variant_id": variant_id,
                },
                expected_eligibility=eligibility,
            )
            if hard_gate_verified:
                round_evidence.add(hard_gate_verified)
        if len(result_ids) != len(set(result_ids)):
            errors.append(f"{round_label}.variant_results repeats variant_id")
        if candidate_set and set(result_ids) != candidate_set:
            errors.append(
                f"{round_label}.variant_results must cover every candidate variant exactly once"
            )
        round_evidence_sets.append(frozenset(round_evidence))

    if len(round_ids) != len(set(round_ids)):
        errors.append(f"{label}.ablation_rounds repeats round_id")
    if len(controlled_changes) != len(set(controlled_changes)):
        errors.append(f"{label}.ablation_rounds must use distinct controlled changes")
    if len(round_evidence_sets) != len(set(round_evidence_sets)):
        errors.append(f"{label}.ablation_rounds must use distinct evidence sets")

    surviving_variants = {
        variant_id
        for variant_id, survives in selected_eligibility.items()
        if survives
    }
    if len(surviving_variants) < CONFLICT_RESOLUTION_POLICY[
        "minimum_surviving_variants_for_user_decision"
    ]:
        errors.append(
            f"{label} must retain at least 2 hard-gate-eligible variants for user decision"
        )

    decision = conflict.get("user_decision")
    if not require_user_decision and decision not in (None, {}):
        errors.append(f"{label}.user_decision must be empty before the user checkpoint")
    if require_user_decision and status == "resolved" and not isinstance(decision, dict):
        errors.append(f"{label}.user_decision must be an object")
    if require_user_decision and isinstance(decision, dict):
        if decision.get("status") != "confirmed":
            errors.append(f"{label}.user_decision.status must be confirmed")
        if not _non_empty_string(decision.get("checkpoint_id")):
            errors.append(f"{label}.user_decision.checkpoint_id must be non-empty")
        selected = decision.get("selected_variant_id")
        if not _non_empty_string(selected) or selected not in candidate_set:
            errors.append(f"{label}.user_decision.selected_variant_id is invalid")
        elif selected not in surviving_variants:
            errors.append(
                f"{label} selected variant must be eligible in every ablation round"
            )
        reviewed = decision.get("reviewed_round_ids")
        if not isinstance(reviewed, list) or len(reviewed) != len(set(map(str, reviewed))):
            errors.append(f"{label}.user_decision.reviewed_round_ids is invalid")
        elif set(map(str, reviewed)) != set(round_ids):
            errors.append(f"{label}.user_decision must acknowledge every ablation round")
        if not _non_empty_string(decision.get("rationale")):
            errors.append(f"{label}.user_decision.rationale must be non-empty")
        decision_evidence = decision.get("decision_evidence")
        decision_path = _validate_ablation_evidence(
            root,
            decision_evidence,
            errors,
            f"{label}.user_decision.decision_evidence",
            expected_identity={
                "conflict_id": conflict_id,
                "checkpoint_id": decision.get("checkpoint_id"),
                "selected_variant_id": selected,
            },
        )
        if decision_path is not None:
            decision_payload = _load_json(
                root / decision_path,
                errors,
                f"{label}.user_decision.decision_evidence",
            )
            if decision_payload is not None:
                if decision_payload.get("format") != "modickx-user-conflict-decision":
                    errors.append(f"{label}.user_decision.decision_evidence.format is invalid")
                if decision_payload.get("schema_version") != 1:
                    errors.append(
                        f"{label}.user_decision.decision_evidence.schema_version is invalid"
                    )
                for field in (
                    "checkpoint_id",
                    "status",
                    "selected_variant_id",
                    "reviewed_round_ids",
                ):
                    if decision_payload.get(field) != decision.get(field):
                        errors.append(
                            f"{label}.user_decision.decision_evidence.{field} does not match"
                        )
                expected_snapshot = _ablation_snapshot_sha256(conflict)
                if decision_payload.get("ablation_snapshot_sha256") != expected_snapshot:
                    errors.append(
                        f"{label}.user_decision.decision_evidence is stale for the current ablation snapshot"
                    )
                if decision_payload.get("checkpoint_skill") != "manuscript-qa":
                    errors.append(
                        f"{label}.user_decision.decision_evidence.checkpoint_skill is invalid"
                    )
                for timestamp_field in ("checkpoint_opened_at", "recorded_at"):
                    if not _non_empty_string(decision_payload.get(timestamp_field)):
                        errors.append(
                            f"{label}.user_decision.decision_evidence.{timestamp_field} must be non-empty"
                        )
                request_verified = _validate_hash_bound_file(
                    root,
                    decision_payload.get("request_snapshot"),
                    errors,
                    f"{label}.user_decision.decision_evidence.request_snapshot",
                )
                if request_verified is not None:
                    request_payload = _load_json(
                        root / request_verified,
                        errors,
                        f"{label}.user_decision.decision_evidence.request_snapshot",
                    )
                    request_conflicts = (
                        request_payload.get("conflicts", [])
                        if isinstance(request_payload, dict)
                        else []
                    )
                    request_conflict = next(
                        (
                            item
                            for item in request_conflicts
                            if isinstance(item, dict) and item.get("id") == conflict_id
                        ),
                        None,
                    )
                    if (
                        not isinstance(request_payload, dict)
                        or request_payload.get("format") != CONFLICT_AUDIT_FORMAT
                        or request_payload.get("schema_version")
                        != CONFLICT_AUDIT_SCHEMA_VERSION
                    ):
                        errors.append(
                            f"{label}.user_decision.decision_evidence.request_snapshot has an unsupported schema"
                        )
                    if not isinstance(request_conflict, dict):
                        errors.append(
                            f"{label}.user_decision.decision_evidence.request_snapshot is missing the conflict"
                        )
                    else:
                        if request_conflict.get("status") != "awaiting-user":
                            errors.append(
                                f"{label}.user_decision.decision_evidence.request_snapshot was not awaiting user review"
                            )
                        if request_conflict.get("user_decision") not in (None, {}):
                            errors.append(
                                f"{label}.user_decision.decision_evidence.request_snapshot already contains a decision"
                            )
                        for field in ("candidate_variants", "ablation_rounds"):
                            if request_conflict.get(field) != conflict.get(field):
                                errors.append(
                                    f"{label}.user_decision.decision_evidence.request_snapshot.{field} is stale"
                                )
                receipt_verified = _validate_hash_bound_file(
                    root,
                    decision_payload.get("checkpoint_receipt"),
                    errors,
                    f"{label}.user_decision.decision_evidence.checkpoint_receipt",
                )
                if receipt_verified is not None:
                    receipt_payload = _load_json(
                        root / receipt_verified,
                        errors,
                        f"{label}.user_decision.decision_evidence.checkpoint_receipt",
                    )
                    if (
                        receipt_payload is None
                        or receipt_payload.get("format")
                        != "modickx-final-review-checkpoint-receipt"
                        or receipt_payload.get("schema_version") != 1
                    ):
                        errors.append(
                            f"{label}.user_decision.decision_evidence.checkpoint_receipt has an unsupported schema"
                        )
                    else:
                        for field in (
                            "checkpoint_id",
                            "checkpoint_skill",
                            "checkpoint_opened_at",
                            "recorded_at",
                            "request_snapshot",
                        ):
                            if receipt_payload.get(field) != decision_payload.get(field):
                                errors.append(
                                    f"{label}.user_decision.decision_evidence.checkpoint_receipt.{field} does not match"
                                )
                        if receipt_payload.get("decision") != "continue":
                            errors.append(
                                f"{label}.user_decision.decision_evidence.checkpoint_receipt was not continued"
                            )
                        receipt_decisions = receipt_payload.get("conflict_decisions")
                        receipt_decision = next(
                            (
                                item
                                for item in receipt_decisions
                                if isinstance(item, dict)
                                and item.get("conflict_id") == conflict_id
                            ),
                            None,
                        ) if isinstance(receipt_decisions, list) else None
                        if not isinstance(receipt_decision, dict):
                            errors.append(
                                f"{label}.user_decision.decision_evidence.checkpoint_receipt is missing the conflict decision"
                            )
                        else:
                            for field in (
                                "selected_variant_id",
                                "reviewed_round_ids",
                                "rationale",
                            ):
                                if receipt_decision.get(field) != decision.get(field):
                                    errors.append(
                                        f"{label}.user_decision.decision_evidence.checkpoint_receipt.{field} does not match"
                                    )

    if require_user_decision and status == "resolved" and not _non_empty_string(conflict.get("resolution")):
        errors.append(f"{label}.resolution must be non-empty")
    if not require_user_decision and _non_empty_string(conflict.get("resolution")):
        errors.append(f"{label}.resolution must be empty before the user checkpoint")
    evidence_paths = conflict.get("evidence_paths")
    if not isinstance(evidence_paths, list) or not evidence_paths:
        errors.append(f"{label}.evidence_paths must be non-empty")
    else:
        for evidence_index, evidence_path in enumerate(evidence_paths):
            _resolved_local_file(
                root,
                evidence_path,
                errors,
                f"{label}.evidence_paths[{evidence_index}]",
            )


def validate_conflict_decision_request(
    ledger_path: str | Path,
) -> dict[str, Any]:
    """Validate an unresolved conflict ledger before opening a user checkpoint."""

    ledger = Path(ledger_path).resolve()
    root = ledger.parent
    errors: list[str] = []
    payload = _load_json(ledger, errors, "final review decision request")
    if payload is None:
        return {"status": "blocked", "errors": errors, "conflict_count": 0}
    if (
        payload.get("format") != CONFLICT_AUDIT_FORMAT
        or payload.get("schema_version") != CONFLICT_AUDIT_SCHEMA_VERSION
    ):
        errors.append("final review decision request has an unsupported schema")

    coverage = payload.get("comparison_coverage")
    coverage_values = [str(item) for item in coverage] if isinstance(coverage, list) else []
    if (
        set(coverage_values) != REQUIRED_CONFLICT_COMPARISONS
        or len(coverage_values) != len(set(coverage_values))
    ):
        errors.append("final review decision request comparison coverage is invalid")

    conflicts = payload.get("conflicts")
    if not isinstance(conflicts, list) or any(
        not isinstance(item, dict) for item in conflicts
    ):
        errors.append("final review decision request conflicts must be a list of objects")
        conflicts = []
    conflict_ids: list[str] = []
    conflict_pairs: dict[str, str] = {}
    for index, conflict in enumerate(conflicts):
        _validate_conflict(
            root,
            conflict,
            index,
            errors,
            require_user_decision=False,
        )
        conflict_id = conflict.get("id")
        if _non_empty_string(conflict_id):
            conflict_ids.append(str(conflict_id))
            conflict_pairs[str(conflict_id)] = str(conflict.get("pair", ""))
    if len(conflict_ids) != len(set(conflict_ids)):
        errors.append("final review decision request repeats conflict ids")

    comparisons = payload.get("pairwise_comparisons")
    comparison_map: dict[str, dict[str, Any]] = {}
    if not isinstance(comparisons, list):
        errors.append("final review decision request pairwise_comparisons must be a list")
        comparisons = []
    for index, comparison in enumerate(comparisons):
        label = f"pairwise_comparisons[{index}]"
        if not isinstance(comparison, dict):
            errors.append(f"{label} must be an object")
            continue
        pair = comparison.get("pair")
        if pair not in REQUIRED_CONFLICT_COMPARISONS or pair in comparison_map:
            errors.append(f"{label}.pair is invalid or repeated")
            continue
        comparison_map[str(pair)] = comparison
        outcome = comparison.get("outcome")
        linked = comparison.get("conflict_ids")
        if outcome not in PAIRWISE_OUTCOMES:
            errors.append(f"{label}.outcome is invalid")
        if not isinstance(linked, list) or any(
            not _non_empty_string(item) for item in linked
        ):
            errors.append(f"{label}.conflict_ids must be a list of ids")
            linked = []
        if outcome == "no-conflict" and linked:
            errors.append(f"{label} cannot name conflicts when outcome is no-conflict")
        if outcome == "conflicts-recorded" and not linked:
            errors.append(f"{label} must name its conflicts")
        evidence_paths = comparison.get("evidence_paths")
        if not isinstance(evidence_paths, list) or not evidence_paths:
            errors.append(f"{label}.evidence_paths must be a non-empty list")
        else:
            for evidence_index, evidence_path in enumerate(evidence_paths):
                _resolved_local_file(
                    root,
                    evidence_path,
                    errors,
                    f"{label}.evidence_paths[{evidence_index}]",
                )
    if set(comparison_map) != REQUIRED_CONFLICT_COMPARISONS:
        errors.append("final review decision request must contain all pairwise comparisons")
    linked_ids = [
        str(conflict_id)
        for record in comparison_map.values()
        for conflict_id in record.get("conflict_ids", [])
    ]
    if set(linked_ids) != set(conflict_ids) or len(linked_ids) != len(set(linked_ids)):
        errors.append("each conflict must be linked from exactly one matching review pair")
    for conflict_id, pair in conflict_pairs.items():
        record = comparison_map.get(pair, {})
        if conflict_id not in record.get("conflict_ids", []):
            errors.append(f"conflict {conflict_id} is not linked from its declared pair")

    review_inputs = payload.get("review_inputs")
    if not isinstance(review_inputs, list) or not review_inputs:
        errors.append("final review decision request review_inputs must be a non-empty list")
    else:
        seen_inputs: set[str] = set()
        for index, review_input in enumerate(review_inputs):
            label = f"review_inputs[{index}]"
            verified = _validate_hash_bound_file(root, review_input, errors, label)
            if verified is not None:
                if verified in seen_inputs:
                    errors.append(f"{label} repeats {verified}")
                seen_inputs.add(verified)

    return {
        "status": "ready" if not errors else "blocked",
        "errors": errors,
        "conflict_count": len(conflicts),
        "conflict_ids": conflict_ids,
        "ledger": str(ledger),
        "sha256": _sha256(ledger) if ledger.is_file() else "",
    }


def finalize_conflict_decisions(
    ledger_path: str | Path,
    *,
    checkpoint_id: str,
    checkpoint_opened_at: str,
    decisions: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Freeze a reviewed request and write the exact current user decisions."""

    ledger = Path(ledger_path).resolve()
    validation = validate_conflict_decision_request(ledger)
    if validation["status"] != "ready":
        raise IntegratedReviewGateError("; ".join(validation["errors"]))
    if not _non_empty_string(checkpoint_id) or not _non_empty_string(
        checkpoint_opened_at
    ):
        raise IntegratedReviewGateError("a current runtime checkpoint is required")
    payload = _read_required_object(ledger, "final review decision request")
    conflicts = payload.get("conflicts", [])
    supplied = decisions or []
    if not isinstance(supplied, list) or any(
        not isinstance(item, dict) for item in supplied
    ):
        raise IntegratedReviewGateError("conflict decisions must be a list of objects")
    decision_map: dict[str, dict[str, Any]] = {}
    for item in supplied:
        conflict_id = item.get("conflict_id")
        if not _non_empty_string(conflict_id) or str(conflict_id) in decision_map:
            raise IntegratedReviewGateError("conflict decisions contain a missing or repeated id")
        decision_map[str(conflict_id)] = item
    expected_ids = {str(item.get("id")) for item in conflicts}
    if set(decision_map) != expected_ids:
        raise IntegratedReviewGateError(
            "the current checkpoint must decide every conflict exactly once"
        )

    if not conflicts:
        # An empty conflict ledger has no decision to attest. Preserve its
        # bytes and hashes; adding a decision checkpoint would invalidate it.
        return {
            "status": "no-conflicts",
            "ledger": str(ledger),
            "checkpoint_id": checkpoint_id,
            "decision_evidence_paths": [],
            "conflict_count": 0,
        }

    normalized_decisions: list[dict[str, Any]] = []
    for conflict in conflicts:
        conflict_id = str(conflict["id"])
        decision = decision_map[conflict_id]
        selected = decision.get("selected_variant_id")
        candidate_ids = {
            str(item.get("variant_id"))
            for item in conflict.get("candidate_variants", [])
            if isinstance(item, dict)
        }
        surviving = {
            variant_id
            for variant_id in candidate_ids
            if all(
                any(
                    isinstance(result, dict)
                    and result.get("variant_id") == variant_id
                    and result.get("eligibility") == "eligible"
                    for result in round_payload.get("variant_results", [])
                )
                for round_payload in conflict.get("ablation_rounds", [])
                if isinstance(round_payload, dict)
            )
        }
        if selected not in surviving:
            raise IntegratedReviewGateError(
                f"conflict {conflict_id} selection is not a hard-gate-eligible survivor"
            )
        reviewed_rounds = decision.get("reviewed_round_ids")
        round_ids = [
            str(item.get("round_id"))
            for item in conflict.get("ablation_rounds", [])
            if isinstance(item, dict)
        ]
        if not isinstance(reviewed_rounds, list) or set(map(str, reviewed_rounds)) != set(
            round_ids
        ):
            raise IntegratedReviewGateError(
                f"conflict {conflict_id} decision must acknowledge every ablation round"
            )
        rationale = decision.get("rationale")
        if not _non_empty_string(rationale):
            raise IntegratedReviewGateError(
                f"conflict {conflict_id} decision requires a rationale"
            )
        normalized_decisions.append(
            {
                "conflict_id": conflict_id,
                "selected_variant_id": selected,
                "reviewed_round_ids": [str(item) for item in reviewed_rounds],
                "rationale": str(rationale).strip(),
            }
        )

    safe_checkpoint = re.sub(r"[^0-9A-Za-z._-]+", "-", checkpoint_id).strip(".-")
    if not safe_checkpoint:
        raise IntegratedReviewGateError("checkpoint id cannot form a safe evidence path")
    evidence_dir = ledger.parent / "review" / "final-conflict-checkpoints"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    request_path = evidence_dir / f"{safe_checkpoint}-request.json"
    receipt_path = evidence_dir / f"{safe_checkpoint}-receipt.json"
    if request_path.exists() or receipt_path.exists():
        raise IntegratedReviewGateError("checkpoint evidence already exists; open a new checkpoint")
    _write_json(request_path, copy.deepcopy(payload))
    request_ref = {
        "path": request_path.relative_to(ledger.parent).as_posix(),
        "sha256": _sha256(request_path),
    }
    recorded_at = datetime.now(timezone.utc).isoformat()
    receipt_payload = {
        "format": "modickx-final-review-checkpoint-receipt",
        "schema_version": 1,
        "checkpoint_id": checkpoint_id,
        "checkpoint_skill": "manuscript-qa",
        "checkpoint_opened_at": checkpoint_opened_at,
        "recorded_at": recorded_at,
        "decision": "continue",
        "request_snapshot": request_ref,
        "conflict_decisions": normalized_decisions,
    }
    _write_json(receipt_path, receipt_payload)
    receipt_ref = {
        "path": receipt_path.relative_to(ledger.parent).as_posix(),
        "sha256": _sha256(receipt_path),
    }
    finalized = copy.deepcopy(payload)
    written_decisions: list[str] = []
    normalized_map = {
        item["conflict_id"]: item for item in normalized_decisions
    }
    for conflict in finalized.get("conflicts", []):
        conflict_id = str(conflict["id"])
        decision = normalized_map[conflict_id]
        selected = decision["selected_variant_id"]
        reviewed_rounds = decision["reviewed_round_ids"]
        rationale = decision["rationale"]
        safe_conflict = re.sub(r"[^0-9A-Za-z._-]+", "-", conflict_id).strip(".-")
        decision_path = evidence_dir / f"{safe_checkpoint}-{safe_conflict}.json"
        decision_payload = {
            "format": "modickx-user-conflict-decision",
            "schema_version": 1,
            "conflict_id": conflict_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_skill": "manuscript-qa",
            "checkpoint_opened_at": checkpoint_opened_at,
            "recorded_at": recorded_at,
            "status": "confirmed",
            "selected_variant_id": selected,
            "reviewed_round_ids": [str(item) for item in reviewed_rounds],
            "rationale": str(rationale).strip(),
            "ablation_snapshot_sha256": _ablation_snapshot_sha256(conflict),
            "request_snapshot": request_ref,
            "checkpoint_receipt": receipt_ref,
        }
        _write_json(decision_path, decision_payload)
        relative_decision = decision_path.relative_to(ledger.parent).as_posix()
        written_decisions.append(relative_decision)
        conflict["status"] = "resolved"
        conflict["user_decision"] = {
            "checkpoint_id": checkpoint_id,
            "status": "confirmed",
            "selected_variant_id": selected,
            "reviewed_round_ids": [str(item) for item in reviewed_rounds],
            "rationale": str(rationale).strip(),
            "decision_evidence": {
                "path": relative_decision,
                "sha256": _sha256(decision_path),
            },
        }
        conflict["resolution"] = str(rationale).strip()
    finalized["decision_checkpoint"] = {
        "checkpoint_id": checkpoint_id,
        "checkpoint_skill": "manuscript-qa",
        "opened_at": checkpoint_opened_at,
        "recorded_at": recorded_at,
        "request_snapshot": request_ref,
        "checkpoint_receipt": receipt_ref,
    }
    _write_json(ledger, finalized)
    return {
        "status": "resolved",
        "ledger": str(ledger),
        "checkpoint_id": checkpoint_id,
        "request_snapshot": request_ref,
        "checkpoint_receipt": receipt_ref,
        "decision_evidence_paths": written_decisions,
        "conflict_count": len(conflicts),
    }


def validate_gate(
    gate_path: str | Path,
    *,
    expected_profile: str = "",
) -> dict[str, Any]:
    """Return a deterministic, non-compensatory gate verdict."""

    gate = Path(gate_path).resolve()
    errors: list[str] = []
    payload = _load_json(gate, errors, GATE_NAME)
    if payload is None:
        return {
            "status": "blocked",
            "gate": str(gate),
            "errors": errors,
            "component_statuses": {},
            "verified_artifact_count": 0,
        }

    if payload.get("format") != GATE_FORMAT or payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("integrated review gate has an unsupported schema")
    profile = payload.get("publication_profile")
    if not isinstance(profile, str) or not profile.strip():
        errors.append("publication_profile must be non-empty")
    elif expected_profile and profile != expected_profile:
        errors.append("publication_profile does not match the active profile")

    policy = payload.get("decision_policy")
    if not isinstance(policy, dict):
        errors.append("decision_policy must be an object")
        policy = {}
    if policy.get("authority_order") != AUTHORITY_ORDER:
        errors.append("decision_policy.authority_order is invalid")
    if "domain_owners" in policy:
        errors.append("decision_policy.domain_owners is forbidden")
    if policy.get("review_perspectives") != REVIEW_PERSPECTIVES:
        errors.append("decision_policy.review_perspectives is invalid")
    if policy.get("conflict_resolution") != CONFLICT_RESOLUTION_POLICY:
        errors.append("decision_policy.conflict_resolution is invalid")
    if policy.get("score_aggregation") != "forbidden":
        errors.append("decision_policy.score_aggregation must be forbidden")
    if policy.get("release_rule") != "all_applicable_hard_gates_ready":
        errors.append("decision_policy.release_rule must be all_applicable_hard_gates_ready")
    if policy.get("waiver_policy") != "downstream_review_cannot_waive_upstream":
        errors.append("decision_policy.waiver_policy is invalid")
    for key_path in _find_forbidden_release_scores(payload):
        errors.append(f"{key_path} is forbidden because scores cannot determine release")

    components = payload.get("components")
    if not isinstance(components, dict):
        errors.append("components must be an object")
        components = {}
    component_statuses: dict[str, str] = {}
    verified_artifact_count = 0
    review_artifacts: dict[str, list[dict[str, Any]]] = {
        component_id: [] for component_id in COMPONENT_IDS
    }
    root = gate.parent
    for component_id in COMPONENT_IDS:
        component = components.get(component_id)
        if not isinstance(component, dict):
            errors.append(f"components.{component_id} is required")
            continue
        status = component.get("status")
        component_statuses[component_id] = str(status or "missing")
        if status != "ready":
            errors.append(f"components.{component_id}.status must be ready")
        blocking_items = component.get("blocking_items")
        if not isinstance(blocking_items, list):
            errors.append(f"components.{component_id}.blocking_items must be a list")
        elif blocking_items:
            errors.append(f"components.{component_id} retains blocking items")
        if component_id == "bzd" and component.get("score_is_release_gate") is not False:
            errors.append("components.bzd.score_is_release_gate must be false")

        artifacts = component.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"components.{component_id}.artifacts must be non-empty")
            artifacts = []
        roles: set[str] = set()
        reviewer_ids: set[str] = set()
        nature_report_paths: set[str] = set()
        nature_synthesis_path: Path | None = None
        bzd_summary_path: Path | None = None
        for index, artifact in enumerate(artifacts):
            label = f"components.{component_id}.artifacts[{index}]"
            if not isinstance(artifact, dict):
                errors.append(f"{label} must be an object")
                continue
            role = artifact.get("role")
            if not isinstance(role, str) or not role.strip():
                errors.append(f"{label}.role must be non-empty")
                continue
            roles.add(role)
            artifact_path = _resolved_local_file(root, artifact.get("path"), errors, f"{label}.path")
            expected_hash = artifact.get("sha256")
            if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
                errors.append(f"{label}.sha256 must be a lowercase SHA-256 digest")
            elif artifact_path is not None:
                actual_hash = _sha256(artifact_path)
                if actual_hash != expected_hash:
                    errors.append(f"{label} hash mismatch")
                else:
                    verified_artifact_count += 1
                    review_artifacts[component_id].append(
                        {
                            "path": artifact_path.relative_to(root).as_posix(),
                            "sha256": expected_hash,
                        }
                    )

            if artifact_path is None:
                continue
            if component_id == "bzd" and role == "judge-review-summary":
                bzd_summary_path = artifact_path
            elif component_id == "nature" and role == "post-review-synthesis":
                nature_synthesis_path = artifact_path
            elif component_id == "nature" and role == "reviewer-report":
                reviewer_id = _validate_nature_report(artifact_path, artifact, errors, label)
                if reviewer_id:
                    reviewer_ids.add(reviewer_id)
                    nature_report_paths.add(str(artifact.get("path")))

        missing_roles = REQUIRED_ROLES[component_id] - roles
        if missing_roles:
            errors.append(
                f"components.{component_id} is missing roles: {', '.join(sorted(missing_roles))}"
            )
        if component_id == "bzd" and bzd_summary_path is not None:
            _validate_bzd_summary(bzd_summary_path, errors)
        if component_id == "nature":
            declared_count = component.get("reviewer_count")
            if not isinstance(declared_count, int) or isinstance(declared_count, bool) or declared_count < 3:
                errors.append("components.nature.reviewer_count must be at least three")
            if len(reviewer_ids) < 3:
                errors.append("components.nature must include three distinct frozen reviewer reports")
            if nature_synthesis_path is not None:
                _validate_nature_synthesis(nature_synthesis_path, errors)
                synthesis = _load_json(nature_synthesis_path, [], "Nature review synthesis") or {}
                synthesis_paths = {str(item) for item in synthesis.get("reviewer_reports", [])}
                if synthesis_paths != nature_report_paths:
                    errors.append("Nature synthesis reviewer_reports do not match the frozen reports")

    conflict_audit = payload.get("conflict_audit")
    ledger_conflicts: list[dict[str, Any]] | None = None
    ledger_payload: dict[str, Any] | None = None
    if not isinstance(conflict_audit, dict):
        errors.append("conflict_audit must be an object")
    else:
        if conflict_audit.get("role") != "cross-review-conflict-audit":
            errors.append("conflict_audit.role is invalid")
        conflict_path = _resolved_local_file(
            root,
            conflict_audit.get("path"),
            errors,
            "conflict_audit.path",
        )
        expected_hash = conflict_audit.get("sha256")
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            errors.append("conflict_audit.sha256 must be a lowercase SHA-256 digest")
        elif conflict_path is not None:
            if _sha256(conflict_path) != expected_hash:
                errors.append("conflict_audit hash mismatch")
            else:
                verified_artifact_count += 1
        if conflict_path is not None:
            ledger_payload = _load_json(
                conflict_path,
                errors,
                "cross-review conflict audit",
            )
            try:
                ledger_conflicts, _ = _load_conflict_audit(
                    root,
                    conflict_path,
                    review_artifacts,
                )
            except IntegratedReviewGateError as exc:
                errors.append(str(exc))

    conflicts = payload.get("conflicts")
    if not isinstance(conflicts, list):
        errors.append("conflicts must be a list")
        conflicts = []
    elif ledger_conflicts is not None and conflicts != ledger_conflicts:
        errors.append("conflicts do not match the frozen cross-review conflict audit")
    for index, conflict in enumerate(conflicts):
        if not isinstance(conflict, dict):
            errors.append(f"conflicts[{index}] must be an object")
            continue
        _validate_conflict(root, conflict, index, errors)

    if ledger_payload is not None:
        verified_artifact_count += _validate_runtime_checkpoint_attestation(
            root,
            conflict_path,
            ledger_payload,
            [item for item in conflicts if isinstance(item, dict)],
            payload.get("runtime_checkpoint_attestation"),
            errors,
        )

    unresolved = payload.get("unresolved_blocking_items")
    if not isinstance(unresolved, list):
        errors.append("unresolved_blocking_items must be a list")
    elif unresolved:
        errors.append("unresolved_blocking_items must be empty before release")
    if payload.get("final_disposition") != "ready":
        errors.append("final_disposition must be ready")

    return {
        "status": "ready" if not errors else "blocked",
        "gate": str(gate),
        "gate_sha256": _sha256(gate) if gate.is_file() else None,
        "publication_profile": profile,
        "authority_order": list(AUTHORITY_ORDER),
        "component_statuses": component_statuses,
        "verified_artifact_count": verified_artifact_count,
        "errors": errors,
    }


def require_ready_gate(
    gate_path: str | Path,
    *,
    expected_profile: str = "",
) -> dict[str, Any]:
    """Validate a gate and raise a concise error if release is blocked."""

    result = validate_gate(gate_path, expected_profile=expected_profile)
    if result["status"] != "ready":
        details = "; ".join(result["errors"][:6])
        if len(result["errors"]) > 6:
            details += f"; and {len(result['errors']) - 6} more"
        raise IntegratedReviewGateError(f"integrated final review gate is blocked: {details}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--gate", type=Path, help="validate an existing gate")
    action.add_argument("--build-root", type=Path, help="build a gate from this workspace")
    parser.add_argument("--profile", default="")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--conflict-ledger", default="")
    args = parser.parse_args()
    if args.build_root is not None:
        result = build_gate(
            args.build_root,
            publication_profile=args.profile or "competition-cn",
            overwrite=args.overwrite,
            conflict_ledger=args.conflict_ledger or None,
        )
    else:
        result = validate_gate(args.gate, expected_profile=args.profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
