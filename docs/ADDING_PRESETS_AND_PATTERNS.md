# Adding Presets And Patterns

Use this guide when adding built-in seed presets, showcase/demo flows, or changing pattern import/export behavior. These changes are usually lower risk than adding rules or topologies, but they still touch persistence and browser workflows.

## Concepts

- A preset is an in-app seed generator tied to a rule or rule alias.
- A pattern is the portable JSON format exported from the app or imported back into it.
- Pattern payloads use sparse `cells_by_id` maps keyed by stable topology cell ids.

Presets should create useful starting states. Pattern import/export should preserve user state without depending on viewport position or canvas pixels.

## Files To Inspect

- [frontend/presets/registry.ts](../frontend/presets/registry.ts): combines preset registries and aliases.
- [frontend/presets/catalog-square.ts](../frontend/presets/catalog-square.ts): square-grid preset examples.
- [frontend/presets/catalog-hex.ts](../frontend/presets/catalog-hex.ts): hex-grid preset examples.
- [frontend/presets/core.ts](../frontend/presets/core.ts): shared preset helpers and types.
- [frontend/presets.ts](../frontend/presets.ts): public preset listing and seed construction.
- [frontend/pattern-io.ts](../frontend/pattern-io.ts): pattern payload serialization, import, export, filenames, and clipboard helpers.
- [frontend/parsers/pattern.ts](../frontend/parsers/pattern.ts): pattern validation.
- [frontend/actions/pattern-import-plan.ts](../frontend/actions/pattern-import-plan.ts) and [frontend/actions/pattern-import-runtime.ts](../frontend/actions/pattern-import-runtime.ts): import planning and execution.

## Add Or Update A Preset

1. Decide which rule owns the preset.
2. Add the preset to the matching catalog, or create a focused catalog if the existing split no longer fits.
3. Use stable topology cell ids when a preset targets specific cells.
4. Keep dimensions and topology assumptions explicit.
5. Add an alias in [frontend/presets/registry.ts](../frontend/presets/registry.ts) only when an existing rule id intentionally shares presets.
6. If the preset is meant as a first-run demo, update showcase controls or browser tests as needed.

## Small Preset Example

For square-grid binary rules, most small presets can use the shared ASCII helper:

```typescript
import { buildCenteredAsciiSeed } from "./core.js";
import type { PresetBuildContext, PresetRegistry } from "../types/presets.js";

const SQUARE_GEOMETRY = "square";

export const SQUARE_PRESET_REGISTRY: PresetRegistry = Object.freeze({
    conway: Object.freeze([
        // existing Conway presets...
        {
            id: "example-seed",
            label: "Example Seed",
            description: "A compact centered seed used as a documentation example.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 5,
            minHeight: 5,
            build: ({ width, height }: PresetBuildContext) => buildCenteredAsciiSeed(
                width,
                height,
                [
                    ".OO",
                    "OO.",
                    ".O.",
                ],
                { O: 1 },
            ),
        },
    ]),
});
```

For mixed or aperiodic topologies, avoid canvas coordinates. Use helpers that resolve against topology cells or write a focused helper that documents the topology assumption.

## Add Or Update Pattern Behavior

1. Keep `format`, `version`, `topology_spec`, `rule`, and `cells_by_id` behavior backward-aware.
2. Validate imported data at parser boundaries rather than spreading loose types through the app.
3. Preserve sparse export: omit zero-state cells from `cells_by_id`.
4. Validate imported cell ids against the reset topology before applying cell states.
5. Update versioned compatibility behavior deliberately if the payload shape changes.

## Small Pattern Example

Pattern payloads are sparse JSON. State `0` cells are omitted:

```json
{
  "format": "cellular-automaton-lab-pattern",
  "version": 5,
  "topology_spec": {
    "tiling_family": "square",
    "geometry_key": "square",
    "adjacency_mode": "edge",
    "sizing_mode": "grid",
    "width": 20,
    "height": 20,
    "patch_depth": 0
  },
  "rule": "conway",
  "cells_by_id": {
    "c:10:9": 1,
    "c:11:10": 1,
    "c:9:11": 1,
    "c:10:11": 1,
    "c:11:11": 1
  }
}
```

If this shape changes, update parser tests, import/export tests, share-link behavior, and any compatibility notes in the same change.

## Tests To Add Or Update

- Update [frontend/presets.test.ts](../frontend/presets.test.ts) for preset listing, aliases, and seed construction.
- Update [frontend/pattern-io.test.ts](../frontend/pattern-io.test.ts) and parser tests for payload shape, validation, filenames, import, and export behavior.
- Update [frontend/actions/pattern-import-runtime.test.ts](../frontend/actions/pattern-import-runtime.test.ts) when import sequencing or validation changes.
- Update [tests/e2e/playwright_case_suite.py](../tests/e2e/playwright_case_suite.py) for browser-visible import/export, clipboard, or showcase flows.

Useful commands:

```powershell
npm run test:frontend -- frontend/presets.test.ts frontend/pattern-io.test.ts frontend/actions/pattern-import-runtime.test.ts
py -3 -m unittest -q tests.e2e.test_playwright_pattern_and_showcase
```

## Common Pitfalls

- Do not encode presets in canvas coordinates; use topology cell ids or repo-owned preset helpers.
- Do not make pattern import depend on the current viewport or rendered canvas state.
- Do not loosen pattern parsing to accept arbitrary shapes without normalizing them at the parser boundary.
- Do not silently change the meaning of an existing pattern version.

## Checklist

- Preset ids and labels are stable and scoped to the owning rule or intentional alias.
- Preset builders use topology-aware cells or shared helpers, not viewport or canvas position.
- Pattern changes preserve sparse `cells_by_id` export and validate imports at parser boundaries.
- Version or compatibility behavior is documented when the payload shape changes.
- Frontend unit tests and browser tests cover the visible import/export or showcase flow when it changes.
