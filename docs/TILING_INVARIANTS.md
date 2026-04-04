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

- Canonical sample: descriptor-driven family-specific open-boundary grid from the reference spec
  - current catalog audit result: all shipped periodic families still use `3x3`
- Required checks:
  - exact sample size
  - exact public kind counts
  - exact adjacency-pair set
  - exact degree histogram
  - deterministic signature
  - exact interior vertex-configuration set
  - exact interior vertex-configuration frequencies
  - selected reciprocal dual-family edge-count / vertex-valence compatibility
- Additional periodic-face checks:
  - `metric_model == "pattern"`
  - `cell_count_per_unit` matches the number of loaded face templates
  - descriptor face-kind vocabulary matches the expected public kind vocabulary
  - descriptor slot vocabulary matches the expected template slots
  - descriptor `id_pattern` round-trips generated cell ids
  - same-slot cells repeat by `unit_width` / `unit_height`
  - odd-row horizontal offsets match `row_offset_x`
  - reciprocal dual-family edge-count / vertex-valence compatibility for the periodic pairs that have an unambiguous dual already present in the catalog

## Aperiodic Substitution Families

- Canonical sample: patch-depth sample chosen per family
- Required checks vary by family but generally include:
  - exact or minimum cell counts at low depths
  - allowed public kind vocabulary
  - required adjacency-pair set
  - deterministic signature
  - metadata presence for families that expose orientation, chirality, tile family, or decorations
  - family-specific rooted local-reference fixtures where low-depth counts/signatures alone are too weak
  - exact polygon-area frequency checks where multiscale hierarchy is part of the family model

## Family-Specific Notes

- `pinwheel`
  - must use the exact-affine verification path
  - contiguity is verified from exact positive-length segment overlap, not only exact whole-edge identity
  - orientation diversity must increase with depth
  - exact-record ids must match serialized patch ids
  - representative support should expand with depth on the exact-affine inflation path
  - a rooted local-reference anchor now checks the exact-path neighborhood around a canonical depth-3 tile
- `shield`
  - `decoration_tokens` are part of the verification surface
  - decorated cell kinds should expose multiple decoration-token variants in representative patches
  - rooted local-reference fixtures now check canonical decorated neighborhoods
  - dead-state rendering now uses decoration-aware accents, but picker promotion still depends on separate browser-visible approval
- `hat-monotile`
  - verification assumes an `H8`-rooted representative patch rather than a one-tile seed
  - representative patches should include opposite-chirality Hat adjacencies
  - reflected hats should appear in the characteristic three-neighbor opposite-chirality local pattern described by the Hat metatiles source
  - rooted local-reference fixtures now check a canonical neighborhood around that `H8`-rooted sample
- `tuebingen-triangle`
  - chirality metadata is part of the expected output
- `square-triangle`
  - public output collapses internal marked tiles to square/triangle kinds, but orientation and chirality metadata remain meaningful
  - the authoritative verifier sample is now a cleaned dense depth-3 central component of the literature patch, not just a shallow adjacency shell
  - that depth-3 sample must stay connected, overlap-clean, hole-free, and exact on public kind counts plus signature
  - rooted local-reference fixtures now pin a few canonical square/triangle neighborhoods inside that dense sample
- `chair`
  - representative patches should follow the true inflation-by-2 chair substitution from a single chair seed
  - low-depth samples should preserve exact substitution depth totals and orientation-token distributions
  - rooted local-reference fixtures now pin a canonical depth-3 neighborhood inside the corrected substitution patch

## What Is Not Yet Proved

- For many families, the verifier is strongest at the level of deterministic low-depth samples, count invariants, and adjacency vocabulary.
- For periodic families, the verifier is now stronger than a plain sample-signature check, but it still targets finite family-specific open-boundary boards rather than quotient-surface or large-sample proofs.
- Reciprocal dual-family checks currently cover only the periodic pairs whose dual matches are unambiguous in the current catalog.
- The new local-reference layer is rooted-neighborhood based; it is not yet a full canonical patch-diff system.
- That is stronger than screenshot plausibility, but it is still not the same thing as a full symbolic proof that the generator exactly matches the literature’s substitution system at all depths.
