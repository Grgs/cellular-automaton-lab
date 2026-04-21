# Dodecagonal Square-Triangle Generator Bundle

This directory contains a standalone literature-derived generator for the public
`dodecagonal-square-triangle` family plus the source assets it depends on.

The generator is intentionally narrow and self-contained. It preserves only the
public patch interface the application consumes and excludes unrelated host-app
details such as routing, frontend wiring, persistence, and review tooling.

## Files

- `generator.py`
  - standalone Python implementation
  - parses the Bielefeld vector patch PDF
  - snaps near-identical PDF vertices into a shared point set
  - rebuilds shared-edge adjacency from the snapped polygons
  - emits deterministic public square/triangle patches for depths `0..7`
- `test_generator.py`
  - focused standalone validation for connectivity, hole-freedom, overlap-free
    area, metadata presence, and reciprocal neighbors
- `bielefeld-patch.pdf`
  - primary vector source used by the generator
- `reference-patch.json`
  - baseline artifact for comparison against the older cleaned-patch approach

## Public Interface

The standalone generator exposes:

```python
def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    ...
```

with a return shape equivalent to:

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

## Public Vocabulary

- `tile_family = "dodecagonal-square-triangle"`
- `dodecagonal-square-triangle-square`
- `dodecagonal-square-triangle-triangle`

Square cells keep `chirality_token = None`. Triangle cells collapse to the
public triangle kind while preserving color-derived chirality tokens:
`"red"`, `"yellow"`, and `"blue"`.

## Core Reconstruction Rule

The generator does not use the older checked-in connected subset as its source
of truth. Instead it:

1. parses filled polygons from `bielefeld-patch.pdf`
2. classifies squares by vertex count and triangles by literature fill color
3. snaps near-identical PDF vertices within a fixed tolerance so theoretically
   shared points become exactly shared
4. rebuilds adjacency from snapped full-edge matches
5. grows the finite patch by graph distance from a fixed square seed cell
6. normalizes the resulting patch around the seed cell and emits deterministic
   public metadata

This keeps the implementation tied to the literature vector source while
avoiding the tiny coordinate drift that made the raw PDF extraction overlap at
deeper depths.

## Invariants

The emitted patch must remain:

- deterministic for the same `patch_depth`
- one connected component
- hole-free
- overlap-free
- full-edge adjacent rather than point-touching
- stable in ids and cell ordering

## Local Verification

Run the standalone checks from the repo root:

```bash
python docs/contracts/dodecagonal-square-triangle-generator/test_generator.py
```

## Integration Note

The application runtime now vendors a generated JSON snapshot of the same
snapped literature source under `backend/simulation/data/` so both server and
standalone hosts can use the same reconstruction without needing live PDF
parsing. This folder remains the narrow standalone handoff copy.
