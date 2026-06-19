# Adding Topologies

Use this guide when adding a new tiling family, adjacency mode, or topology generator. Topology changes are higher risk than rule changes because they affect simulation state, persistence, rendering, tests, and the standalone bootstrap payload.

For system context, start with [ARCHITECTURE.md](ARCHITECTURE.md), [CODE_MAP.md](CODE_MAP.md), and [TESTING_TILINGS.md](TESTING_TILINGS.md).

## Fast path: aperiodic substitution families

If the new family is an aperiodic substitution tiling (the most common case for new entries), `python -m tools tilings scaffold-aperiodic` automates the mechanical wiring. It creates the generator skeleton, reference-spec stub, and test skeleton, and inserts the manifest / registry / topology / reference-spec-init entries. The placeholder substitution is structurally valid (loads end-to-end) so you can confirm wiring before implementing the real geometry.

```powershell
python -m tools tilings scaffold-aperiodic \
    --family-id widget-monotile \
    --label "Widget Monotile" \
    --kind widget \
    --source-url https://tilings.math.uni-bielefeld.de/substitution/widget/
```

After scaffolding, follow the printed checklist:

1. Implement the real substitution geometry in the generated `backend/simulation/aperiodic_<family>.py`.
2. Fill in the depth expectations in the generated `backend/simulation/reference_specs/aperiodic/<family>.py`.
3. Add a dead-palette entry under `frontend/canvas/family-dead-palette-manifest.json`.
4. Regenerate the picker thumbnail, canonical fixtures, frontend topology fixtures, and bootstrap data using the tool invocations printed by the scaffold.

The rest of this document is the manual reference. Use it when the scaffold doesn't fit (regular grid, periodic-face, or non-substitution aperiodic families) or when you need to understand what the scaffold is doing.

## Decide The Topology Type

Choose the smallest existing model that fits the family:

- `regular_grid`: square, hex, and triangle-style coordinate grids.
- `periodic_face`: repeated mixed tiling descriptors with polygon faces.
- `substitution_patch`: finite aperiodic or patch-depth-driven families.

If the family is approximate, finite-sample-only, visually provisional, or intentionally not literature-canonical, document that in [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).

## Files To Inspect

- [backend/simulation/topology_family_manifest.py](../backend/simulation/topology_family_manifest.py): family ids, picker metadata, default rules, sizing policy, and variants.
- [backend/simulation/topology_catalog_data.py](../backend/simulation/topology_catalog_data.py): catalog projections and exported constants consumed by runtime code.
- [backend/simulation/topology_catalog.py](../backend/simulation/topology_catalog.py): public re-export surface; add any new geometry constant to both `__all__` and the import list here.
- [backend/simulation/topology_implementation_registry.py](../backend/simulation/topology_implementation_registry.py): builder kind and render kind dispatch.
- [backend/simulation/topology_regular.py](../backend/simulation/topology_regular.py): regular grid cell builders.
- [backend/simulation/periodic_face_tilings.py](../backend/simulation/periodic_face_tilings.py): registers which geometry keys are handled by the periodic face builder.
- [backend/simulation/data/periodic_face_patterns/](../backend/simulation/data/periodic_face_patterns/): one geometry-only face template descriptor per `periodic_face` tiling, named `<geometry-key>.json`. Its catalog label comes from `topology_family_manifest.py`.
- [backend/simulation/aperiodic_registry.py](../backend/simulation/aperiodic_registry.py): aperiodic family dispatch.
- [backend/simulation/aperiodic_support/](../backend/simulation/aperiodic_support/): shared affine, polygon, and patch helpers (split across `affine.py`, `geometry.py`, `neighbors.py`, `patches.py`, and `types.py`).
- [backend/simulation/reference_specs/](../backend/simulation/reference_specs/): reference family specs split by family class (`regular.py`, `periodic.py`, `aperiodic.py`). Add a `ReferenceFamilySpec` entry here for any tiling with a literature-verifiable cell count, degree histogram, or adjacency signature.
- [frontend/controls/tiling-preview-data.ts](../frontend/controls/tiling-preview-data.ts): pre-computed polygon thumbnail data for the tiling picker. Without an entry here the tiling falls back to a generic square preview.
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
   - Periodic mixed tilings: add [backend/simulation/data/periodic_face_patterns/<geometry-key>.json](../backend/simulation/data/periodic_face_patterns/) with the face template vertices, unit cell dimensions (`unit_width`, `unit_height`), renderer `min_dimension`, slot vocabulary, and bounding extents. The filename must match the descriptor's `geometry` value. Do not repeat `label`; it comes from `TOPOLOGY_FAMILY_MANIFEST`. Then add the geometry key to `PERIODIC_FACE_TILING_GEOMETRIES` in [backend/simulation/periodic_face_tilings.py](../backend/simulation/periodic_face_tilings.py).
   - Before hand-editing the JSON descriptor, **sketch the candidate faces in a Python file and run them through [tools/sketch_tiling.py](../tools/sketch_tiling.py)** to catch overlaps, T-junctions, unmatched edges, and per-vertex angle-sum mistakes before any of the manifest/registry wiring is in place. Pass `--json backend/simulation/data/periodic_face_patterns/<geometry-key>.json` to write the descriptor directly to its final location. See the example under [tools/sketch_examples/](../tools/sketch_examples/) for the input format.
   - Aperiodic families usually get a focused `backend/simulation/aperiodic_*.py` module plus registry wiring.
5. Preserve topology contracts.
   - Cell ids must be deterministic and stable for the same topology spec.
   - Neighbor ids must refer to existing cells.
   - Cell geometry should be overlap-free unless a documented exception exists.
   - Patch-depth families should have explicit caps and sizing behavior.
6. Confirm frontend rendering.
   - Reuse an existing `render_kind` when possible.
   - Add a new geometry adapter only when the existing regular, periodic polygon, or aperiodic polygon adapters cannot represent the family.
7. Add a picker thumbnail.
   - Run `python -m tools tilings preview --geometry <key>` to generate a ready-to-paste entry for [frontend/controls/tiling-preview-data.ts](../frontend/controls/tiling-preview-data.ts). The tool centers the viewbox on the highest-degree vertex, tiles enough unit cells to fill the `0 0 120 72` viewbox, and auto-detects the number of fill indices from the face kinds.
   - Paste the output after the entry for the topologically nearest tiling (same family class, similar picker order).
   - Fill indices 0–3 map to the four picker swatch colors; use `--fill-count 1` to override the auto-detection for tilings where a single color is preferred regardless of face kind count.
   - Without this entry the picker shows a generic square fallback.
8. Add reference, invariant, and known-deviation documentation as needed.
   - Add a `ReferenceFamilySpec` to the appropriate file under [backend/simulation/reference_specs/](../backend/simulation/reference_specs/) (`regular.py`, `periodic.py`, or `aperiodic.py`). Include cell counts, degree histograms, adjacency pairs, and an SHA-prefix signature derived from `verify_reference_tilings.py`.
   - If the tiling is the dual of an existing one, add `expected_dual_geometry` to both the primal and dual `PeriodicDescriptorExpectation` entries to keep the duality relationship machine-checked.

## Automatic Coverage

Registering a topology opts it into the checks below. Do not create a per-tiling copy of these tests. Add focused tests only for behavior or mathematical invariants unique to the new family.

| Inherited check | Coverage | Command or test |
| --- | --- | --- |
| Descriptor and registry synchronization | Every periodic descriptor has one registered geometry and no orphaned file | `tests/unit/test_periodic_face_tilings.py` |
| Implementation dispatch | Every supported geometry resolves without the square fallback | `tests/unit/test_topology_implementation_registry.py` |
| Geometry and graph validity | Every mixed and aperiodic catalog geometry is checked for topology structure, adjacency, holes, and edge multiplicity | `python -m tools tilings validate` |
| Grid-size variation | Periodic geometries are sampled across widths and heights from 1 through 3 | `tests/unit/test_hypothesis_topology_properties.py` |
| Reference coverage | Every catalog geometry requires a reference spec and passes its declared signatures and invariants | `python -m tools tilings verify` |
| Picker preview coverage | Every non-regular picker entry has a thumbnail and no orphaned thumbnail remains | `tests/unit/test_tiling_preview_coverage.py` |
| Frontend catalog and adapter dispatch | Every bootstrapped topology appears in picker options and resolves its default geometry adapter | `frontend/topology-catalog-bootstrap.test.ts` |
| Bootstrap freshness | Generated frontend and standalone metadata remains derived from backend manifests | `python -m tools repo generated-check` |

The periodic scaffold should wire a geometry into these catalog-driven surfaces and generate only tiling-specific artifacts, such as its descriptor and reference expectations. It should not generate generic test files.

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

Also export the new constant through [backend/simulation/topology_catalog_data.py](../backend/simulation/topology_catalog_data.py) and [backend/simulation/topology_catalog.py](../backend/simulation/topology_catalog.py) (both `__all__` and the import list) if runtime modules need to import it from the catalog surface.

The actual face template descriptor belongs in its own file under [backend/simulation/data/periodic_face_patterns/](../backend/simulation/data/periodic_face_patterns/) — not in `periodic_face_tilings.py`. That module only lists which geometry keys are dispatched through the periodic face builder. The JSON descriptor should include enough geometry (vertex coordinates, `unit_width`, `unit_height`, slot vocabulary) for deterministic cell ids, neighbors, and polygon rendering.

If a topology cannot be represented by an existing builder kind and `render_kind`, add the smallest new builder or adapter path that preserves the same payload contracts.

## Tests To Add Or Update

- Add or update topology unit tests in [tests/unit](../tests/unit), especially `test_topology_validation.py`, `test_topology_implementation_registry.py`, and family-contract tests.
- Update [tests/api/test_api_state_and_rules.py](../tests/api/test_api_state_and_rules.py) when reset behavior, default rules, patch-depth caps, or serialized topology payloads change.
- Update frontend catalog, geometry, render-bounds, and overlap tests when render metadata or adapters change.
- Add Playwright coverage for picker/reset/persistence behavior if the family is user-visible.
- Add or update reference verifier coverage when the family has source-backed invariants.
- Add known-deviation docs when the implementation is intentionally weaker than the strongest target model.

Useful commands:

```powershell
# Generate a picker thumbnail for a new periodic face tiling
python -m tools tilings preview --geometry <key>
python -m tools tilings preview --list

python -m tools tilings validate
python -m tools tilings verify
npm run fixtures:reference:check
npm run test:frontend -- frontend/geometry/polygon-overlap.test.ts frontend/geometry/render-bounds.test.ts
py -3 -m unittest -q tests.unit.test_topology_validation
py -3 -m unittest -q tests.unit.test_periodic_face_tilings
py -3 -m unittest -q tests.unit.test_tiling_preview_coverage
py -3 -m unittest -q tests.api.test_api_state_and_rules
npm run test:e2e:playwright:server
```

## Periodic Face Tilings With Skewed Or Non-Edge-To-Edge Lattices

The descriptor's lattice is `(unit_width, 0)` along x and a second basis vector along y. Two ways to express the second basis:

- **`row_offset_x`** (default semantic) - only odd rows shift by `row_offset_x`. The lattice is a 2-row brick stack. Used by `cairo-pentagonal`, `trihexagonal-3-6-3-6`, and any tiling where `row_offset_x == unit_width / 2` (so the cumulative shift modulo `unit_width` is zero after 2 rows).

- **`lattice_skew_x`** (set to opt in) - every row shifts cumulatively by `k * lattice_skew_x`. The lattice is a genuine skewed parallelogram. Used by `stein-14-pentagonal`. Mutually exclusive with `row_offset_x` at descriptor level (set one or the other; never both).

When choosing the rotation: orient the tiling so one basis vector becomes horizontal (`(unit_width, 0)`). The other vector becomes `(lattice_skew_x, unit_height)`. The sign of `lattice_skew_x` follows the direction of the rotated vector (negative means rows shift leftward as y grows). The unit cell's vertices DO NOT need to fit inside a rectangle - they form a parallelogram, and `min_x`/`max_x` should describe the actual tile extent (which may exceed `unit_width`).

**Non-edge-to-edge tilings** (T-junctions where one tile's vertex sits on the midpoint of another tile's edge): the periodic-face neighbor builder detects T-junction adjacency automatically since the post-Stein-14 fix. No descriptor flag is needed for that. But if the tiling combines T-junctions with **irrational coordinates** (Stein-14, Stein-15, some Reinhardt/Rice pentagons), the topology validator's strict `1e-7` overlap tolerance can flag spurious overlaps from float-precision drift between the stored vertex and the geometric midpoint. Add the geometry id to `_NON_EDGE_TO_EDGE_IRRATIONAL_GEOMETRIES` in `backend/simulation/topology_validation.py` to opt into a looser `1e-3` tolerance, and note the looser tolerance in `docs/TILING_KNOWN_DEVIATIONS.md`.

## Common Pitfalls

- Do not add catalog metadata without a builder and render path.
- Do not add a backend builder that emits unstable cell ids; sparse persistence and pattern import depend on ids.
- Do not silently accept mathematical shortcuts. If a family is finite-sample, approximate, or decorated rather than canonical, document that boundary.
- Do not refresh generated fixtures by hand. Use the repo-owned regeneration tools and review the resulting diff.
- Do not forget the picker thumbnail. Without an entry in `tiling-preview-data.ts` the tiling silently falls back to a generic square preview in the picker menu.
- For periodic face tilings, the face template data belongs in `periodic_face_patterns/<geometry-key>.json`, not in `periodic_face_tilings.py`. Adding only the geometry key to `PERIODIC_FACE_TILING_GEOMETRIES` without a descriptor file will produce an empty or broken topology at runtime.
- Do not set both `row_offset_x` and `lattice_skew_x` in the same descriptor; they describe mutually exclusive lattice semantics. See the "Periodic Face Tilings With Skewed Or Non-Edge-To-Edge Lattices" section above.
- For Laves (dual) tilings, cross-link the primal tiling's reference spec with `expected_dual_geometry` so the duality relationship is verified automatically.
- Python files must pass `ruff format` or the pre-commit hook will reject the commit. Run `py -3 -m ruff format <file>` before staging if you write or generate Python with non-standard formatting.

## Checklist

- Topology id is stable, lowercase, and treated as persisted data once released.
- Catalog metadata, implementation registry wiring, backend builder, and frontend render path agree on the same `geometry_key` and `render_kind`.
- New geometry constant is exported from both `topology_catalog_data.py` and `topology_catalog.py`.
- Generated cells have deterministic ids, valid neighbor ids, and documented adjacency behavior.
- Patch-depth or sizing limits are explicit and covered by tests.
- Picker thumbnail entry added to `tiling-preview-data.ts` and verified visually.
- Reference spec added to `backend/simulation/reference_specs/` with cell counts, degree histogram, and signature.
- Dual relationship cross-linked via `expected_dual_geometry` if applicable.
- Reference docs, known deviations, and fixtures are updated through repo-owned tools when they apply.
