from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha1
from importlib import import_module
import json
from typing import Literal

from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
from backend.simulation.aperiodic_support import AperiodicPatch, ExactPatchRecord
from backend.simulation.literature_reference_specs import (
    REFERENCE_FAMILY_SPECS,
    STAGED_REFERENCE_WAIVERS,
    BuilderSignalExpectation,
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)


VerificationStatus = Literal["PASS", "KNOWN_DEVIATION", "FAIL"]


@dataclass(frozen=True)
class ReferenceCheckFailure:
    code: str
    message: str
    depth: int | None = None


@dataclass(frozen=True)
class ReferencePatchObservation:
    geometry: str
    depth: int
    total_cells: int
    kind_counts: tuple[tuple[str, int], ...]
    unique_orientation_tokens: int
    unique_chirality_tokens: int
    adjacency_pairs: tuple[tuple[str, str], ...]
    bounds_aspect_ratio: float
    signature: str


@dataclass(frozen=True)
class ReferenceVerificationResult:
    geometry: str
    display_name: str
    status: VerificationStatus
    blocking: bool
    waived: bool
    source_urls: tuple[str, ...]
    observations: tuple[ReferencePatchObservation, ...]
    failures: tuple[ReferenceCheckFailure, ...]

    @property
    def is_success(self) -> bool:
        return self.status != "FAIL"


def _patch_adjacency_pairs(patch: AperiodicPatch) -> tuple[tuple[str, str], ...]:
    by_id = {cell.id: cell for cell in patch.cells}
    pairs: set[tuple[str, str]] = set()
    for cell in patch.cells:
        for neighbor_id in cell.neighbors:
            if neighbor_id not in by_id:
                continue
            left = cell.kind
            right = by_id[neighbor_id].kind
            pairs.add((left, right) if left <= right else (right, left))
    return tuple(sorted(pairs))


def _patch_bounds_aspect_ratio(patch: AperiodicPatch) -> float:
    all_x = [vertex[0] for cell in patch.cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in patch.cells for vertex in cell.vertices]
    if not all_x or not all_y:
        return 0.0
    width = max(all_x) - min(all_x)
    height = max(all_y) - min(all_y)
    shortest = min(width, height)
    if shortest <= 0.0:
        return float("inf")
    return max(width, height) / shortest


def _patch_signature_payload(geometry: str, patch: AperiodicPatch) -> dict[str, object]:
    kind_counts = Counter(cell.kind for cell in patch.cells)
    orientation_counts = Counter(
        cell.orientation_token
        for cell in patch.cells
        if cell.orientation_token is not None
    )
    chirality_counts = Counter(
        cell.chirality_token
        for cell in patch.cells
        if cell.chirality_token is not None
    )
    degree_histogram = Counter(len(cell.neighbors) for cell in patch.cells)
    return {
        "geometry": geometry,
        "patch_depth": patch.patch_depth,
        "kind_counts": sorted(kind_counts.items()),
        "orientation_counts": sorted(orientation_counts.items()),
        "chirality_counts": sorted(chirality_counts.items()),
        "adjacency_pairs": _patch_adjacency_pairs(patch),
        "degree_histogram": sorted(degree_histogram.items()),
        "bounds_aspect_ratio": round(_patch_bounds_aspect_ratio(patch), 6),
    }


def _patch_signature(geometry: str, patch: AperiodicPatch) -> str:
    digest = sha1(
        json.dumps(_patch_signature_payload(geometry, patch), sort_keys=True).encode("utf-8")
    ).hexdigest()
    return digest[:12]


def observe_reference_patch(geometry: str, depth: int) -> ReferencePatchObservation:
    patch = build_aperiodic_patch(geometry, depth)
    kind_counts = Counter(cell.kind for cell in patch.cells)
    unique_orientation_tokens = len(
        {
            cell.orientation_token
            for cell in patch.cells
            if cell.orientation_token is not None
        }
    )
    unique_chirality_tokens = len(
        {
            cell.chirality_token
            for cell in patch.cells
            if cell.chirality_token is not None
        }
    )
    return ReferencePatchObservation(
        geometry=geometry,
        depth=int(depth),
        total_cells=len(patch.cells),
        kind_counts=tuple(sorted(kind_counts.items())),
        unique_orientation_tokens=unique_orientation_tokens,
        unique_chirality_tokens=unique_chirality_tokens,
        adjacency_pairs=_patch_adjacency_pairs(patch),
        bounds_aspect_ratio=round(_patch_bounds_aspect_ratio(patch), 6),
        signature=_patch_signature(geometry, patch),
    )


def _metadata_failures(
    patch: AperiodicPatch,
    requirement: MetadataRequirement,
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    matching_cells = [cell for cell in patch.cells if cell.kind == requirement.kind]
    if not matching_cells:
        failures.append(
            ReferenceCheckFailure(
                code="missing-kind",
                message=f"Required kind '{requirement.kind}' is absent from the patch.",
            )
        )
        return failures
    for field_name in requirement.fields:
        if any(getattr(cell, field_name) is None for cell in matching_cells):
            failures.append(
                ReferenceCheckFailure(
                    code="missing-metadata",
                    message=f"Cells of kind '{requirement.kind}' are missing required metadata field '{field_name}'.",
                )
            )
    return failures


def _expectation_failures(
    observation: ReferencePatchObservation,
    expectation: ReferenceDepthExpectation,
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    kind_counts = dict(observation.kind_counts)
    adjacency_pairs = set(observation.adjacency_pairs)
    if (
        expectation.exact_total_cells is not None
        and observation.total_cells != expectation.exact_total_cells
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-cell-count",
                message=(
                    f"Depth {observation.depth} expected exactly "
                    f"{expectation.exact_total_cells} cells but saw {observation.total_cells}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.minimum_total_cells is not None
        and observation.total_cells < expectation.minimum_total_cells
    ):
        failures.append(
            ReferenceCheckFailure(
                code="too-few-cells",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.minimum_total_cells} cells but saw {observation.total_cells}."
                ),
                depth=observation.depth,
            )
        )
    for kind in expectation.required_kinds:
        if kind_counts.get(kind, 0) <= 0:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-required-kind",
                    message=f"Depth {observation.depth} is missing required kind '{kind}'.",
                    depth=observation.depth,
                )
            )
    for pair in expectation.required_adjacency_pairs:
        normalized = pair if pair[0] <= pair[1] else (pair[1], pair[0])
        if normalized not in adjacency_pairs:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-adjacency-pair",
                    message=(
                        f"Depth {observation.depth} is missing required adjacency pair "
                        f"{normalized[0]}/{normalized[1]}."
                    ),
                    depth=observation.depth,
                )
            )
    if (
        expectation.min_unique_orientation_tokens is not None
        and observation.unique_orientation_tokens < expectation.min_unique_orientation_tokens
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-orientation-diversity",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.min_unique_orientation_tokens} unique orientation tokens "
                    f"but saw {observation.unique_orientation_tokens}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.min_unique_chirality_tokens is not None
        and observation.unique_chirality_tokens < expectation.min_unique_chirality_tokens
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-chirality-diversity",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.min_unique_chirality_tokens} unique chirality tokens "
                    f"but saw {observation.unique_chirality_tokens}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.max_bounds_aspect_ratio is not None
        and observation.bounds_aspect_ratio > expectation.max_bounds_aspect_ratio
    ):
        failures.append(
            ReferenceCheckFailure(
                code="degenerate-bounds",
                message=(
                    f"Depth {observation.depth} expected bounds aspect ratio <= "
                    f"{expectation.max_bounds_aspect_ratio} but saw {observation.bounds_aspect_ratio}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.expected_signature is not None
        and observation.signature != expectation.expected_signature
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-signature",
                message=(
                    f"Depth {observation.depth} expected signature "
                    f"{expectation.expected_signature} but saw {observation.signature}."
                ),
                depth=observation.depth,
            )
        )
    return failures


def _builder_signal_failures(
    expectations: tuple[BuilderSignalExpectation, ...],
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    for expectation in expectations:
        module = import_module(expectation.module)
        value = getattr(module, expectation.attribute, None)
        if value != expectation.expected_value:
            failures.append(
                ReferenceCheckFailure(
                    code="builder-signal-mismatch",
                    message=(
                        f"{expectation.module}.{expectation.attribute} expected "
                        f"{expectation.expected_value!r} but saw {value!r}."
                    ),
                )
            )
    return failures


def _pinwheel_exact_path_failures() -> list[ReferenceCheckFailure]:
    from backend.simulation.aperiodic_pinwheel import collect_pinwheel_exact_records

    failures: list[ReferenceCheckFailure] = []
    for depth in range(4):
        patch = build_aperiodic_patch("pinwheel", depth)
        exact_records = collect_pinwheel_exact_records(depth)
        if len(exact_records) != len(patch.cells):
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-record-mismatch",
                    message=(
                        f"Depth {depth} exact record count {len(exact_records)} "
                        f"did not match patch cell count {len(patch.cells)}."
                    ),
                    depth=depth,
                )
            )
        exact_ids = tuple(sorted(record["id"] for record in exact_records))
        patch_ids = tuple(sorted(cell.id for cell in patch.cells))
        if exact_ids != patch_ids:
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-id-mismatch",
                    message=f"Depth {depth} exact-record ids did not match patch ids.",
                    depth=depth,
                )
            )
    return failures


def _verify_spec(spec: ReferenceFamilySpec) -> ReferenceVerificationResult:
    observations = tuple(
        observe_reference_patch(spec.geometry, depth)
        for depth in sorted(spec.depth_expectations)
    )
    failures: list[ReferenceCheckFailure] = []
    deepest_patch = build_aperiodic_patch(spec.geometry, max(spec.depth_expectations, default=0))
    observed_kinds = {cell.kind for cell in deepest_patch.cells}
    unexpected_kinds = observed_kinds.difference(spec.allowed_public_cell_kinds)
    if unexpected_kinds:
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-kind",
                message=(
                    f"Observed unexpected public kinds for {spec.geometry}: "
                    + ", ".join(sorted(unexpected_kinds))
                ),
            )
        )
    for requirement in spec.required_metadata:
        failures.extend(_metadata_failures(deepest_patch, requirement))
    failures.extend(_builder_signal_failures(spec.builder_signals))
    if spec.exact_reference_mode == "pinwheel_exact":
        failures.extend(_pinwheel_exact_path_failures())
    for observation in observations:
        expectation = spec.depth_expectations[observation.depth]
        failures.extend(_expectation_failures(observation, expectation))

    waived = spec.geometry in STAGED_REFERENCE_WAIVERS
    status: VerificationStatus
    if failures:
        status = "KNOWN_DEVIATION" if waived else "FAIL"
    else:
        status = "PASS"
    return ReferenceVerificationResult(
        geometry=spec.geometry,
        display_name=spec.display_name,
        status=status,
        blocking=status == "FAIL",
        waived=waived,
        source_urls=spec.source_urls,
        observations=observations,
        failures=tuple(failures),
    )


def verify_reference_family(geometry: str) -> ReferenceVerificationResult:
    try:
        spec = REFERENCE_FAMILY_SPECS[geometry]
    except KeyError as error:
        raise ValueError(f"Unsupported reference verification geometry '{geometry}'.") from error
    return _verify_spec(spec)


def verify_all_reference_families() -> tuple[ReferenceVerificationResult, ...]:
    return tuple(
        _verify_spec(spec)
        for _, spec in sorted(REFERENCE_FAMILY_SPECS.items())
    )
