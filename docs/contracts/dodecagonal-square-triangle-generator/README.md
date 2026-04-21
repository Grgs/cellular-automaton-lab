# Dodecagonal Square-Triangle Generator Contract

This directory is a standalone implementation contract for the `dodecagonal-square-triangle`
patch generator. It is intentionally stripped of host-application concerns. Another model
should be able to recreate the generator from this directory alone.

## Goal

Implement a function with this behavior:

```python
def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    ...
```

The function returns a finite public square-triangle patch for the
`dodecagonal-square-triangle` family.

This contract preserves:

- the callable interface
- the output schema
- the patch-depth semantics
- the exact metadata vocabulary
- the exact neighbor construction rule
- the observable outputs for patch depths `0` through `4`

This contract does **not** require any knowledge of the surrounding application.

## Included Files

- `README.md`: this contract
- `contract.json`: machine-readable summary of thresholds, vocabularies, and exact depth-level counts
- `reference-patch.json`: authoritative full reference dataset
- `expected-patches/patch-depth-0.json`
- `expected-patches/patch-depth-1.json`
- `expected-patches/patch-depth-2.json`
- `expected-patches/patch-depth-3.json`
- `expected-patches/patch-depth-4.json`

If you implement against this bundle, the `expected-patches` files are the authoritative
acceptance oracles.

## External Source Provenance

The included `reference-patch.json` is the authoritative input dataset for this contract.
It is a validated public patch sample derived from the square-triangle literature source:

- [Square-triangle](https://tilings.math.uni-bielefeld.de/substitution/square-triangle/)

You do not need to re-derive the dataset from the literature source if you have this bundle.
If you choose to re-derive it anyway, your produced `reference-patch.json` and generated
patches must match the included artifacts exactly.

## Required Output Types

The generator must produce this logical shape:

```python
class PatchCell(TypedDict):
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[str, ...]
    tile_family: str | None
    orientation_token: str | None
    chirality_token: str | None
    decoration_tokens: tuple[str, ...] | None


class AperiodicPatch(TypedDict):
    patch_depth: int
    width: int
    height: int
    cells: tuple[PatchCell, ...]
```

The concrete implementation language does not matter as long as the observable data is
equivalent.

## Public Vocabulary

### Family identifier

- `tile_family = "dodecagonal-square-triangle"`

### Public cell kinds

- `dodecagonal-square-triangle-square`
- `dodecagonal-square-triangle-triangle`

### Orientation tokens

Orientation tokens are strings, not integers. The allowed vocabulary is:

- `"0"`
- `"30"`
- `"60"`
- `"90"`
- `"120"`
- `"150"`
- `"180"`
- `"210"`
- `"240"`
- `"270"`
- `"300"`
- `"330"`

### Chirality tokens

For triangles only:

- `"red"`
- `"yellow"`
- `"blue"`

For squares:

- `chirality_token = null`

### Decoration tokens

For this family, `decoration_tokens` is always `null` in the included artifacts.

## Reference Dataset Schema

`reference-patch.json` contains:

```json
{
  "unit_scale": 24.5,
  "seed_id": "sqtri:ref:05016",
  "snap_epsilon": 0.0025,
  "selection_policy": "deterministic hole-free greedy subset ordered by (graph_distance, id)",
  "records": [
    {
      "id": "sqtri:ref:05016",
      "kind": "dodecagonal-square-triangle-square",
      "center": [0.789106, 0.788325],
      "vertices": [[1.000932, -0.001858], [1.579341, 1.00006], [0.5773, 1.578509], [-0.001148, 0.57659]],
      "tile_family": "dodecagonal-square-triangle",
      "orientation_token": "60",
      "chirality_token": null,
      "variant": "square-white",
      "graph_distance": 0
    }
  ]
}
```

Only these record fields are required to build the runtime patch:

- `id`
- `kind`
- `center`
- `vertices`
- `tile_family`
- `orientation_token`
- `chirality_token`
- `graph_distance`

The `variant`, `unit_scale`, `seed_id`, `snap_epsilon`, and `selection_policy` fields are
descriptive metadata. They do not affect runtime patch construction.

## Generator Algorithm

Implement exactly this behavior:

1. Resolve the requested depth as:
   - `resolved_depth = max(0, int(patch_depth))`
2. Use this graph-distance threshold table:

```python
PATCH_DISTANCE_THRESHOLDS = {
    0: 4,
    1: 16,
    2: 40,
    3: 76,
    4: 97,
}
```

3. Convert `resolved_depth` to a record-selection threshold:
   - if `resolved_depth` is in the table, use the matching threshold
   - if `resolved_depth` is less than the smallest key, use the smallest-key threshold
   - if `resolved_depth` is greater than the largest key, use the largest-key threshold
4. Load all records from `reference-patch.json`.
5. Keep only records with `graph_distance <= selected_threshold`.
6. For each retained record, carry these fields through unchanged into a runtime patch record:
   - `id`
   - `kind`
   - `center`
   - `vertices`
   - `tile_family`
   - `orientation_token`
   - `chirality_token`
   - `decoration_tokens = null`
7. Build neighbors by exact full-edge matching after rounding coordinates to 6 decimal places.
8. Sort cells lexicographically by `id`.
9. Sort each cell’s `neighbors` lexicographically by neighbor id.
10. Compute:
    - `width = max(1, ceil(max_x - min_x))`
    - `height = max(1, ceil(max_y - min_y))`
    where `max_x`, `min_x`, `max_y`, `min_y` are taken over all cell vertices in the
    selected patch.
11. Return:
    - `patch_depth = resolved_depth`
    - `width`
    - `height`
    - `cells`

## Neighbor Construction Rule

Neighboring is defined by shared full polygon edges only.

Canonicalize an edge like this:

1. Round both endpoints to 6 decimal places.
2. Sort the two rounded endpoints lexicographically.
3. Use the resulting ordered endpoint pair as the edge key.

Cells `A` and `B` are neighbors if and only if there exists an edge key owned by exactly
those two cell ids.

Important consequences:

- partial overlap is **not** enough
- touching at a point is **not** enough
- near-equal edges must be normalized by 6-decimal rounding first

## Non-Negotiable Invariants

The generated patch must satisfy all of these:

- all cells have `tile_family == "dodecagonal-square-triangle"`
- all cell kinds are in the two-kind public vocabulary
- all triangle cells have non-null `chirality_token`
- all square cells have null `chirality_token`
- all cells have non-null `orientation_token`
- cells are sorted by `id`
- neighbors are sorted by `id`
- the selected patch is connected
- the selected patch is hole-free
- the selected patch is overlap-free
- no records are excluded beyond the graph-distance threshold rule
- centers are copied from the dataset; do not recompute them from vertices

## Exact Depth-Level Expectations

These are the required depth-level outputs:

| Depth | Threshold | Width | Height | Cells | Squares | Triangles |
|---|---:|---:|---:|---:|---:|---:|
| `0` | `4` | `8` | `6` | `20` | `6` | `14` |
| `1` | `16` | `18` | `17` | `132` | `37` | `95` |
| `2` | `40` | `24` | `31` | `259` | `75` | `184` |
| `3` | `76` | `40` | `32` | `462` | `140` | `322` |
| `4` | `97` | `52` | `32` | `565` | `174` | `391` |

For exact orientation, chirality, and degree expectations, use `contract.json`.

## Acceptance Rule

The implementation is correct if:

1. For patch depths `0` through `4`, it produces semantic JSON equality with the matching
   files under `expected-patches/`.
2. For any requested depth `>= 5`, it produces the same cells, width, and height as
   `patch-depth-4.json`, while still returning `patch_depth = max(0, int(requested_depth))`.
3. For any requested negative depth, it behaves like depth `0`.

## Irrelevant Context To Ignore

Do not include or depend on:

- UI behavior
- HTTP routes
- frontend bootstrap data
- browser review tooling
- host application controller types
- simulation rules
- persistence formats outside this directory

This contract is only about generating the finite dodecagonal square-triangle patch data.
