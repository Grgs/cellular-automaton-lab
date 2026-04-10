from __future__ import annotations

from backend.simulation.literature_reference_specs import (
    REFERENCE_FAMILY_SPECS,
    MetadataRequirement,
    ReferenceDepthExpectation,
)
from backend.simulation.topology_types import LatticeTopology

from .fixtures import _canonical_patch_fixture_failures, _local_reference_fixture_failures
from .observation import (
    _component_size_summary,
    _observe_reference_topology,
    _polygon_area_frequencies_by_kind,
)
from .types import ReferenceCheckFailure, ReferencePatchObservation


def _metadata_failures(
    topology: LatticeTopology,
    requirement: MetadataRequirement,
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    matching_cells = [cell for cell in topology.cells if cell.kind == requirement.kind]
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
    degree_histogram = dict(observation.degree_histogram)
    adjacency_pairs = set(observation.adjacency_pairs)
    chirality_adjacency_pairs = set(observation.chirality_adjacency_pairs)
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
    if expectation.require_connected_graph and observation.connected_component_count != 1:
        failures.append(
            ReferenceCheckFailure(
                code="disconnected-topology-graph",
                message=(
                    f"Depth {observation.depth} expected a single connected topology component but saw "
                    f"{observation.connected_component_count} components with sizes "
                    f"{_component_size_summary(observation.disconnected_component_sizes)}."
                ),
                depth=observation.depth,
            )
        )
    if expectation.require_hole_free_surface and observation.hole_count != 0:
        failures.append(
            ReferenceCheckFailure(
                code="surface-holes",
                message=(
                    f"Depth {observation.depth} expected a hole-free surface but saw "
                    f"{observation.hole_count} enclosed gap(s)."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.expected_kind_counts is not None
        and observation.kind_counts != expectation.expected_kind_counts
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-kind-counts",
                message=(
                    f"Depth {observation.depth} expected kind counts "
                    f"{expectation.expected_kind_counts!r} but saw {observation.kind_counts!r}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.expected_orientation_token_counts is not None
        and observation.orientation_token_counts != expectation.expected_orientation_token_counts
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-orientation-token-counts",
                message=(
                    f"Depth {observation.depth} expected orientation-token counts "
                    f"{expectation.expected_orientation_token_counts!r} but saw "
                    f"{observation.orientation_token_counts!r}."
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
    if (
        expectation.expected_adjacency_pairs is not None
        and adjacency_pairs != set(expectation.expected_adjacency_pairs)
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-adjacency-pairs",
                message=(
                    f"Depth {observation.depth} expected adjacency pairs "
                    f"{expectation.expected_adjacency_pairs!r} but saw {observation.adjacency_pairs!r}."
                ),
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
    for pair in expectation.required_chirality_adjacency_pairs:
        normalized = pair if pair[0] <= pair[1] else (pair[1], pair[0])
        if normalized not in chirality_adjacency_pairs:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-chirality-adjacency-pair",
                    message=(
                        f"Depth {observation.depth} is missing required chirality adjacency pair "
                        f"{normalized[0]}/{normalized[1]}."
                    ),
                    depth=observation.depth,
                )
            )
    if (
        expectation.expected_degree_histogram is not None
        and degree_histogram != dict(expectation.expected_degree_histogram)
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-degree-histogram",
                message=(
                    f"Depth {observation.depth} expected degree histogram "
                    f"{expectation.expected_degree_histogram!r} but saw {observation.degree_histogram!r}."
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
        expectation.min_three_opposite_chirality_neighbor_cells is not None
        and observation.three_opposite_chirality_neighbor_cells
        < expectation.min_three_opposite_chirality_neighbor_cells
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-opposite-chirality-triplets",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.min_three_opposite_chirality_neighbor_cells} cells whose three neighbors "
                    f"all have opposite chirality, but saw {observation.three_opposite_chirality_neighbor_cells}."
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
    if expectation.min_unique_polygon_areas_by_kind is not None:
        observed_area_counts = dict(observation.unique_polygon_areas_by_kind)
        for kind, minimum_count in expectation.min_unique_polygon_areas_by_kind:
            if observed_area_counts.get(kind, 0) < minimum_count:
                failures.append(
                    ReferenceCheckFailure(
                        code="insufficient-area-classes",
                        message=(
                            f"Depth {observation.depth} expected at least {minimum_count} distinct polygon-area classes "
                            f"for kind '{kind}' but saw {observed_area_counts.get(kind, 0)}."
                        ),
                        depth=observation.depth,
                    )
                )
    if expectation.min_unique_decoration_variants_by_kind is not None:
        observed_decoration_counts = dict(observation.unique_decoration_variants_by_kind)
        for kind, minimum_count in expectation.min_unique_decoration_variants_by_kind:
            if observed_decoration_counts.get(kind, 0) < minimum_count:
                failures.append(
                    ReferenceCheckFailure(
                        code="insufficient-decoration-variants",
                        message=(
                            f"Depth {observation.depth} expected at least {minimum_count} distinct decoration-token variants "
                            f"for kind '{kind}' but saw {observed_decoration_counts.get(kind, 0)}."
                        ),
                        depth=observation.depth,
                    )
                )
    if (
        expectation.min_bounds_longest_span is not None
        and observation.bounds_longest_span < expectation.min_bounds_longest_span
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-bounds-span",
                message=(
                    f"Depth {observation.depth} expected longest bounds span >= "
                    f"{expectation.min_bounds_longest_span} but saw {observation.bounds_longest_span}."
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


def _depth_topology_expectation_failures(
    *,
    geometry: str,
    depth: int,
    topology: LatticeTopology,
    expectation: ReferenceDepthExpectation,
    observation: ReferencePatchObservation | None = None,
) -> list[ReferenceCheckFailure]:
    active_observation = observation
    if active_observation is None:
        active_observation = _observe_reference_topology(
            geometry=geometry,
            sample_mode=REFERENCE_FAMILY_SPECS[geometry].sample_mode,
            depth=depth,
            topology=topology,
        )

    failures: list[ReferenceCheckFailure] = list(
        _expectation_failures(active_observation, expectation)
    )
    if expectation.expected_polygon_area_frequencies_by_kind is not None:
        observed = _polygon_area_frequencies_by_kind(topology)
        if observed != expectation.expected_polygon_area_frequencies_by_kind:
            failures.append(
                ReferenceCheckFailure(
                    code="unexpected-polygon-area-frequencies",
                    message=(
                        f"Depth {depth} expected polygon-area frequencies "
                        f"{expectation.expected_polygon_area_frequencies_by_kind!r} "
                        f"but saw {observed!r}."
                    ),
                    depth=depth,
                )
            )
    failures.extend(_local_reference_fixture_failures(geometry, depth, topology))
    failures.extend(_canonical_patch_fixture_failures(geometry, depth, topology, expectation))
    return failures

