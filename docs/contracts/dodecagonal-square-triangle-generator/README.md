# Dodecagonal Square-Triangle Generator

This file documents the runtime generator for the public
`dodecagonal-square-triangle` family.

The implementation lives in
`backend/simulation/aperiodic_dodecagonal_square_triangle.py`. There is no
vendored data: the runtime is a deterministic geometric construction that
scales to any requested patch depth.

## Construction

The runtime tiles the plane with a decorated 3.12.12 Archimedean tiling:

1. Place regular dodecagonal supercells on a hexagonal lattice with primitive
   pitch `2 + sqrt(3)` (the dodecagon-edge-sharing distance for unit-edge
   regular dodecagons).
2. Decompose every dodecagon into its canonical layout of six unit squares plus
   twelve unit equilateral triangles. The interior layout is 6-fold symmetric:
   six inner triangles fan out from the centre to form a unit hexagon, six
   unit squares sit on each hexagon edge, and six outer triangles wedge between
   adjacent squares.
3. Add the bridging equilateral triangles of the underlying 3.12.12 tiling
   (one per dodecagon corner, shared by three supercells). Each supercell
   claims two of those triangles using a 120-degree-orbit transversal so that
   each plane triangle is owned by exactly one supercell.

For any requested `patch_depth`, the runtime materialises supercells in a
sufficient hex-lattice radius around the origin, builds edge-sharing
adjacency, and returns the BFS-cropped subgraph from a chosen seed square.

## Public Vocabulary

- `tile_family = "dodecagonal-square-triangle"`
- `dodecagonal-square-triangle-square` — `chirality_token = None`
- `dodecagonal-square-triangle-triangle` — `chirality_token` in
  `{"red", "yellow", "blue"}` derived from the centroid-relative orientation
  of the first vertex.

## Invariants

At every patch depth the runtime patch must remain:

- deterministic for the same `patch_depth`
- one connected component
- hole-free
- overlap-free
- composed of unit squares and unit equilateral triangles only
- full-edge adjacent rather than point-touching
- stable in ids and cell ordering

## Caveats

- The construction is not the canonical Schlottmann quasi-periodic
  square-triangle tiling. A faithful Schlottmann substitution requires marked
  prototiles and is not currently available in-repo.
- The decorated 3.12.12 generator is locally 6-fold symmetric inside every
  former-dodecagon region (and 12-fold symmetric in flavour because the
  enclosing dodecagonal shape is regular) but globally periodic at the
  hex-lattice scale.
- The asymptotic triangle/square ratio is 14:6 = 7:3 ≈ 2.333, close to the
  canonical Schlottmann limit of 4/sqrt(3) ≈ 2.309 but not identical.
