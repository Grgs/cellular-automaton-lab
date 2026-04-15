from __future__ import annotations

from importlib import import_module

from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
from backend.simulation.literature_reference_specs import (
    REFERENCE_FAMILY_SPECS,
    STAGED_REFERENCE_WAIVERS,
    BuilderSignalExpectation,
    ReferenceFamilySpec,
)

from .depth import _depth_topology_expectation_failures, _metadata_failures
from .observation import _build_reference_topology, observe_reference_patch
from .periodic import _periodic_face_descriptor_failures
from .types import ReferenceCheckFailure, ReferenceVerificationResult, VerificationStatus


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
    from backend.simulation.aperiodic_support import AperiodicPatch
    from backend.simulation.aperiodic_pinwheel import collect_pinwheel_exact_records

    def _bounds_longest_span(patch: AperiodicPatch) -> float:
        vertices = [vertex for cell in patch.cells for vertex in (cell.vertices or ())]
        if not vertices:
            return 0.0
        min_x = min(vertex[0] for vertex in vertices)
        max_x = max(vertex[0] for vertex in vertices)
        min_y = min(vertex[1] for vertex in vertices)
        max_y = max(vertex[1] for vertex in vertices)
        return max(max_x - min_x, max_y - min_y)

    failures: list[ReferenceCheckFailure] = []
    previous_bounds_longest_span: float | None = None
    for depth in range(4):
        patch = build_aperiodic_patch("pinwheel", depth)
        exact_records = collect_pinwheel_exact_records(depth)
        expected_exact_count = 2 * (5**depth)
        if len(exact_records) != expected_exact_count:
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-growth-mismatch",
                    message=(
                        f"Depth {depth} exact record count {len(exact_records)} "
                        f"did not match literature growth 2*5^{depth}={expected_exact_count}."
                    ),
                    depth=depth,
                )
            )
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
        if any(
            not (
                record_id.startswith("pinwheel:root0")
                or record_id.startswith("pinwheel:root1")
            )
            for record_id in exact_ids
        ):
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-root-mismatch",
                    message=(
                        f"Depth {depth} exact-record ids were not rooted exclusively "
                        "under pinwheel:root0 or pinwheel:root1."
                    ),
                    depth=depth,
                )
            )
        observed_roots = {
            record_id.split(".", 1)[0].removeprefix("pinwheel:")
            for record_id in exact_ids
        }
        if observed_roots != {"root0", "root1"}:
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-root-coverage-mismatch",
                    message=(
                        f"Depth {depth} exact-record roots {sorted(observed_roots)!r} "
                        "did not match ['root0', 'root1']."
                    ),
                    depth=depth,
                )
            )
        bounds_longest_span = _bounds_longest_span(patch)
        if (
            previous_bounds_longest_span is not None
            and bounds_longest_span <= previous_bounds_longest_span
        ):
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-support-nonexpanding",
                    message=(
                        f"Depth {depth} support span {bounds_longest_span:.6f} did not grow "
                        f"beyond the previous depth span {previous_bounds_longest_span:.6f}."
                    ),
                    depth=depth,
                )
            )
        previous_bounds_longest_span = bounds_longest_span
    return failures


def _verify_spec(spec: ReferenceFamilySpec) -> ReferenceVerificationResult:
    observations = tuple(
        observe_reference_patch(spec.geometry, depth)
        for depth in sorted(spec.depth_expectations)
    )
    failures: list[ReferenceCheckFailure] = []
    deepest_topology = _build_reference_topology(spec, max(spec.depth_expectations, default=0))
    observed_kinds = {cell.kind for cell in deepest_topology.cells}
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
        failures.extend(_metadata_failures(deepest_topology, requirement))
    failures.extend(_periodic_face_descriptor_failures(spec))
    failures.extend(_builder_signal_failures(spec.builder_signals))
    if spec.exact_reference_mode == "pinwheel_exact":
        failures.extend(_pinwheel_exact_path_failures())
    for observation in observations:
        expectation = spec.depth_expectations[observation.depth]
        depth_topology = _build_reference_topology(spec, observation.depth)
        failures.extend(
            _depth_topology_expectation_failures(
                geometry=spec.geometry,
                depth=observation.depth,
                topology=depth_topology,
                expectation=expectation,
                observation=observation,
            )
        )

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
