from __future__ import annotations

from collections import Counter
import math
import re

from backend.simulation.literature_reference_specs import (
    REFERENCE_FAMILY_SPECS,
    PeriodicDescriptorExpectation,
    ReferenceFamilySpec,
)
from backend.simulation.periodic_face_tilings import (
    PeriodicFaceCell,
    PeriodicFaceTilingDescriptor,
    get_periodic_face_tiling_descriptor,
    is_periodic_face_tiling,
)

from .observation import _periodic_face_sample_size
from .types import ReferenceCheckFailure

_FLOAT_TOLERANCE = 1e-6


def _compile_periodic_face_id_pattern(id_pattern: str) -> re.Pattern[str]:
    token_patterns = {
        "prefix": r"(?P<prefix>[^:]+)",
        "slot": r"(?P<slot>[^:]+)",
        "x": r"(?P<x>\d+)",
        "y": r"(?P<y>\d+)",
    }
    parts: list[str] = []
    position = 0
    for match in re.finditer(r"\{(prefix|slot|x|y)\}", id_pattern):
        parts.append(re.escape(id_pattern[position:match.start()]))
        parts.append(token_patterns[match.group(1)])
        position = match.end()
    parts.append(re.escape(id_pattern[position:]))
    return re.compile("^" + "".join(parts) + "$")


def _parse_periodic_face_cell_id(
    descriptor: PeriodicFaceTilingDescriptor,
    cell_id: str,
) -> dict[str, str] | None:
    match = _compile_periodic_face_id_pattern(descriptor.id_pattern).fullmatch(cell_id)
    if match is None:
        return None
    return {key: value for key, value in match.groupdict().items() if value is not None}


def _verify_periodic_face_id_roundtrip(
    descriptor: PeriodicFaceTilingDescriptor,
    cell: PeriodicFaceCell,
) -> ReferenceCheckFailure | None:
    parsed = _parse_periodic_face_cell_id(descriptor, cell.id)
    if parsed is None:
        return ReferenceCheckFailure(
            code="descriptor-id-pattern-mismatch",
            message=f"{descriptor.geometry} cell id '{cell.id}' did not match descriptor pattern {descriptor.id_pattern!r}.",
        )
    if "slot" in parsed and parsed["slot"] != cell.slot:
        return ReferenceCheckFailure(
            code="descriptor-slot-roundtrip-mismatch",
            message=(
                f"{descriptor.geometry} cell id '{cell.id}' encoded slot {parsed['slot']!r} "
                f"but the generated cell slot was {cell.slot!r}."
            ),
        )
    if "x" not in parsed or "y" not in parsed:
        return ReferenceCheckFailure(
            code="descriptor-missing-grid-coordinates",
            message=f"{descriptor.geometry} descriptor id pattern must encode both x and y coordinates.",
        )
    reconstructed_id = descriptor.id_pattern.format(
        prefix=parsed.get("prefix", ""),
        slot=cell.slot or "",
        x=int(parsed["x"]),
        y=int(parsed["y"]),
    )
    if reconstructed_id != cell.id:
        return ReferenceCheckFailure(
            code="descriptor-id-roundtrip-mismatch",
            message=(
                f"{descriptor.geometry} cell id '{cell.id}' did not round-trip through the descriptor "
                f"pattern; reconstructed '{reconstructed_id}'."
            ),
        )
    return None


def _canonicalize_vertex_configuration(configuration: tuple[str, ...]) -> tuple[str, ...]:
    if not configuration:
        return ()
    candidates: list[tuple[str, ...]] = []
    for direction in (configuration, tuple(reversed(configuration))):
        for index in range(len(direction)):
            candidates.append(direction[index:] + direction[:index])
    return min(candidates)


def _periodic_face_interior_vertex_configuration_occurrences(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[tuple[str, ...], ...]:
    def _matching_group_id(
        groups: list[list[tuple[float, float]]],
        point: tuple[float, float],
    ) -> int | None:
        for group_id, group in enumerate(groups):
            representative = group[0]
            if (
                math.isclose(representative[0], point[0], abs_tol=_FLOAT_TOLERANCE)
                and math.isclose(representative[1], point[1], abs_tol=_FLOAT_TOLERANCE)
            ):
                return group_id
        return None

    vertex_groups: list[list[tuple[float, float]]] = []
    vertex_group_by_cell_vertex: dict[tuple[int, int], int] = {}
    incident_cells_by_group: dict[int, set[str]] = {}
    cells_by_id = {cell.id: cell for cell in cells}

    for cell_index, cell in enumerate(cells):
        for vertex_index, point in enumerate(cell.vertices):
            group_id = _matching_group_id(vertex_groups, point)
            if group_id is None:
                group_id = len(vertex_groups)
                vertex_groups.append([point])
            else:
                vertex_groups[group_id].append(point)
            vertex_group_by_cell_vertex[(cell_index, vertex_index)] = group_id
            incident_cells_by_group.setdefault(group_id, set()).add(cell.id)

    if not vertex_groups:
        return ()

    representative_points: dict[int, tuple[float, float]] = {}
    for group_id, group in enumerate(vertex_groups):
        representative_points[group_id] = (
            sum(point[0] for point in group) / len(group),
            sum(point[1] for point in group) / len(group),
        )

    edge_counts: Counter[tuple[int, int]] = Counter()
    for cell_index, cell in enumerate(cells):
        for vertex_index in range(len(cell.vertices)):
            left_group = vertex_group_by_cell_vertex[(cell_index, vertex_index)]
            right_group = vertex_group_by_cell_vertex[
                (cell_index, (vertex_index + 1) % len(cell.vertices))
            ]
            if left_group == right_group:
                continue
            edge = (
                (left_group, right_group)
                if left_group <= right_group
                else (right_group, left_group)
            )
            edge_counts[edge] += 1

    boundary_vertex_groups = {
        group_id
        for edge, count in edge_counts.items()
        if count == 1
        for group_id in edge
    }

    all_x = [point[0] for point in representative_points.values()]
    all_y = [point[1] for point in representative_points.values()]
    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)
    for group_id, point in representative_points.items():
        if (
            math.isclose(point[0], min_x, abs_tol=_FLOAT_TOLERANCE)
            or math.isclose(point[0], max_x, abs_tol=_FLOAT_TOLERANCE)
            or math.isclose(point[1], min_y, abs_tol=_FLOAT_TOLERANCE)
            or math.isclose(point[1], max_y, abs_tol=_FLOAT_TOLERANCE)
        ):
            boundary_vertex_groups.add(group_id)

    configurations: list[tuple[str, ...]] = []
    for group_id, cell_ids in incident_cells_by_group.items():
        if group_id in boundary_vertex_groups:
            continue
        point = representative_points[group_id]
        incident_cells = [cells_by_id[cell_id] for cell_id in cell_ids]
        ordered_cells = sorted(
            incident_cells,
            key=lambda cell: math.atan2(
                cell.center[1] - point[1],
                cell.center[0] - point[0],
            ),
        )
        configurations.append(
            _canonicalize_vertex_configuration(
                tuple(cell.kind for cell in ordered_cells)
            )
        )
    return tuple(sorted(configurations))


def _periodic_face_interior_vertex_configurations(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        sorted(set(_periodic_face_interior_vertex_configuration_occurrences(cells)))
    )


def _periodic_face_interior_vertex_configuration_frequencies(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[tuple[tuple[str, ...], int], ...]:
    return tuple(
        sorted(
            Counter(
                _periodic_face_interior_vertex_configuration_occurrences(cells)
            ).items()
        )
    )


def _periodic_face_vertex_valence_frequency_signature(
    configuration_frequencies: tuple[tuple[tuple[str, ...], int], ...],
) -> tuple[tuple[int, int], ...]:
    return tuple(
        sorted(
            (len(configuration), count)
            for configuration, count in configuration_frequencies
        )
    )


def _periodic_face_unique_polygon_side_counts(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[int, ...]:
    return tuple(sorted({len(cell.vertices) for cell in cells}))


def _periodic_face_dual_structure_failure(
    *,
    geometry: str,
    periodic_descriptor: PeriodicDescriptorExpectation,
    sample_cells: tuple[PeriodicFaceCell, ...],
    observed_vertex_configurations: tuple[tuple[str, ...], ...],
) -> ReferenceCheckFailure | None:
    dual_geometry = periodic_descriptor.expected_dual_geometry
    if dual_geometry is None:
        return None
    dual_spec = REFERENCE_FAMILY_SPECS.get(dual_geometry)
    if dual_spec is None or dual_spec.periodic_descriptor is None or not is_periodic_face_tiling(dual_geometry):
        return ReferenceCheckFailure(
            code="descriptor-dual-geometry-missing",
            message=(
                f"{geometry} expected periodic dual geometry {dual_geometry!r}, "
                "but no matching periodic reference spec was available."
            ),
        )
    if dual_spec.periodic_descriptor.expected_dual_geometry != geometry:
        return ReferenceCheckFailure(
            code="descriptor-dual-geometry-not-reciprocal",
            message=(
                f"{geometry} expected reciprocal dual geometry {dual_geometry!r}, "
                f"but that spec pointed to {dual_spec.periodic_descriptor.expected_dual_geometry!r}."
            ),
        )

    dual_width, dual_height = _periodic_face_sample_size(
        dual_spec,
        max(dual_spec.depth_expectations, default=3),
    )
    dual_cells = get_periodic_face_tiling_descriptor(dual_geometry).build_faces(
        dual_width,
        dual_height,
    )
    observed_side_counts = _periodic_face_unique_polygon_side_counts(sample_cells)
    observed_vertex_valences = tuple(sorted({len(configuration) for configuration in observed_vertex_configurations}))
    dual_side_counts = _periodic_face_unique_polygon_side_counts(dual_cells)
    dual_vertex_valences = tuple(
        sorted(
            {
                len(configuration)
                for configuration in _periodic_face_interior_vertex_configurations(dual_cells)
            }
        )
    )
    if observed_side_counts != dual_vertex_valences or dual_side_counts != observed_vertex_valences:
        return ReferenceCheckFailure(
            code="descriptor-dual-structure-mismatch",
            message=(
                f"{geometry} expected reciprocal dual structure with {dual_geometry}: "
                f"face side counts {observed_side_counts!r} vs dual interior vertex valences {dual_vertex_valences!r}, "
                f"and interior vertex valences {observed_vertex_valences!r} vs dual face side counts {dual_side_counts!r}."
            ),
        )
    return None


def _periodic_face_dual_candidate_failure(
    *,
    geometry: str,
    periodic_descriptor: PeriodicDescriptorExpectation,
    sample_cells: tuple[PeriodicFaceCell, ...],
    observed_vertex_configurations: tuple[tuple[str, ...], ...],
    observed_vertex_configuration_frequencies: tuple[tuple[tuple[str, ...], int], ...],
) -> ReferenceCheckFailure | None:
    expected_candidates = tuple(sorted(periodic_descriptor.expected_dual_candidate_geometries))
    expected_signature = periodic_descriptor.expected_dual_structure_signature
    if not expected_candidates and expected_signature is None:
        return None

    observed_side_counts = _periodic_face_unique_polygon_side_counts(sample_cells)
    observed_vertex_valences = tuple(sorted({len(configuration) for configuration in observed_vertex_configurations}))
    candidate_geometries: list[str] = []
    for candidate_geometry, candidate_spec in sorted(REFERENCE_FAMILY_SPECS.items()):
        if candidate_geometry == geometry:
            continue
        if candidate_spec.periodic_descriptor is None or not is_periodic_face_tiling(candidate_geometry):
            continue
        candidate_width, candidate_height = _periodic_face_sample_size(
            candidate_spec,
            max(candidate_spec.depth_expectations, default=3),
        )
        candidate_cells = get_periodic_face_tiling_descriptor(candidate_geometry).build_faces(
            candidate_width,
            candidate_height,
        )
        candidate_side_counts = _periodic_face_unique_polygon_side_counts(candidate_cells)
        candidate_vertex_valences = tuple(
            sorted(
                {
                    len(configuration)
                    for configuration in _periodic_face_interior_vertex_configurations(candidate_cells)
                }
            )
        )
        if observed_side_counts == candidate_vertex_valences and candidate_side_counts == observed_vertex_valences:
            candidate_geometries.append(candidate_geometry)
    observed_candidates = tuple(candidate_geometries)
    if expected_candidates and observed_candidates != expected_candidates:
        return ReferenceCheckFailure(
            code="descriptor-dual-candidate-class-mismatch",
            message=(
                f"{geometry} expected periodic dual candidate class {expected_candidates!r} "
                f"but observed {observed_candidates!r}."
            ),
        )

    observed_signature = _periodic_face_vertex_valence_frequency_signature(
        observed_vertex_configuration_frequencies
    )
    if expected_signature is not None and observed_signature != expected_signature:
        return ReferenceCheckFailure(
            code="descriptor-dual-candidate-structure-mismatch",
            message=(
                f"{geometry} expected periodic dual-structure signature "
                f"{expected_signature!r} but saw {observed_signature!r}."
            ),
        )
    return None


def _periodic_face_translation_failures(
    descriptor: PeriodicFaceTilingDescriptor,
    cells: tuple[PeriodicFaceCell, ...],
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    cells_by_slot_and_grid: dict[tuple[str, int, int], PeriodicFaceCell] = {}
    for cell in cells:
        parsed = _parse_periodic_face_cell_id(descriptor, cell.id)
        if parsed is None or "x" not in parsed or "y" not in parsed or cell.slot is None:
            continue
        cells_by_slot_and_grid[(cell.slot, int(parsed["x"]), int(parsed["y"]))] = cell

    for (slot, logical_x, logical_y), cell in sorted(cells_by_slot_and_grid.items()):
        right = cells_by_slot_and_grid.get((slot, logical_x + 1, logical_y))
        if right is not None:
            delta_x = right.center[0] - cell.center[0]
            delta_y = right.center[1] - cell.center[1]
            if not math.isclose(delta_x, descriptor.unit_width, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-x-translation-mismatch",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} expected x translation {descriptor.unit_width} "
                            f"but saw {round(delta_x, 6)} between logical cells ({logical_x},{logical_y}) and ({logical_x + 1},{logical_y})."
                        ),
                    )
                )
            if not math.isclose(delta_y, 0.0, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-x-translation-y-drift",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} drifted in y by {round(delta_y, 6)} "
                            f"across x translation at logical row {logical_y}."
                        ),
                    )
                )

        below = cells_by_slot_and_grid.get((slot, logical_x, logical_y + 1))
        if below is not None:
            expected_delta_x = (
                descriptor.row_offset_x
                if (logical_y + 1) % 2 == 1
                else 0.0
            ) - (descriptor.row_offset_x if logical_y % 2 == 1 else 0.0)
            delta_x = below.center[0] - cell.center[0]
            delta_y = below.center[1] - cell.center[1]
            if not math.isclose(delta_y, descriptor.unit_height, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-y-translation-mismatch",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} expected y translation {descriptor.unit_height} "
                            f"but saw {round(delta_y, 6)} between logical rows {logical_y} and {logical_y + 1}."
                        ),
                    )
                )
            if not math.isclose(delta_x, expected_delta_x, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-row-offset-mismatch",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} expected row-offset delta {expected_delta_x} "
                            f"but saw {round(delta_x, 6)} between logical rows {logical_y} and {logical_y + 1}."
                        ),
                    )
                )
    return failures


def _periodic_face_descriptor_failures(spec: ReferenceFamilySpec) -> list[ReferenceCheckFailure]:
    if not is_periodic_face_tiling(spec.geometry):
        return []
    descriptor = get_periodic_face_tiling_descriptor(spec.geometry)
    failures: list[ReferenceCheckFailure] = []
    if descriptor.metric_model != "pattern":
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-descriptor-metric-model",
                message=(
                    f"{spec.geometry} descriptor expected metric_model 'pattern' "
                    f"but saw {descriptor.metric_model!r}."
                ),
            )
        )
    if descriptor.cell_count_per_unit != descriptor.face_template_count:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-cell-count-mismatch",
                message=(
                    f"{spec.geometry} descriptor declared cell_count_per_unit "
                    f"{descriptor.cell_count_per_unit} but loaded {descriptor.face_template_count} face templates."
                ),
            )
        )
    if set(descriptor.face_kinds) != set(spec.allowed_public_cell_kinds):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-kind-vocabulary-mismatch",
                message=(
                    f"{spec.geometry} descriptor face kinds {descriptor.face_kinds!r} "
                    f"did not match the reference spec kinds {spec.allowed_public_cell_kinds!r}."
                ),
            )
        )
    periodic_descriptor = spec.periodic_descriptor
    if periodic_descriptor is None:
        return failures
    if descriptor.face_template_count != periodic_descriptor.face_template_count:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-face-template-count-mismatch",
                message=(
                    f"{spec.geometry} descriptor face template count {descriptor.face_template_count} "
                    f"did not match the reference expectation {periodic_descriptor.face_template_count}."
                ),
            )
        )
    if descriptor.face_slots != periodic_descriptor.slot_vocabulary:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-slot-vocabulary-mismatch",
                message=(
                    f"{spec.geometry} descriptor slots {descriptor.face_slots!r} "
                    f"did not match the reference expectation {periodic_descriptor.slot_vocabulary!r}."
                ),
            )
        )
    if descriptor.id_pattern != periodic_descriptor.id_pattern:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-id-pattern-mismatch",
                message=(
                    f"{spec.geometry} descriptor id pattern {descriptor.id_pattern!r} "
                    f"did not match the reference expectation {periodic_descriptor.id_pattern!r}."
                ),
            )
        )
    if not math.isclose(descriptor.row_offset_x, periodic_descriptor.row_offset_x, abs_tol=_FLOAT_TOLERANCE):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-row-offset-field-mismatch",
                message=(
                    f"{spec.geometry} descriptor row_offset_x {descriptor.row_offset_x} "
                    f"did not match the reference expectation {periodic_descriptor.row_offset_x}."
                ),
            )
        )
    sample_width, sample_height = _periodic_face_sample_size(
        spec,
        max(spec.depth_expectations, default=3),
    )
    sample_cells = descriptor.build_faces(sample_width, sample_height)
    for cell in sample_cells:
        failure = _verify_periodic_face_id_roundtrip(descriptor, cell)
        if failure is not None:
            failures.append(failure)
    observed_vertex_configurations = _periodic_face_interior_vertex_configurations(sample_cells)
    observed_vertex_configuration_frequencies = _periodic_face_interior_vertex_configuration_frequencies(sample_cells)
    if (
        observed_vertex_configurations
        != periodic_descriptor.expected_interior_vertex_configurations
    ):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-interior-vertex-configurations-mismatch",
                message=(
                    f"{spec.geometry} interior vertex configurations "
                    f"{observed_vertex_configurations!r} did not match the reference expectation "
                    f"{periodic_descriptor.expected_interior_vertex_configurations!r}."
                ),
            )
        )
    if (
        observed_vertex_configuration_frequencies
        != periodic_descriptor.expected_interior_vertex_configuration_frequencies
    ):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-interior-vertex-configuration-frequencies-mismatch",
                message=(
                    f"{spec.geometry} interior vertex configuration frequencies "
                    f"{observed_vertex_configuration_frequencies!r} did not match the reference expectation "
                    f"{periodic_descriptor.expected_interior_vertex_configuration_frequencies!r}."
                ),
            )
        )
    dual_candidate_failure = _periodic_face_dual_candidate_failure(
        geometry=spec.geometry,
        periodic_descriptor=periodic_descriptor,
        sample_cells=sample_cells,
        observed_vertex_configurations=observed_vertex_configurations,
        observed_vertex_configuration_frequencies=observed_vertex_configuration_frequencies,
    )
    if dual_candidate_failure is not None:
        failures.append(dual_candidate_failure)
    dual_failure = _periodic_face_dual_structure_failure(
        geometry=spec.geometry,
        periodic_descriptor=periodic_descriptor,
        sample_cells=sample_cells,
        observed_vertex_configurations=observed_vertex_configurations,
    )
    if dual_failure is not None:
        failures.append(dual_failure)
    failures.extend(_periodic_face_translation_failures(descriptor, sample_cells))
    return failures

