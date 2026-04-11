from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_contracts import APERIODIC_IMPLEMENTATION_CONTRACTS
from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.literature_reference_verification import verify_all_reference_families
from backend.simulation.reference_verification.types import (
    ReferenceCheckFailure,
    ReferencePatchObservation,
    ReferenceVerificationResult,
    VerificationStatus,
)
from backend.simulation.topology_validation import recommended_validation_options


_LOCAL_REFERENCE_FIXTURE_PATH = (
    ROOT / "backend" / "simulation" / "data" / "reference_patch_local_fixtures.json"
)
_CANONICAL_REFERENCE_FIXTURE_PATH = (
    ROOT / "backend" / "simulation" / "data" / "reference_patch_canonical_fixtures.json"
)
_SCHEMA_VERSION = 1

ReportFormat = Literal["summary", "detail", "json"]


@dataclass(frozen=True)
class ObservationSummary:
    depth: int
    total_cells: int
    signature: str
    bounds_longest_span: float
    unique_orientation_tokens: int
    unique_chirality_tokens: int


@dataclass(frozen=True)
class FailureSummary:
    code: str
    message: str
    depth: int | None


@dataclass(frozen=True)
class VerificationStrengthRow:
    geometry: str
    display_name: str
    sample_mode: str
    implementation_status: str
    verification_status: VerificationStatus
    waived: bool
    blocking: bool
    strength_tags: tuple[str, ...]
    verification_modes: tuple[str, ...]
    promotion_blocker: str | None
    source_urls: tuple[str, ...]
    depths: tuple[int, ...]
    exact_reference_mode: str | None
    has_local_reference: bool
    has_canonical_patch: bool
    strict_validation: bool
    failure_codes: tuple[str, ...]
    observations: tuple[ObservationSummary, ...]
    failures: tuple[FailureSummary, ...]


@lru_cache(maxsize=1)
def _load_local_reference_geometries() -> set[str]:
    payload = json.loads(_LOCAL_REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))
    return set(payload)


@lru_cache(maxsize=1)
def _load_canonical_reference_geometries() -> set[str]:
    if not _CANONICAL_REFERENCE_FIXTURE_PATH.exists():
        return set()
    payload = json.loads(_CANONICAL_REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))
    return set(payload)


def _strength_tags(geometry: str) -> tuple[str, ...]:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    tags: list[str] = []
    if any(
        expectation.exact_total_cells is not None or expectation.expected_signature is not None
        for expectation in spec.depth_expectations.values()
    ):
        tags.append("sample-exact")
    if spec.required_metadata:
        tags.append("metadata")
    if spec.periodic_descriptor is not None:
        tags.extend(("descriptor", "vertex-stars"))
        if spec.periodic_descriptor.expected_dual_geometry is not None:
            tags.append("dual-checks")
        if spec.periodic_descriptor.expected_dual_candidate_geometries:
            tags.append("dual-candidate-checks")
    if any(
        expectation.expected_polygon_area_frequencies_by_kind is not None
        for expectation in spec.depth_expectations.values()
    ):
        tags.append("area-hierarchy")
    if geometry in _load_local_reference_geometries():
        tags.append("local-reference")
    if geometry in _load_canonical_reference_geometries():
        tags.append("canonical-patch")
    if spec.exact_reference_mode is not None:
        tags.append("exact-path")
    if all(recommended_validation_options(geometry).values()):
        tags.append("strict-validation")
    return tuple(tags)


def _verification_modes(geometry: str) -> tuple[str, ...]:
    contract = APERIODIC_IMPLEMENTATION_CONTRACTS.get(geometry)
    if contract is not None:
        return contract.verification_modes

    spec = REFERENCE_FAMILY_SPECS[geometry]
    modes: list[str] = []
    if spec.depth_expectations:
        modes.append("depth-expectations")
    if spec.required_metadata:
        modes.append("metadata")
    if spec.periodic_descriptor is not None:
        modes.extend(("descriptor", "vertex-stars"))
        if spec.periodic_descriptor.expected_dual_geometry is not None:
            modes.append("dual-checks")
        if spec.periodic_descriptor.expected_dual_candidate_geometries:
            modes.append("dual-candidate-checks")
    if geometry in _load_local_reference_geometries():
        modes.append("local-reference")
    if geometry in _load_canonical_reference_geometries():
        modes.append("canonical-patch")
    if spec.exact_reference_mode is not None:
        modes.append("exact-path")
    if spec.builder_signals:
        modes.append("builder-signals")
    return tuple(modes)


def _observation_summary(observation: ReferencePatchObservation) -> ObservationSummary:
    return ObservationSummary(
        depth=observation.depth,
        total_cells=observation.total_cells,
        signature=observation.signature,
        bounds_longest_span=observation.bounds_longest_span,
        unique_orientation_tokens=observation.unique_orientation_tokens,
        unique_chirality_tokens=observation.unique_chirality_tokens,
    )


def _failure_summary(failure: ReferenceCheckFailure) -> FailureSummary:
    return FailureSummary(
        code=failure.code,
        message=failure.message,
        depth=failure.depth,
    )


@lru_cache(maxsize=1)
def build_verification_strength_rows() -> tuple[VerificationStrengthRow, ...]:
    live_results = {
        result.geometry: result
        for result in verify_all_reference_families()
    }
    rows: list[VerificationStrengthRow] = []
    for geometry in sorted(REFERENCE_FAMILY_SPECS):
        spec = REFERENCE_FAMILY_SPECS[geometry]
        result = live_results[geometry]
        contract = APERIODIC_IMPLEMENTATION_CONTRACTS.get(geometry)
        failures = tuple(_failure_summary(failure) for failure in result.failures)
        rows.append(
            VerificationStrengthRow(
                geometry=geometry,
                display_name=spec.display_name,
                sample_mode=spec.sample_mode,
                implementation_status=contract.implementation_status if contract is not None else "",
                verification_status=result.status,
                waived=result.waived,
                blocking=result.blocking,
                strength_tags=_strength_tags(geometry),
                verification_modes=_verification_modes(geometry),
                promotion_blocker=contract.promotion_blocker if contract is not None else None,
                source_urls=spec.source_urls,
                depths=tuple(observation.depth for observation in result.observations),
                exact_reference_mode=spec.exact_reference_mode,
                has_local_reference=geometry in _load_local_reference_geometries(),
                has_canonical_patch=geometry in _load_canonical_reference_geometries(),
                strict_validation=all(recommended_validation_options(geometry).values()),
                failure_codes=tuple(sorted({failure.code for failure in result.failures})),
                observations=tuple(_observation_summary(observation) for observation in result.observations),
                failures=failures,
            )
        )
    return tuple(rows)


def _summary_output(rows: tuple[VerificationStrengthRow, ...]) -> str:
    lines = ["geometry\tsample_mode\timplementation_status\tverification_status\tstrength_tags"]
    for row in rows:
        lines.append(
            f"{row.geometry}\t{row.sample_mode}\t{row.implementation_status}\t"
            f"{row.verification_status}\t{','.join(row.strength_tags)}"
        )
    return "\n".join(lines) + "\n"


def _detail_output(rows: tuple[VerificationStrengthRow, ...]) -> str:
    blocks: list[str] = []
    for row in rows:
        lines = [
            f"{row.geometry} ({row.display_name})",
            f"  sample_mode: {row.sample_mode}",
            f"  implementation_status: {row.implementation_status or '-'}",
            f"  verification_status: {row.verification_status}",
            f"  waived: {str(row.waived).lower()}",
            f"  blocking: {str(row.blocking).lower()}",
            f"  verification_modes: {', '.join(row.verification_modes) if row.verification_modes else '-'}",
            f"  strength_tags: {', '.join(row.strength_tags) if row.strength_tags else '-'}",
            f"  exact_reference_mode: {row.exact_reference_mode or '-'}",
            f"  has_local_reference: {str(row.has_local_reference).lower()}",
            f"  has_canonical_patch: {str(row.has_canonical_patch).lower()}",
            f"  strict_validation: {str(row.strict_validation).lower()}",
            f"  failure_codes: {', '.join(row.failure_codes) if row.failure_codes else '-'}",
        ]
        if row.promotion_blocker is not None:
            lines.append(f"  promotion_blocker: {row.promotion_blocker}")
        lines.append("  source_urls:")
        if row.source_urls:
            lines.extend(f"    - {url}" for url in row.source_urls)
        else:
            lines.append("    -")
        lines.append("  observations:")
        if row.observations:
            for observation in row.observations:
                lines.append(
                    "    - "
                    f"depth={observation.depth} cells={observation.total_cells} "
                    f"signature={observation.signature} span={observation.bounds_longest_span} "
                    f"orientations={observation.unique_orientation_tokens} "
                    f"chirality={observation.unique_chirality_tokens}"
                )
        else:
            lines.append("    -")
        if row.failures:
            lines.append("  failures:")
            for failure in row.failures:
                prefix = f"{failure.code}[d{failure.depth}]" if failure.depth is not None else failure.code
                lines.append(f"    - {prefix}: {failure.message}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _json_output(rows: tuple[VerificationStrengthRow, ...]) -> str:
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "families": [asdict(row) for row in rows],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_verification_strength_report(
    rows: tuple[VerificationStrengthRow, ...],
    *,
    output_format: ReportFormat = "summary",
) -> str:
    if output_format == "summary":
        return _summary_output(rows)
    if output_format == "detail":
        return _detail_output(rows)
    if output_format == "json":
        return _json_output(rows)
    raise ValueError(f"Unsupported report format '{output_format}'.")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report literature verification strength and live verification status for each tiling family.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "detail", "json"),
        default="summary",
        help="Select the report format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to write the rendered report to.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    rows = build_verification_strength_rows()
    rendered = render_verification_strength_report(rows, output_format=args.format)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
