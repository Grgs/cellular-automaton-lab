# Adding Topologies

Use this guide when adding a new tiling family, adjacency mode, or topology generator. Topology changes are higher risk than rule changes because they affect simulation state, persistence, rendering, tests, and the standalone bootstrap payload.

For system context, start with [ARCHITECTURE.md](ARCHITECTURE.md), [CODE_MAP.md](CODE_MAP.md), and [TESTING_TILINGS.md](TESTING_TILINGS.md).

## Decide The Topology Type

Choose the smallest existing model that fits the family:

- `regular_grid`: square, hex, and triangle-style coordinate grids.
- `periodic_face`: repeated mixed tiling descriptors with polygon faces.
- `substitution_patch`: finite aperiodic or patch-depth-driven families.

If the family is approximate, finite-sample-only, visually provisional, or intentionally not literature-canonical, document that in [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).

## Files To Inspect

- [backend/simulation/topology_family_manifest.py](../backend/simulation/topology_family_manifest.py): family ids, picker metadata, default rules, sizing policy, and variants.
- [backend/simulation/topology_catalog_data.py](../backend/simulation/topology_catalog_data.py): catalog projections and exported constants consumed by runtime code.
- [backend/simulation/topology_implementation_registry.py](../backend/simulation/topology_implementation_registry.py): builder kind and render kind dispatch.
- [backend/simulation/topology_regular.py](../backend/simulation/topology_regular.py): regular grid cell builders.
- [backend/simulation/periodic_face_tilings.py](../backend/simulation/periodic_face_tilings.py): periodic mixed-tiling descriptors.
- [backend/simulation/aperiodic_registry.py](../backend/simulation/aperiodic_registry.py): aperiodic family dispatch.
- [backend/simulation/aperiodic_support.py](../backend/simulation/aperiodic_support.py): shared affine, polygon, and patch helpers.
- [frontend/geometry/registry.ts](../frontend/geometry/registry.ts): render adapter lookup by `render_kind`.
- [frontend/geometry/periodic-mixed-adapter.ts](../frontend/geometry/periodic-mixed-adapter.ts) and [frontend/geometry/aperiodic-prototile-adapter.ts](../frontend/geometry/aperiodic-prototile-adapter.ts): main polygon render paths.

## Add A Topology

1. Add or choose the family id.
   - Keep ids stable, lowercase, and kebab-case.
   - Treat ids as persistence and pattern-file surface once released.
2. Add catalog metadata in [backend/simulation/topology_family_manifest.py](../backend/simulation/topology_family_manifest.py).
   - Set display labels, adjacency modes, default rule, sizing mode, and patch-depth behavior.
   - Use existing variants as templates.
3. Wire the implementation in [backend/simulation/topology_implementation_registry.py](../backend/simulation/topology_implementation_registry.py).
   - Pick `builder_kind`.
   - Pick `render_kind`.
   - Add the geometry to the matching implementation group or provide a focused builder wrapper.
4. Implement the backend builder.
   - Regular grids belong near [backend/simulation/topology_regular.py](../backend/simulation/topology_regular.py).
   - Periodic mixed tilings usually need descriptor data in [backend/simulation/periodic_face_tilings.py](../backend/simulation/periodic_face_tilings.py).
   - Aperiodic families usually get a focused `backend/simulation/aperiodic_*.py` module plus registry wiring.
5. Preserve topology contracts.
   - Cell ids must be deterministic and stable for the same topology spec.
   - Neighbor ids must refer to existing cells.
   - Cell geometry should be overlap-free unless a documented exception exists.
   - Patch-depth families should have explicit caps and sizing behavior.
6. Confirm frontend rendering.
   - Reuse an existing `render_kind` when possible.
   - Add a new geometry adapter only when the existing regular, periodic polygon, or aperiodic polygon adapters cannot represent the family.
7. Add reference, invariant, and known-deviation documentation as needed.

## Small Example

For a periodic mixed tiling that can use the existing polygon renderer, the change usually has three pieces: catalog metadata, implementation registry wiring, and descriptor data. This example is shortened to show the shape:

```python
# backend/simulation/topology_family_manifest.py
EXAMPLE_MIXED_GEOMETRY = "example-mixed"

TOPOLOGY_FAMILY_MANIFEST: dict[str, TopologyFamilyManifestEntry] = {
    # existing entries...
    EXAMPLE_MIXED_GEOMETRY: _single_variant_family(
        tiling_family=EXAMPLE_MIXED_GEOMETRY,
        label="Example Mixed",
        picker_group="Experimental",
        picker_order=410,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 24),
        default_rule="conway",
        minimum_grid_dimension=1,
    ),
}
```

```python
# backend/simulation/topology_implementation_registry.py
from backend.simulation.topology_catalog_data import EXAMPLE_MIXED_GEOMETRY

_PERIODIC_FACE_GEOMETRIES = (
    # existing geometries...
    EXAMPLE_MIXED_GEOMETRY,
)
```

Also export the new constant through [backend/simulation/topology_catalog_data.py](../backend/simulation/topology_catalog_data.py) if runtime modules need to import it from the catalog surface. The actual descriptor belongs with the existing periodic descriptors, and should include enough geometry for deterministic cell ids, neighbors, and polygon rendering. If a topology cannot be represented by an existing builder kind and `render_kind`, add the smallest new builder or adapter path that preserves the same payload contracts.

## Tests To Add Or Update

- Add or update topology unit tests in [tests/unit](../tests/unit), especially `test_topology_validation.py`, `test_topology_implementation_registry.py`, and family-contract tests.
- Update [tests/api/test_api_state_and_rules.py](../tests/api/test_api_state_and_rules.py) when reset behavior, default rules, patch-depth caps, or serialized topology payloads change.
- Update frontend catalog, geometry, render-bounds, and overlap tests when render metadata or adapters change.
- Add Playwright coverage for picker/reset/persistence behavior if the family is user-visible.
- Add or update reference verifier coverage when the family has source-backed invariants.
- Add known-deviation docs when the implementation is intentionally weaker than the strongest target model.

Useful commands:

```powershell
py -3 tools\validate_tilings.py
py -3 tools\verify_reference_tilings.py
npm run fixtures:reference:check
npm run test:frontend -- frontend/geometry/polygon-overlap.test.ts frontend/geometry/render-bounds.test.ts
py -3 -m unittest -q tests.unit.test_topology_validation
py -3 -m unittest -q tests.api.test_api_state_and_rules
npm run test:e2e:playwright:server
```

## Common Pitfalls

- Do not add catalog metadata without a builder and render path.
- Do not add a backend builder that emits unstable cell ids; sparse persistence and pattern import depend on ids.
- Do not silently accept mathematical shortcuts. If a family is finite-sample, approximate, or decorated rather than canonical, document that boundary.
- Do not refresh generated fixtures by hand. Use the repo-owned regeneration tools and review the resulting diff.

## Checklist

- Topology id is stable, lowercase, and treated as persisted data once released.
- Catalog metadata, implementation registry wiring, backend builder, and frontend render path agree on the same `geometry_key` and `render_kind`.
- Generated cells have deterministic ids, valid neighbor ids, and documented adjacency behavior.
- Patch-depth or sizing limits are explicit and covered by tests.
- Reference docs, known deviations, and fixtures are updated through repo-owned tools when they apply.
