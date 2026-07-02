# Dodecagonal Square-Triangle Generator

This file documents the runtime generator for the public
`dodecagonal-square-triangle` family.

The implementation lives in
`backend/simulation/aperiodic_dodecagonal_square_triangle.py`. There is no
vendored data: the runtime is the Schlottmann marked square-triangle
substitution expressed as an exact symbolic rule table, and it scales to any
requested patch depth.

## Construction

The runtime iterates Schlottmann's quasi-periodic square-triangle pseudo
substitution (Tilings Encyclopedia, `substitution/square-triangle/`):

1. Five marked prototiles: three marked unit equilateral triangles
   (`triangle-red`, `triangle-yellow`, `triangle-blue`) and two marked unit
   squares (`square-plain`, `square-marked`). The linear inflation factor is
   `2 + sqrt(3)`.
2. The substitution is a *pseudo* substitution: supertiles interlock, so
   children on a supertile boundary are emitted by both adjacent supertiles.
   The runtime deduplicates them by exact geometry in the `Z[zeta12]` module
   (integer 4-tuples `a + b*zeta + c*zeta^2 + d*zeta^3`, `zeta = exp(i*pi/6)`),
   and asserts that no two parents ever disagree about a tile's kind.
3. The blue triangle's rule contains a blue-triangle child at the identity
   pose strictly inside its supertile. The runtime anchors the expansion on
   that recurrent slot, so the patch converges around a fixed anchor tile as
   depth grows, cell ids are stable across depths, and subtrees that cannot
   reach the requested BFS ball are pruned for speed.
4. For any requested `patch_depth`, the runtime expands enough substitution
   levels around the anchor, builds edge-sharing adjacency from exact module
   edges, and returns the BFS-cropped subgraph from the square nearest the
   anchor.

## Provenance And Verification

The child placements (101 slots across the five rules) were extracted from
the Tilings Encyclopedia substitution-rule figure by exact-geometry image
analysis, then validated against the encyclopedia's own 4999-cell finite
patch (recoverable from repo history; formerly vendored as
`dodecagonal_square_triangle_literature_source.json`):

- a two-level supertile decomposition of the literature patch matches the
  extracted rules with zero colour conflicts and pins every child's marked
  pose (up to each marking's stabilizer) by intersection over many instances;
- re-expanding the decomposed coarse configuration reproduces the literature
  patch tile-for-tile, marking colours included, across the covered window;
- `sigma^2` supertile patches are exactly gap-free and overlap-free, and
  `sigma^3` expansion from every prototile produces no kind conflicts;
- the triangle:square census converges to the canonical `4/sqrt(3)` and the
  triangle-colour frequencies match the literature patch.

## Public Vocabulary

- `tile_family = "dodecagonal-square-triangle"`
- `dodecagonal-square-triangle-square` — `chirality_token = None` (both marked
  square prototiles collapse to the public square kind, matching the
  literature patch's own colour data)
- `dodecagonal-square-triangle-triangle` — `chirality_token` in
  `{"red", "yellow", "blue"}`, the marking colour of the prototile

## Invariants

At every patch depth the runtime patch must remain:

- deterministic for the same `patch_depth`
- one connected component
- hole-free
- overlap-free
- composed of unit squares and unit equilateral triangles only
- full-edge adjacent rather than point-touching
- stable in ids and cell ordering (shallower patches are id-subsets of deeper
  patches)

## Caveats

- The two marked square prototiles are distinguished internally (they have
  different substitution rules and `square-marked` is chiral) but share the
  public square kind.
- The family remains in the `Experimental` picker group until manual visual
  review accepts the rendered field.
