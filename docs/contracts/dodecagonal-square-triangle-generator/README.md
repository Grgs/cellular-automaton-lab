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
  - substitution-rule image used to regenerate the backend-owned diagnostic
    substitution spec
- `bielefeld-patch.pdf`
  - finite vector patch used by the current public runtime and retained as the
    validated reference crop
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

1. `bielefeld-patch.pdf` is parsed by
   `tools/regenerate_dodecagonal_literature_source.py`.
2. The tool derives
   `backend/simulation/data/dodecagonal_square_triangle_literature_source.json`.
3. `backend/simulation/aperiodic_dodecagonal_square_triangle.py` crops that
   finite source by graph distance for the app.

The checked-in `bielefeld-rule.png` path remains diagnostic tooling. It produces
a valid one-level rule-image patch, but the current five marked labels are not
enough to recursively substitute tiles without overlaps and fragmented
adjacency.

## Public Vocabulary

- `tile_family = "dodecagonal-square-triangle"`
- `dodecagonal-square-triangle-square`
- `dodecagonal-square-triangle-triangle`

Square cells keep `chirality_token = None`. Triangle cells collapse to the
public triangle kind while preserving color-derived chirality tokens:
`"red"`, `"yellow"`, and `"blue"`.

## Core Reconstruction Rule

The runtime source intentionally uses the finite literature crop until the
missing marked recursive state is recovered. The public depth cap is `40`.
Strict overlap-free and hole-free validation is currently proven through depth
`11`; higher depths are available as larger finite-crop views.

The substitution-spec regeneration tool is still useful for diagnostics:

1. parses colored tile components from `bielefeld-rule.png`
2. classifies the five marked states: two squares and three triangles
3. fits regular square/triangle prototypes to each rule image component
4. snaps child linear transforms to rotations at the `2 + sqrt(3)` scale
5. propagates exact child translations through shared-edge constraints inside
   each supertile
6. emits deterministic public metadata while collapsing marked states back to
   square/triangle public kinds

That diagnostic path keeps the extracted rule image available for future work
while avoiding a false recursive runtime.

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
python tools/regenerate_dodecagonal_substitution_spec.py --check
```

## Integration Note

The application runtime vendors generated JSON under `backend/simulation/data/`
so the app does not need live image/PDF parsing. This folder remains the narrow
source-asset bundle for regenerating that backend snapshot and for comparing it
with the diagnostic rule-image spec.
