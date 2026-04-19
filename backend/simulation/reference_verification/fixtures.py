from __future__ import annotations

import json
from pathlib import Path

from backend.simulation.literature_reference_specs import ReferenceDepthExpectation
from backend.simulation.topology_types import LatticeCell, LatticeTopology

from .observation import _polygon_area
from .types import (
    _CanonicalPatchCellPayload,
    _CanonicalPatchFixturePayload,
    _LocalReferenceAnchorPayload,
    _LocalReferenceNeighborPayload,
    _LocalReferencePayload,
    ReferenceCheckFailure,
)

_LOCAL_REFERENCE_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "reference_patch_local_fixtures.json"
)
_CANONICAL_REFERENCE_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "reference_patch_canonical_fixtures.json"
)


def _load_local_reference_fixtures() -> dict[str, dict[str, dict[str, object]]]:
    return json.loads(_LOCAL_REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_canonical_reference_fixtures() -> dict[str, dict[str, _CanonicalPatchFixturePayload]]:
    return json.loads(_CANONICAL_REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _canonical_patch_payload(
    topology: LatticeTopology,
    *,
    include_id: bool,
) -> list[_CanonicalPatchCellPayload]:
    polygon_cells = [
        cell for cell in topology.cells if cell.vertices is not None and cell.center is not None
    ]
    if not polygon_cells:
        return []
    min_x = min(vertex[0] for cell in polygon_cells for vertex in cell.vertices or ())
    min_y = min(vertex[1] for cell in polygon_cells for vertex in cell.vertices or ())

    normalized: list[tuple[tuple[object, ...], _CanonicalPatchCellPayload]] = []
    for cell in polygon_cells:
        if cell.vertices is None or cell.center is None:
            continue
        decoration_tokens = (
            sorted(cell.decoration_tokens) if cell.decoration_tokens is not None else None
        )
        payload: _CanonicalPatchCellPayload = {
            "kind": cell.kind,
            "orientation_token": cell.orientation_token,
            "chirality_token": cell.chirality_token,
            "decoration_tokens": decoration_tokens,
            "center": [
                round(cell.center[0] - min_x, 6),
                round(cell.center[1] - min_y, 6),
            ],
            "vertices": [
                [round(vertex[0] - min_x, 6), round(vertex[1] - min_y, 6)]
                for vertex in cell.vertices
            ],
        }
        if include_id:
            payload["id"] = cell.id
        normalized.append(
            (
                (
                    payload["kind"],
                    payload["orientation_token"] or "",
                    payload["chirality_token"] or "",
                    tuple(payload["decoration_tokens"] or []),
                    tuple(payload["center"]),
                    tuple(tuple(vertex) for vertex in payload["vertices"]),
                    payload.get("id", ""),
                ),
                payload,
            )
        )
    return [payload for _, payload in sorted(normalized, key=lambda item: item[0])]


def _cell_local_reference_payload(
    topology: LatticeTopology,
    anchor_id: str,
) -> _LocalReferenceAnchorPayload | None:
    if not topology.has_cell(anchor_id):
        return None
    anchor = topology.get_cell(anchor_id)
    if anchor.vertices is None or anchor.center is None:
        return None
    cells_by_id = {cell.id: cell for cell in topology.cells}
    center_x, center_y = anchor.center

    def _payload(cell: LatticeCell) -> _LocalReferencePayload:
        vertices = cell.vertices
        if vertices is None:
            raise ValueError("Local reference payloads require polygon vertices.")
        return {
            "kind": cell.kind,
            "orientation_token": cell.orientation_token,
            "chirality_token": cell.chirality_token,
            "decoration_tokens": list(cell.decoration_tokens)
            if cell.decoration_tokens is not None
            else None,
            "area": round(_polygon_area(vertices), 6),
        }

    neighbors: list[_LocalReferenceNeighborPayload] = []
    for neighbor_id in sorted(
        neighbor_id for neighbor_id in anchor.neighbors if neighbor_id is not None
    ):
        neighbor = cells_by_id.get(neighbor_id)
        if neighbor is None or neighbor.vertices is None or neighbor.center is None:
            continue
        payload = _payload(neighbor)
        neighbors.append(
            {
                **payload,
                "delta": [
                    round(neighbor.center[0] - center_x, 6),
                    round(neighbor.center[1] - center_y, 6),
                ],
            }
        )

    ordered_neighbors = sorted(
        neighbors,
        key=lambda item: (
            item["kind"],
            item["orientation_token"] or "",
            item["chirality_token"] or "",
            tuple(item["decoration_tokens"] or []),
            item["delta"][0],
            item["delta"][1],
            item["area"],
        ),
    )
    return {
        "root": {
            **_payload(anchor),
            "degree": len(
                tuple(neighbor_id for neighbor_id in anchor.neighbors if neighbor_id is not None)
            ),
        },
        "neighbors": ordered_neighbors,
    }


def _local_reference_fixture_failures(
    geometry: str,
    depth: int,
    topology: LatticeTopology,
) -> list[ReferenceCheckFailure]:
    fixtures = _load_local_reference_fixtures()
    geometry_fixtures = fixtures.get(geometry, {})
    depth_fixtures = geometry_fixtures.get(str(depth))
    if not isinstance(depth_fixtures, dict):
        return []
    failures: list[ReferenceCheckFailure] = []
    for anchor_id, expected_payload in sorted(depth_fixtures.items()):
        observed_payload = _cell_local_reference_payload(topology, anchor_id)
        if observed_payload is None:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-local-reference-anchor",
                    message=(
                        f"Depth {depth} expected local reference anchor {anchor_id!r} "
                        f"for {geometry} but that cell was absent."
                    ),
                    depth=depth,
                )
            )
            continue
        if observed_payload != expected_payload:
            failures.append(
                ReferenceCheckFailure(
                    code="local-reference-fixture-mismatch",
                    message=(
                        f"Depth {depth} local reference payload for {geometry} anchor {anchor_id!r} "
                        "did not match the checked-in canonical fixture."
                    ),
                    depth=depth,
                )
            )
    return failures


def _canonical_patch_fixture_failures(
    geometry: str,
    depth: int,
    topology: LatticeTopology,
    expectation: ReferenceDepthExpectation,
) -> list[ReferenceCheckFailure]:
    fixture_key = expectation.canonical_patch_fixture_key
    if fixture_key is None:
        return []
    geometry_fixtures = _load_canonical_reference_fixtures().get(geometry, {})
    fixture = geometry_fixtures.get(fixture_key)
    if fixture is None:
        return [
            ReferenceCheckFailure(
                code="missing-canonical-patch-fixture",
                message=(
                    f"Depth {depth} expected canonical patch fixture {fixture_key!r} "
                    f"for {geometry} but none was checked in."
                ),
                depth=depth,
            )
        ]
    fixture_depth = int(fixture.get("depth", depth))
    if fixture_depth != depth:
        return [
            ReferenceCheckFailure(
                code="canonical-patch-fixture-depth-mismatch",
                message=(
                    f"Depth {depth} expected canonical patch fixture {fixture_key!r} "
                    f"for {geometry}, but the checked-in fixture declared depth {fixture_depth}."
                ),
                depth=depth,
            )
        ]
    expected_include_id = expectation.canonical_patch_include_id
    fixture_include_id = bool(fixture.get("include_id", False))
    if fixture_include_id != expected_include_id:
        return [
            ReferenceCheckFailure(
                code="canonical-patch-fixture-include-id-mismatch",
                message=(
                    f"Depth {depth} expected canonical patch fixture {fixture_key!r} "
                    f"for {geometry} to declare include_id={expected_include_id}, "
                    f"but the checked-in fixture declared include_id={fixture_include_id}."
                ),
                depth=depth,
            )
        ]
    observed_payload = _canonical_patch_payload(topology, include_id=expected_include_id)
    expected_payload = fixture.get("cells", [])
    if observed_payload != expected_payload:
        return [
            ReferenceCheckFailure(
                code="canonical-patch-fixture-mismatch",
                message=(
                    f"Depth {depth} canonical patch payload for {geometry} fixture "
                    f"{fixture_key!r} did not match the checked-in canonical serialization."
                ),
                depth=depth,
            )
        ]
    return []
