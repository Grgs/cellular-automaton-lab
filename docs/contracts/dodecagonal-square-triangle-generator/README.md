# Dodecagonal Square-Triangle Source Bundle

This directory contains the literature source assets for the public
`dodecagonal-square-triangle` family.

It is not a second executable generator. The application runtime uses the
backend implementation in
`backend/simulation/aperiodic_dodecagonal_square_triangle.py` together with the
derived backend source file
`backend/simulation/data/dodecagonal_square_triangle_literature_source.json`.

## Files

- `bielefeld-rule.png`
  - primary substitution-rule image used to regenerate the backend-owned
    substitution spec
- `bielefeld-patch.pdf`
  - finite vector patch retained as an oracle/reference crop during generator
    validation
- `reference-patch.json`
  - baseline artifact for comparison against the older cleaned-patch approach
- `../../../tools/regenerate_dodecagonal_substitution_spec.py`
  - regeneration tool that parses the rule image, extracts the five colored
    marked tile states, snaps child transforms to the `2 + sqrt(3)`
    substitution scale, and rewrites the backend-owned substitution spec
- `../../../tools/regenerate_dodecagonal_literature_source.py`
  - regeneration tool that parses the PDF, snaps shared vertices, rebuilds
    shared-edge adjacency, and rewrites the oracle-only JSON source

## Runtime Integration

The authoritative runtime path is:

1. `bielefeld-rule.png` is the checked-in substitution-rule source.
2. `tools/regenerate_dodecagonal_substitution_spec.py` derives
   `backend/simulation/data/dodecagonal_square_triangle_substitution_spec.json`.
3. `backend/simulation/aperiodic_dodecagonal_square_triangle.py` expands that
   spec and crops a connected graph-distance patch for the app.

The older `bielefeld-patch.pdf` path is still checked in as oracle tooling, not
as the public runtime generator.

## Public Vocabulary

- `tile_family = "dodecagonal-square-triangle"`
- `dodecagonal-square-triangle-square`
- `dodecagonal-square-triangle-triangle`

Square cells keep `chirality_token = None`. Triangle cells collapse to the
public triangle kind while preserving color-derived chirality tokens:
`"red"`, `"yellow"`, and `"blue"`.

## Core Reconstruction Rule

The runtime source does not use the older checked-in connected subset or finite
literature crop as its source of truth. Instead the substitution-spec
regeneration tool:

1. parses colored tile components from `bielefeld-rule.png`
2. classifies the five marked states: two squares and three triangles
3. fits regular square/triangle prototypes to each rule image component
4. snaps child linear transforms to rotations at the `2 + sqrt(3)` scale
5. propagates exact child translations through shared-edge constraints inside
   each supertile
6. emits deterministic public metadata while collapsing marked states back to
   square/triangle public kinds

This keeps the implementation tied to the literature rule image while avoiding a
runtime dependency on live image/PDF parsing.

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
python tools/regenerate_dodecagonal_substitution_spec.py --check
python tools/regenerate_dodecagonal_literature_source.py --check
```

## Integration Note

The application runtime vendors a generated JSON substitution spec under
`backend/simulation/data/` so the app does not need live image/PDF parsing. This
folder remains the narrow source-asset bundle for regenerating that backend
snapshot and for comparing it with the finite oracle/reference patch.
