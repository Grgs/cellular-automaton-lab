# Canonical Socolar Generator

This file documents the runtime generator for the public `socolar-hexagonal`
family (catalog label "Socolar (hexagon-square-rhomb)") — the **canonical**
Socolar tiling with prototiles {regular hexagon, square, 30° rhomb}
(Socolar, *Simple octagonal and dodecagonal quasicrystals*, Phys. Rev. B 39,
1989). The pre-existing `socolar-12-fold` family is the distinct dodecagonal
**rhombus** presentation; this family carries the hexagon-bearing canonical
prototile set.

The implementation lives in
`backend/simulation/aperiodic_socolar_hexagonal.py`.

## Construction

The runtime is Socolar's **cut-and-project** construction (the scheme Socolar
described alongside the decorated substitution; per Klitzing it projects from
the A2xA2 root lattice), expressed as exact acceptance-window tests:

1. Coordinates are integer 4-tuples `(a, b, c, d)` in the `Z[zeta12]` module
   (`zeta = exp(i*pi/6)`, `zeta^4 = zeta^2 - 1`) at x2 scale, so every tile
   center is integral. The Galois star map `zeta -> zeta^5` (linear on
   coefficients) sends centers to internal space.
2. Tile centers split into 13 classes — 6 rhomb orientations, 3 square
   orientations, and 2 hexagon orientation families x 2 deep-hole subtypes —
   each a coset of a rank-4 sublattice. A center hosts a tile exactly when its
   star image lies in that class's **closed** convex window: equilateral
   triangles for the hexagon subtypes (the A2 Delone up/down triangles; the
   third sub-coset of each hexagon family is never occupied), parallelograms
   for rhombs, squares for squares. All window-edge normals are multiples of
   30° and all offsets are exact in `Q(sqrt(3))`, so membership is decided by
   exact integer sign tests.
3. A patch of depth `d` is every tile whose center lies within
   `4 + 0.75*d` tile-edge units of the origin. Cell ids come from the exact
   module center, so shallower patches are id-subsets of deeper ones.

## Why not a substitution rule table

The Socolar substitution (inflation `2 + sqrt(3)`, child counts rhomb
3r+6s+0h / square 4r+1s+4h / hexagon 12r+12s+7h) was extracted from the
encyclopedia's rule figure and validated during development, but it is
**oriented**: the hexagon supertile's three boundary "pillow" regions (four
tiles each) flip between two point-reflected states, and empirically the flip
is determined neither by the parent slot nor by any adjacent supertile — the
flips are the phases of the tiling's 1-dimensional quasiperiodic Conway worms,
which Socolar's original construction pins with arrow decorations. An
undecorated parent-to-children rule table therefore cannot deterministically
generate the canonical tiling; the cut-and-project windows encode the same
information exactly.

## Provenance and verification

The window data was extracted from the Tilings Encyclopedia's published
Socolar patch and is independent of this generator's own output:

- the encyclopedia patch (`patch.gif`, 2353 complete tiles) was segmented and
  exact-snapped to the module: every tile verified as a unit-edge prototile,
  every interior vertex angle sum exactly 360°, zero duplicate directed edges;
- per class, the observed star images and every rejected coset point separate
  perfectly under the closed windows (verified with exact `Q(sqrt(3))`
  arithmetic; the patch's translation gauge is singular, with module points
  exactly on window boundaries, and the closed-window convention reproduces
  the published member's resolution of those orbits);
- regenerating the patch region from the windows alone reproduces the
  encyclopedia patch **tile-for-tile** (1876/1876 deep-interior tiles, zero
  missing/extra/kind mismatches), and the runtime's exact output was re-diffed
  against the extraction at radius 13 (457/457 tiles);
- a 338-tile sample of the exact-snapped literature patch is vendored at
  `backend/simulation/data/socolar_hexagonal_literature_sample.json`, and
  `tests/unit/test_aperiodic_socolar_hexagonal.py` re-runs the bidirectional
  tile-for-tile diff against it on every test run.

Corroborating independent checks performed during extraction: prototile
frequencies converge to the Perron ratios `sqrt(3) : sqrt(3) : 1`
(rhomb : square : hexagon); the five interior vertex configurations and their
frequencies match between the generated tiling and the literature patch; the
substitution child counts above (from Klitzing) reappear exactly when the
patch is decomposed into supertiles.

## Public vocabulary

- `tile_family = "socolar-hexagonal"`
- `socolar-hexagonal-hexagon` — `orientation_token` in `{"0", "30"}`
- `socolar-hexagonal-square` — `orientation_token` in `{"0", "30", "60"}`
- `socolar-hexagonal-rhomb` — `orientation_token` in
  `{"0", "30", ..., "150"}`

## Invariants

At every patch depth the runtime patch must remain:

- deterministic for the same `patch_depth`
- one connected component, hole-free, overlap-free
- composed of unit-edge regular hexagons, squares, and 30° rhombs only
- free of same-kind edge contacts (the Socolar matching rules: rhomb-rhomb,
  square-square, and hexagon-hexagon adjacencies never occur)
- stable in ids (shallower patches are id-subsets of deeper patches)

## Caveats

- The generator emits the specific tiling member published by the
  encyclopedia (its singular, symmetric gauge), not a generic member of the
  LI class; this is deliberate so the vendored literature diff stays exact.
- The tiles are emitted undecorated: Socolar's edge arrows / Ammann bars are
  matching-rule decorations and are not part of the public vocabulary.
