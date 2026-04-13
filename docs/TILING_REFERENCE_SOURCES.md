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
- `snub-square-dual`
  - [Snub square tiling](https://en.wikipedia.org/wiki/Snub_square_tiling)
  - [Pentagonal tiling](https://en.wikipedia.org/wiki/Pentagonal_tiling)

## Aperiodic / Substitution Families

- `penrose-p3-rhombs`
  - [Penrose rhomb](https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/)
- `penrose-p3-rhombs-vertex`
  - [Penrose rhomb](https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/)
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
- `taylor-socolar`
  - [Half-hex](https://tilings.math.uni-bielefeld.de/substitution/half-hex/)
  - [Lee and Moody 2013](https://www.mdpi.com/2073-8994/5/1/1)
- `sphinx`
  - [Sphinx](https://tilings.math.uni-bielefeld.de/substitution/sphinx/)
- `chair`
  - [Chair](https://tilings.math.uni-bielefeld.de/substitution/chair/)
- `robinson-triangles`
  - [Robinson triangle](https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/)
- `tuebingen-triangle`
  - [Tuebingen Triangle](https://tilings.math.uni-bielefeld.de/substitution/tuebingen-triangle/)
- `dodecagonal-square-triangle`
  - [Square-triangle](https://tilings.math.uni-bielefeld.de/substitution/square-triangle/)
- `shield`
  - [Shield](https://tilings.math.uni-bielefeld.de/substitution/shield/)
- `pinwheel`
  - [The pinwheel tilings of the plane](https://annals.math.princeton.edu/1994/139-3/p05)
  - [Pinwheel](https://tilings.math.uni-bielefeld.de/substitution/pinwheel/)

## Notes

- Periodic mixed families now default to family-specific citations. `snub-square-dual` still keeps a pentagonal-tiling background reference because the public dual-family material is weaker than the primary snub-square source alone.
- The verifier is allowed to be stronger than the source list here, but not weaker. If a new reference drives a spec change, update this file at the same time.
