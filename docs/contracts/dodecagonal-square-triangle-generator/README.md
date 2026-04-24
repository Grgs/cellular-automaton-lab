# Dodecagonal Square-Triangle Source Bundle

This directory contains the literature source assets for the public
`dodecagonal-square-triangle` family.

It is not a second executable generator. The application runtime uses the
backend implementation in
`backend/simulation/aperiodic_dodecagonal_square_triangle.py` together with the
derived backend source file
`backend/simulation/data/dodecagonal_square_triangle_literature_source.json`.

## Files

- `bielefeld-patch.pdf`
  - primary vector source used to regenerate the backend-owned literature source
- `reference-patch.json`
  - baseline artifact for comparison against the older cleaned-patch approach
- `../../../tools/regenerate_dodecagonal_literature_source.py`
  - regeneration tool that parses the PDF, snaps shared vertices, rebuilds
    shared-edge adjacency, and rewrites the backend-owned JSON source

## Runtime Integration

The authoritative runtime path is:

1. `bielefeld-patch.pdf` is the checked-in literature vector source.
2. `tools/regenerate_dodecagonal_literature_source.py` derives the snapped source
   JSON from that PDF.
3. `backend/simulation/aperiodic_dodecagonal_square_triangle.py` builds the app
   patch from the derived JSON.

## Public Vocabulary

- `tile_family = "dodecagonal-square-triangle"`
- `dodecagonal-square-triangle-square`
- `dodecagonal-square-triangle-triangle`

Square cells keep `chirality_token = None`. Triangle cells collapse to the
public triangle kind while preserving color-derived chirality tokens:
`"red"`, `"yellow"`, and `"blue"`.

## Core Reconstruction Rule

The runtime source does not use the older checked-in connected subset as its
source of truth. Instead the regeneration tool:

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

The derived backend source and emitted runtime patch must remain:

- deterministic for the same `patch_depth`
- one connected component
- hole-free
- overlap-free
- full-edge adjacent rather than point-touching
- stable in ids and cell ordering

## Regeneration And Verification

Run the regeneration check from the repo root:

```bash
python tools/regenerate_dodecagonal_literature_source.py --check
```

## Integration Note

The application runtime vendors a generated JSON snapshot of the snapped
literature source under `backend/simulation/data/` so the app does not need live
PDF parsing. This folder remains the narrow source-asset bundle for regenerating
that backend snapshot and for comparing it with the older reference patch.
