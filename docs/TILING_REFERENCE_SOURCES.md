# Tiling Reference Sources

This file lists the current literature or catalog references used when writing and maintaining `backend/simulation/literature_reference_specs.py`.

The order is intentional:

1. family-specific substitution or tiling source
2. broader reference fallback only when the family-specific source is weaker or unavailable

## Regular Grids

- `square`
  - [Square tiling](https://en.wikipedia.org/wiki/Square_tiling)
  - [Regular tiling](https://en.wikipedia.org/wiki/Regular_tiling)
- `hex`
  - [Hexagonal tiling](https://en.wikipedia.org/wiki/Hexagonal_tiling)
  - [Regular tiling](https://en.wikipedia.org/wiki/Regular_tiling)
- `triangle`
  - [Triangular tiling](https://en.wikipedia.org/wiki/Triangular_tiling)
  - [Regular tiling](https://en.wikipedia.org/wiki/Regular_tiling)

## Periodic Mixed / Uniform Families

- `archimedean-4-8-8`
  - [Truncated square tiling](https://en.wikipedia.org/wiki/Truncated_square_tiling)
- `archimedean-3-12-12`
  - [Truncated hexagonal tiling](https://en.wikipedia.org/wiki/Truncated_hexagonal_tiling)
- `archimedean-3-4-6-4`
  - [Rhombitrihexagonal tiling](https://en.wikipedia.org/wiki/Rhombitrihexagonal_tiling)
- `archimedean-4-6-12`
  - [Truncated trihexagonal tiling](https://en.wikipedia.org/wiki/Truncated_trihexagonal_tiling)
- `archimedean-3-3-4-3-4`
  - [Snub square tiling](https://en.wikipedia.org/wiki/Snub_square_tiling)
- `archimedean-3-3-3-4-4`
  - [Elongated triangular tiling](https://en.wikipedia.org/wiki/Elongated_triangular_tiling)
- `archimedean-3-3-3-3-6`
  - [Snub trihexagonal tiling](https://en.wikipedia.org/wiki/Snub_trihexagonal_tiling)
- `trihexagonal-3-6-3-6`
  - [Trihexagonal tiling](https://en.wikipedia.org/wiki/Trihexagonal_tiling)
- `uniform-2-10-36-3262`
  - [List of k-uniform tilings](https://en.wikipedia.org/wiki/List_of_k-uniform_tilings)
  - [2-uniform #10 reference image](https://commons.wikimedia.org/wiki/File:2-uniform_n10.svg)
- `uniform-2-2-3122-34312`
  - [List of k-uniform tilings](https://en.wikipedia.org/wiki/List_of_k-uniform_tilings)
  - [2-uniform #2 reference image](https://commons.wikimedia.org/wiki/File:2-uniform_n2.svg)
- `uniform-2-19-v1-36-346`
  - [List of k-uniform tilings](https://en.wikipedia.org/wiki/List_of_k-uniform_tilings)
  - [2-uniform #19 variant 1 reference image](https://commons.wikimedia.org/wiki/File:2-uniform_n19.svg)
- `uniform-3-4-36-3262-63`
  - [List of k-uniform tilings](https://en.wikipedia.org/wiki/List_of_k-uniform_tilings)
  - [3-uniform #4 reference image](https://commons.wikimedia.org/wiki/File:3-uniform_4.svg)
- `cairo-pentagonal`
  - [Cairo pentagonal tiling](https://en.wikipedia.org/wiki/Cairo_pentagonal_tiling)
- `rhombille`
  - [Rhombille tiling](https://en.wikipedia.org/wiki/Rhombille_tiling)
- `deltoidal-hexagonal`
  - [Deltoidal hexagonal tiling](https://en.wikipedia.org/wiki/Deltoidal_hexagonal_tiling)
- `tetrakis-square`
  - [Tetrakis square tiling](https://en.wikipedia.org/wiki/Tetrakis_square_tiling)
- `triakis-triangular`
  - [Triakis triangular tiling](https://en.wikipedia.org/wiki/Triakis_triangular_tiling)
- `deltoidal-trihexagonal`
  - [Deltoidal trihexagonal tiling](https://en.wikipedia.org/wiki/Deltoidal_trihexagonal_tiling)
- `prismatic-pentagonal`
  - [Prismatic pentagonal tiling](https://en.wikipedia.org/wiki/Prismatic_pentagonal_tiling)
- `floret-pentagonal`
  - [Floret pentagonal tiling](https://en.wikipedia.org/wiki/Floret_pentagonal_tiling)
- `type-7-pentagonal`
  - [Pentagonal tiling](https://en.wikipedia.org/wiki/Pentagonal_tiling)
  - [Type 7 pentagonal tiling](https://www.mathartroom.com/wallpaper/pentagon_tiling/type07/)
- `house-pentagonal`
  - [Pentagonal tiling](https://en.wikipedia.org/wiki/Pentagonal_tiling)
  - The "house" / home-plate pentagon (unit square + symmetric 45-degree roof;
    angles 90/90/135/90/135) is the simplest Type 1 monohedral convex pentagon.
    Shipped as an edge-to-edge tiling with rational coordinates on a skewed
    two-tile lattice (`lattice_skew_x`); upright + inverted houses interlock so
    inverted tops carry the next row shifted by half a cell.
- `snub-square-dual`
  - [Snub square tiling](https://en.wikipedia.org/wiki/Snub_square_tiling)
  - [Pentagonal tiling](https://en.wikipedia.org/wiki/Pentagonal_tiling)
- `kisrhombille`
  - [Truncated trihexagonal tiling](https://en.wikipedia.org/wiki/Truncated_trihexagonal_tiling)

## Aperiodic / Substitution Families

- `penrose-p3-rhombs`
  - [Penrose rhomb](https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/)
- `penrose-p3-rhombs-vertex`
  - [Penrose rhomb](https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/)
- `penrose-p1`
  - `distributed` mode (`penrose-p1-pentagon-diamond` implementation geometry)
    - [Penrose tiling: original pentagonal tiling (P1)](https://en.wikipedia.org/wiki/Penrose_tiling#Original_pentagonal_Penrose_tiling_(P1))
    - [Pentagrid and Penrose tilings](https://www.math.brown.edu/reschwar/M272/pentagrid.pdf)
    - [Pattern Collider](https://github.com/aatishb/patterncollider)
  - `boat-star` mode (`penrose-p1-pentagon-boat-star` implementation geometry)
    - [Penrose Pentagon Boat Star](https://tilings.math.uni-bielefeld.de/substitution/penrose-pentagon-boat-star/)
    - [Pentagrid and Penrose tilings](https://www.math.brown.edu/reschwar/M272/pentagrid.pdf)
- `penrose-p2-kite-dart`
  - [Penrose kite-dart](https://tilings.math.uni-bielefeld.de/substitution/penrose-kite-dart/)
- `ammann-beenker`
  - [Ammann-Beenker](https://tilings.math.uni-bielefeld.de/substitution/ammann-beenker/)
- `spectre`
  - [Spectre](https://tilings.math.uni-bielefeld.de/substitution/spectre/)
  - [The Spectre monotile paper DOI page](https://doi.org/10.5070/C64264241)
- `hat-monotile`
  - [An aperiodic monotile](https://arxiv.org/abs/2303.10798)
  - [Hat metatiles](https://tilings.math.uni-bielefeld.de/substitution/hat-metatiles/)
- `turtle-monotile`
  - [An aperiodic monotile](https://arxiv.org/abs/2303.10798) (the Turtle is the `Tile(sqrt(3), 1)` member of the hat continuum)
  - [Hat metatiles](https://tilings.math.uni-bielefeld.de/substitution/hat-metatiles/)
  - [christianp/aperiodic-monotile](https://github.com/christianp/aperiodic-monotile) (independent canonical Turtle outline used in congruence tests)
- `taylor-socolar`
  - [Half-hex](https://tilings.math.uni-bielefeld.de/substitution/half-hex/)
  - [Lee and Moody 2013](https://www.mdpi.com/2073-8994/5/1/1)
- `sphinx`
  - [Sphinx](https://tilings.math.uni-bielefeld.de/substitution/sphinx/)
- `chair`
  - [Chair](https://tilings.math.uni-bielefeld.de/substitution/chair/)
  - The app representative patch starts from two substituted chair supertiles
    arranged as a 3x2 rectangle so the default view is wider while preserving
    the same inflation-by-2 chair substitution.
- `l-tetromino`
  - [Rep-tile (L-tromino / L-tetromino / P-pentomino are rep-n^2)](https://en.wikipedia.org/wiki/Rep-tile)
  - Shipped as the exact integer-lattice rep-4 substitution of the L-tetromino
    (the tetromino analogue of the L-tromino `chair`). The rep-4 dissection is
    geometrically exact and self-evident, so faithfulness needs no external
    coordinate source; it is verified directly (area conservation, congruence to
    the prototile, gap-free / overlap-free cover). The representative app patch
    uses two substituted supertiles arranged as a 4x2 rectangle so the default
    view is wider without changing the underlying substitution rule.
- `p-pentomino`
  - [Rep-tile (L-tromino / L-tetromino / P-pentomino are rep-n^2)](https://en.wikipedia.org/wiki/Rep-tile)
  - Shipped as the exact integer-lattice rep-4 substitution of the P-pentomino,
    the *unique* rep-4 pentomino (every other pentomino fails rep-4, confirmed by
    exhaustive exact cover of the doubled tile). As with the other rep-tiles the
    dissection is geometrically exact, so faithfulness needs no external
    coordinate source; it is verified directly (area conservation, congruence to
    the prototile, gap-free / overlap-free cover). Being chiral, the substitution
    closes over the full eight-element dihedral group D4 rather than a
    four-element subgroup. The representative app patch uses two substituted
    supertiles arranged as a 5x2 rectangle so the default view is wider without
    changing the underlying substitution rule.
- `robinson-triangles`
  - [Robinson triangle](https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/)
- `tuebingen-triangle`
  - [Tuebingen Triangle](https://tilings.math.uni-bielefeld.de/substitution/tuebingen-triangle/)
- `dodecagonal-square-triangle`
  - [Square-triangle](https://tilings.math.uni-bielefeld.de/substitution/square-triangle/)
  - The runtime is a decorated 3.12.12 Archimedean tiling: hexagonal lattice of
    regular dodecagonal supercells, each decomposed into the canonical six unit
    squares plus twelve unit equilateral triangles, with two bridging triangles
    per supercell from the underlying 3.12.12 layout. It scales without a
    depth limit and depends on no vendored data. It is not the canonical
    Schlottmann quasi-periodic tiling.
- `socolar-12-fold`
  - [Socolar](https://tilings.math.uni-bielefeld.de/substitution/socolar/)
  - [Socolar, *Simple octagonal and dodecagonal quasicrystals*, Phys. Rev. B 39 (1989)](https://doi.org/10.1103/PhysRevB.39.10519)
  - [Socolar tiling](https://en.wikipedia.org/wiki/Socolar_tiling)
  - [Klitzing, Socolar tiling (prototiles, inflation 2+sqrt(3), substitution matrix, A2xA2 cut-and-project)](https://bendwavy.org/klitzing/quasi/socolar.htm)
  - Shipped as the dodecagonal **rhombus** tiling (catalog label "Socolar
    12-fold (rhombs)"; prototiles {30° rhomb, 60° rhomb, square}), built by the
    de Bruijn generalized-dual multigrid and MLD to `shield`. This is a distinct
    prototile presentation from the canonical Socolar tiling {30° rhomb, square,
    hexagon}; see [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).
- `enneagonal-9-fold`
  - [Substitution tilings encyclopedia](https://tilings.math.uni-bielefeld.de/substitution/)
  - [Pentagrid and Penrose tilings (de Bruijn generalized-dual method)](https://www.math.brown.edu/reschwar/M272/pentagrid.pdf)
  - [Pattern Collider](https://github.com/aatishb/patterncollider)
  - Shipped as the de Bruijn **enneagrid rhombus** tiling (catalog label
    "Enneagonal 9-fold (rhombs)"; four prototiles, rhombi with acute angles 20°,
    40°, 60°, 80°), the 9-fold analogue of the Penrose and Socolar multigrid
    rhomb tilings. This is a distinct construction from any Danzer-style 9-fold
    marked-prototile substitution; see
    [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).
- `heptagonal-7-fold`
  - [Goodman-Strauss 7-fold rhomb](https://tilings.math.uni-bielefeld.de/substitution/goodman-strauss-7-fold-rhomb/)
  - [Pentagrid and Penrose tilings (de Bruijn generalized-dual method)](https://www.math.brown.edu/reschwar/M272/pentagrid.pdf)
  - [Pattern Collider](https://github.com/aatishb/patterncollider)
  - Shipped as the de Bruijn **heptagrid rhombus** tiling (catalog label
    "Heptagonal 7-fold (rhombs)"; prototiles {thin, medium, wide} rhombi with
    acute angles pi/7, 2*pi/7, 3*pi/7), the 7-fold analogue of the Penrose and
    Socolar multigrid rhomb tilings. This is a distinct construction from the
    Goodman-Strauss 7-fold marked-prototile substitution; see
    [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).
- `hendecagonal-11-fold`
  - [Substitution tilings encyclopedia](https://tilings.math.uni-bielefeld.de/substitution/)
  - [Pentagrid and Penrose tilings (de Bruijn generalized-dual method)](https://www.math.brown.edu/reschwar/M272/pentagrid.pdf)
  - [Pattern Collider](https://github.com/aatishb/patterncollider)
  - Shipped as the de Bruijn **hendecagrid rhombus** tiling (catalog label
    "Hendecagonal 11-fold (rhombs)"; five prototiles, rhombi with acute angles
    `k * 180/11` for k = 1..5), the 11-fold analogue of the Penrose and Socolar
    multigrid rhomb tilings. Eleven is prime, so the eleven families are fully
    independent. This is a distinct construction from any marked-prototile
    substitution; see [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).
- `tridecagonal-13-fold`
  - [Substitution tilings encyclopedia](https://tilings.math.uni-bielefeld.de/substitution/)
  - [Pentagrid and Penrose tilings (de Bruijn generalized-dual method)](https://www.math.brown.edu/reschwar/M272/pentagrid.pdf)
  - [Pattern Collider](https://github.com/aatishb/patterncollider)
  - Shipped as the de Bruijn **tridecagrid rhombus** tiling (catalog label
    "Tridecagonal 13-fold (rhombs)"; six prototiles, rhombi with acute angles
    `k * 180/13` for k = 1..6), the 13-fold analogue of the Penrose and Socolar
    multigrid rhomb tilings. Thirteen is prime, so the thirteen families are
    fully independent. This is a distinct construction from any marked-prototile
    substitution; see [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).
- `shield`
  - [Shield](https://tilings.math.uni-bielefeld.de/substitution/shield/)
- `pinwheel`
  - [The pinwheel tilings of the plane](https://annals.math.princeton.edu/1994/139-3/p05)
  - [Pinwheel](https://tilings.math.uni-bielefeld.de/substitution/pinwheel/)

## Notes

- Periodic mixed families now default to family-specific citations. `snub-square-dual` still keeps a pentagonal-tiling background reference because the public dual-family material is weaker than the primary snub-square source alone.
- The verifier is allowed to be stronger than the source list here, but not weaker. If a new reference drives a spec change, update this file at the same time.
