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
  - deterministic signature
- Additional periodic-face checks:
  - `metric_model == "pattern"`
  - `cell_count_per_unit` matches the number of loaded face templates
  - descriptor face-kind vocabulary matches the expected public kind vocabulary

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
- `shield`
  - `decoration_tokens` are part of the verification surface even though they are not rendered
- `hat-monotile`
  - verification assumes an `H8`-rooted representative patch rather than a one-tile seed
- `tuebingen-triangle`
  - chirality metadata is part of the expected output
- `square-triangle`
  - public output collapses internal marked tiles to square/triangle kinds, but orientation and chirality metadata remain meaningful

## What Is Not Yet Proved

- For many families, the verifier is strongest at the level of deterministic low-depth samples, count invariants, and adjacency vocabulary.
- That is stronger than screenshot plausibility, but it is still not the same thing as a full symbolic proof that the generator exactly matches the literature’s substitution system at all depths.
