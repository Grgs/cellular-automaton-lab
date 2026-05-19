# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

None.

## Current Known Deviations

- `dodecagonal-square-triangle` runs a decorated 3.12.12 Archimedean generator (each regular dodecagonal supercell decomposed into six unit squares plus twelve unit equilateral triangles, plus two bridging triangles per supercell). It tiles the plane exactly, has no depth cap, and uses no vendored data, but it is not the canonical Schlottmann quasi-periodic square-triangle tiling: the supercell layout is locally 6-fold symmetric and the global tiling is periodic at the supercell scale.
- `pinwheel` now renders as a clean two-root substitution patch (the previous chaotic look came from a vertex-ordering bug in the second root that made `_map_local` a non-similarity transform — fixed by listing the second root's vertices in the canonical `(small-angle, right-angle, large-angle)` order so the subdivision rule maps to similar children). The patch keeps both roots as `left` chirality at depth 0; the substitution rule (3 right + 2 left children per left parent) introduces full chirality variety from depth 1 onward. The visual is now consistent with Conway-Radin's pinwheel pattern; promotion out of `Experimental` is gated on a fresh manual review.

## Known Limits That Are Not Currently Treated As Failures

- `penrose-p3-rhombs` and `penrose-p3-rhombs-vertex` are built by the de Bruijn pentagrid construction in `backend/simulation/penrose.py` rather than by iterating the canonical Robinson half-tile substitution from a seed. The pentagrid is mathematically equivalent to the canonical Penrose rhomb substitution and produces valid thick / thin rhombs with correct matching at every depth, so the families are flagged as `canonical_patch` rather than `known_deviation`. The trade-off is that the depth-to-cell-count sequence (5/10/24/66 at depths 0..3) is governed by the bounding-box crop at half-extent `0.85 * phi^d` rather than by the substitution eigenvalue; the analogous half-tile rewrite (acutes at short edges into thin rhombs, obtuses at long edges into thick rhombs) was attempted but does not converge to a clean rhomb tiling at depth >= 2 from any rhomb-star or sun seed examined so far. See `docs/PENROSE_CANONICAL_SUBSTITUTION_PLAN.md` for the original investigation.
- `penrose-p1-pentagon-diamond` is the distributed Penrose P1 variant, built by the de Bruijn pentagrid construction (de Bruijn 1981; Pattern Collider by Aatish Bhatia) followed by a P3 → P1 vertex-merge pass, implemented in `backend/simulation/aperiodic_penrose_multigrid.py`. Stage 1 runs the pentagrid with non-uniform offsets `(0.3, 0.4, 0.5, 0.6, 0.7)` to get a regular Penrose P3 rhomb tiling distributed across the patch without a central singularity. Stage 2 walks every rhomb-vertex and identifies the four canonical Penrose vertex configurations — sun (5 thick rhombs at 72° apex), star (10 thin rhombs at 36° apex), and two 3-rhomb boat configurations (1 thin + 2 thick at 144°/108°/108°, or 2 thin + 1 thick at 144°/144°/72°) — collapsing each into the corresponding P1 prototile cell (pentagon, pentagram star, or hexagonal boat). Unmerged thick rhombs remain as `p1-pentagon` cells (the rhomb-region MLD representative of the pentagonal P1 prototile) and unmerged thin rhombs as `p1-diamond` cells (geometrically exact P1 diamonds). All four P1 prototiles are distributed throughout the patch, with depth-to-cell-count sequence 42 / 107 / 272 / 723 / ... governed by the `1.6 * φ^d` patch radius. Cells are intrinsically gap-free, edge-matched, and connected at every depth.
- `penrose-p1-pentagon-boat-star` is the centered singular-pentagrid Penrose P1 manifestation. It uses the all-zero de Bruijn pentagrid crop so the patch includes the iconic central star and surrounding boat ring from depth 0, and it emits the full `pentagon` / `diamond` / `boat` / `star` vocabulary. Status is `canonical_patch`: the patch is deterministic, gap-free, edge-matched, and validator-clean, but it is still a canonical multigrid patch rather than the literal decorated six-state substitution implementation.
- Periodic mixed families are still verified on finite open-boundary canonical samples rather than larger-sample or quotient-surface proofs. The reference layer now supports per-family periodic sample sizes, but the current audit kept the shipped catalog on `3x3`.
- Periodic dual-family invariants now cover the unambiguous reciprocal pairs plus candidate-class signature checks for the currently ambiguous catalog groups, but they are still finite-sample descriptor checks rather than full dual-construction proofs.
- The reference layer now mixes rooted local-reference anchors with direct canonical patch diffs for `robinson-triangles`, `tuebingen-triangle`, `dodecagonal-square-triangle`, `shield`, and `pinwheel`; it is not yet full canonical patch coverage for every family.
- Several aperiodic families are verified through deterministic low-depth samples, count invariants, adjacency rules, and metadata presence rather than a full symbolic substitution proof.
- Render-space overlap checks still need a looser tolerance than the backend topology-space overlap check; the current frontend helper uses a `1e-4` positive-area threshold plus multi-precision snapped comparison because exact-path families like `pinwheel` are still noisier in adapter space.
- Pinwheel contiguity now uses exact positive-length segment-overlap neighbors on the exact-affine path because the substitution is not edge-to-edge at every subdivision step.

## When To Add An Entry Here

Add a known deviation when:

- the generator is intentionally approximate
- the literature verifier is knowingly weaker than the intended family model
- a family is temporarily kept on a waiver list
- rendering is accepted as a stopgap even though the mathematical generator is not yet canonical

Do not add an entry just because a family uses a finite sample. Finite samples are part of the app’s model and only count as a deviation if they fail to preserve the intended invariants.
