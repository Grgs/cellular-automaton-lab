# Tiling Invariants

This file records the invariants the repo currently treats as authoritative when verifying tilings.

It is intentionally shorter than `backend/simulation/literature_reference_specs.py`; this is the human summary, not the executable source of truth.

## Regular Grids

- Canonical sample: open-boundary `3x3`
- Public kind vocabulary: `cell`
- Required checks:
  - exact sample size
  - exact degree histogram
  - exact adjacency-pair set
  - deterministic signature

## Periodic Mixed / Periodic-Face Families

- Canonical sample: descriptor-driven `3x3`
- Required checks:
  - exact sample size
  - exact public kind counts
  - exact adjacency-pair set
  - exact degree histogram
  - deterministic signature
- Additional periodic-face checks:
  - `metric_model == "pattern"`
  - `cell_count_per_unit` matches the number of loaded face templates
  - descriptor face-kind vocabulary matches the expected public kind vocabulary
  - descriptor slot vocabulary matches the expected template slots
  - descriptor `id_pattern` round-trips generated cell ids
  - same-slot cells repeat by `unit_width` / `unit_height`
  - odd-row horizontal offsets match `row_offset_x`

## Aperiodic Substitution Families

- Canonical sample: patch-depth sample chosen per family
- Required checks vary by family but generally include:
  - exact or minimum cell counts at low depths
  - allowed public kind vocabulary
  - required adjacency-pair set
  - deterministic signature
  - metadata presence for families that expose orientation, chirality, tile family, or decorations

## Family-Specific Notes

- `pinwheel`
  - must use the exact-affine verification path
  - orientation diversity must increase with depth
  - exact-record ids must match serialized patch ids
  - representative support should expand with depth rather than remain a fixed rectangle
- `shield`
  - `decoration_tokens` are part of the verification surface even though they are not rendered
  - decorated cell kinds should expose multiple decoration-token variants in representative patches
- `hat-monotile`
  - verification assumes an `H8`-rooted representative patch rather than a one-tile seed
  - representative patches should include opposite-chirality Hat adjacencies
  - reflected hats should appear in the characteristic three-neighbor opposite-chirality local pattern described by the Hat metatiles source
- `tuebingen-triangle`
  - chirality metadata is part of the expected output
- `square-triangle`
  - public output collapses internal marked tiles to square/triangle kinds, but orientation and chirality metadata remain meaningful
- `chair`
  - the literature target is the Ammann Chair family, so representative patches should expose more than one chair size class

## What Is Not Yet Proved

- For many families, the verifier is strongest at the level of deterministic low-depth samples, count invariants, and adjacency vocabulary.
- For periodic families, the verifier is now stronger than a plain sample-signature check, but it still targets finite `3x3` open-boundary boards rather than quotient-surface or large-sample proofs.
- That is stronger than screenshot plausibility, but it is still not the same thing as a full symbolic proof that the generator exactly matches the literature’s substitution system at all depths.
