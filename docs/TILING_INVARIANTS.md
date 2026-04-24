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
  - reciprocal dual-family edge-count / vertex-valence compatibility for unambiguous pairs
  - dual-candidate class and interior-valence signature checks for the currently ambiguous catalog groups
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
  - direct canonical patch comparisons where rooted local anchors are still too weak
  - exact polygon-area frequency checks where multiscale hierarchy is part of the family model

## Family-Specific Notes

- `pinwheel`
  - the canonical representative patch starts from two literature right triangles forming a rectangle
  - must use the exact-affine verification path
  - contiguity is verified from exact positive-length segment overlap, not only exact whole-edge identity
  - orientation diversity must increase with depth
  - exact-record ids must match serialized patch ids
  - exact-record growth must follow the paired-seed substitution count `2 * 5^d`
  - representative support should expand with depth on the exact-affine inflation path
  - a rooted local-reference anchor now checks the exact-path neighborhood around a canonical depth-3 tile
  - direct canonical patch fixtures now check the exact serialized patch on that exact-affine path at both depth `1` and depth `3`
  - the representative sample must remain hole-free under the canonical surface checks
- `shield`
  - the authoritative verifier sample now comes from Gahler's marked recursive substitution rule translated from the published PostScript source
  - runtime depth is exact substitution depth on a single right-shield seed
  - the public runtime still collapses marked internal tiles to shield / square / triangle kinds while preserving orientation and chirality metadata
  - rooted local-reference fixtures now check canonical neighborhoods inside the exact substitution patch
  - direct canonical patch fixtures now check the normalized public serialization exactly at both depth `1` and depth `3`
- `hat-monotile`
  - verification assumes an `H8`-rooted representative patch rather than a one-tile seed
  - representative patches should include opposite-chirality Hat adjacencies
  - reflected hats should appear in the characteristic three-neighbor opposite-chirality local pattern described by the Hat metatiles source
  - rooted local-reference fixtures now check a canonical neighborhood around that `H8`-rooted sample
- `tuebingen-triangle`
  - chirality metadata is part of the expected output
  - direct canonical patch fixtures now pin both the first handed substitution patch and the representative depth-`3` sample
- `dodecagonal-square-triangle`
  - public output collapses internal marked tiles to square/triangle kinds, but orientation and chirality metadata remain meaningful
  - the runtime expands a checked-in five-state substitution spec recovered from the Bielefeld rule image, then crops a connected graph-distance patch
  - the finite Bielefeld vector crop remains oracle tooling only, not the public runtime source
  - representative samples must stay connected, overlap-clean, hole-free, and exact on public kind counts plus signature
  - rooted local-reference fixtures now pin canonical square/triangle neighborhoods inside the substitution-cropped sample
  - direct canonical patch fixtures now check the normalized public square/triangle serialization exactly at both depth `1` and depth `3`
- `robinson-triangles`
  - direct canonical patch fixtures now pin both the first refined Robinson triangle patch and the representative depth-`3` sample
- `chair`
  - representative patches should follow the true inflation-by-2 chair substitution from a single chair seed
  - low-depth samples should preserve exact substitution depth totals and orientation-token distributions
  - rooted local-reference fixtures now pin a canonical depth-3 neighborhood inside the corrected substitution patch

## What Is Not Yet Proved

- For many families, the verifier is strongest at the level of deterministic low-depth samples, count invariants, and adjacency vocabulary.
- For periodic families, the verifier is now stronger than a plain sample-signature check, but it still targets finite family-specific open-boundary boards rather than quotient-surface or large-sample proofs.
- Periodic dual-family checks now cover unambiguous reciprocal pairs and the current ambiguous candidate classes, but they are still finite-sample descriptor checks rather than full dual constructions.
- The new reference layer mixes rooted neighborhoods with direct canonical patch diffs for selected families; it is not yet a full canonical patch-diff system across the whole catalog.
- `shield` now comes from an exact marked substitution translated from Gahler's published PostScript rule, and it is held to the same strict shared-surface, overlap, and edge-multiplicity checks as the other exact edge-sharing substitution families.
- That is stronger than screenshot plausibility, but it is still not the same thing as a full symbolic proof that the generator exactly matches the literature’s substitution system at all depths.
