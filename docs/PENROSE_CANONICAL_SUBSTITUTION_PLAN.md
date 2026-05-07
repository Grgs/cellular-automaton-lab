# Plan: Canonical Penrose Substitution Rewrite

This document scopes the future fix for the non-canonical Penrose substitution
shared by `penrose-p2-kite-dart`, `penrose-p3-rhombs`, `penrose-p3-rhombs-vertex`,
and `robinson-triangles`. Background on the deviation is in
[TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md).

## Why the current implementations diverge

All four families ultimately stem from the canonical Robinson half-tile
deflation:

- Acute (golden gnomon, 36-72-72): A → 2A + 1B at scale 1/phi.
- Obtuse (golden gnomon, 108-36-36): B → 1A + 1B at scale 1/phi.
- Substitution matrix `[[2,1],[1,1]]`, leading eigenvalue `phi^2 ≈ 2.618`.

Two acute halves of opposite chirality glue along a long edge to form a kite;
two obtuse halves of opposite chirality glue along a short edge to form a dart.
A thick rhomb (P3) is two acute halves; a thin rhomb is two obtuse halves —
same gluing rules, different shape labels.

Starting from the canonical sun seed (5 kites with their 72° tips meeting at
the origin), each substitution step produces:

- Per parent kite: 1 sub-dart (interior, paired) + 1 sub-kite (interior, paired)
  + **2 unpaired half-acutes** sitting on the parent's two short edges.
- The unpaired halves on a kite's short edges live on the **outer boundary of
  the sun**, which has no neighbouring tile to pair with. They cannot be emitted
  as full kites/darts.

The current Python builders sidestep the boundary problem by using a different,
non-canonical full-tile substitution that always emits only full tiles. The
trade-off is the wrong eigenvalue and depth-to-cell-count sequence (see
TILING_KNOWN_DEVIATIONS.md for the actual numbers).

## Required canonical sequences

Starting from the canonical seeds, the canonical depth-to-cell-count
expectations are:

| family               | seed       | d=0 | d=1 | d=2 | d=3 | leading eigenvalue |
|----------------------|------------|-----|-----|-----|-----|--------------------|
| penrose-p2-kite-dart | 5 kites    |   5 |  15 |  40 | 105 | phi^2 ≈ 2.618      |
| penrose-p3-rhombs    | 5 thicks   |   5 |  15 |  40 | 105 | phi^2 ≈ 2.618      |
| robinson-triangles   | 10 acutes  |  10 |  30 |  80 | 210 | phi^2 ≈ 2.618      |

The current in-house sequences (5/20/70/240, 5/10/24/66, 10/40/140/480) need to
be replaced with these.

## Implementation options

### Option 1 — Crop-and-grow

Run the canonical half-tile substitution at depth `d+1` starting from a wider
seed, then crop the result to keep only the cells fully contained in the area
of the original sun. The crop deletes the boundary unpaired halves; what
remains is fully paired.

Pros:
- Reuses the canonical substitution rule directly; no new tile kind.
- Smallest deviation from the existing builder shape.
- Output cells at fixed scale 1 (boundary-cropped sun); no API change for
  consumers.

Cons:
- Patch shrinks slightly with each step (the cropped boundary moves inward).
  That changes the depth-to-cell-count sequence away from
  `[[2,1],[1,1]]^d * seed` and needs new reference numbers derived from a
  reference run.
- Need to define the crop region precisely (e.g. "tiles whose centroid lies
  inside the original sun" vs "tiles whose vertices all lie inside"). Two
  natural choices give slightly different counts.
- Boundary cells lose their kite/dart pairing partner because that partner
  was outside the crop. So the crop must also drop any tile whose pair was
  cropped. This is more involved than a simple bounding-box filter.

### Option 2 — Emit half-tiles directly

Internally substitute Robinson half-tiles (acute / obtuse), pair what can be
paired into full kites/darts, and emit the unpaired boundary halves as their
own cell kind (e.g. `kite-half-acute`, `dart-half-obtuse`).

Pros:
- Canonical eigenvalue everywhere; depth-to-cell-count matches Bielefeld.
- The patch fills its full sun extent — no shrinkage.
- Robinson Triangles becomes a first-class direct substitution, not a
  derived split of P2.

Cons:
- New cell kinds across the catalog: `public_cell_kinds` for P2, P3, and the
  vertex variant grow from 2 to 4. Picker palettes, fill indices, frontend
  renderers, and rule defaults all need entries for the new kinds.
- All canonical patch fixtures and frontend topology fixtures regenerate.
- Reference specs need new `expected_kind_counts` per depth.
- Behavioural change for end users: kites/darts at the patch boundary are
  visibly halved; this needs a UX note or a fade-out treatment.

### Recommendation

For the smallest user-visible change, prefer **Option 1**. For the cleanest
mathematical alignment with Bielefeld and the most useful Robinson
implementation, prefer **Option 2**. The author's preference is Option 2 if we
are willing to take the UX hit on boundary tiles, because it also fixes
`robinson-triangles` properly (currently `robinson-triangles` is just a
post-hoc split of P2, which is itself non-canonical).

## Scope of the change (either option)

Files that need to be touched:

- `backend/simulation/aperiodic_penrose_p2.py` — rewrite the builder.
- `backend/simulation/aperiodic_robinson_triangles.py` — either rewrite as a
  direct half-tile substitution (Option 2), or update to consume the new
  canonical P2 (Option 1).
- The P3 builder (search for `_penrose_p3` or the rhomb builder used by
  `PENROSE_GEOMETRY` / `PENROSE_VERTEX_GEOMETRY`) — analogous rewrite.
- `backend/simulation/reference_specs/aperiodic.py` — replace
  `exact_total_cells` and `expected_kind_counts` for all four families;
  remove the `notes=` deviation paragraphs added during the documentation
  pass; remove the `promotion_blocker` once verification passes against the
  new numbers.
- `backend/simulation/aperiodic_family_manifest.py` — clear
  `promotion_blocker` and switch `implementation_status` back to
  `true_substitution` for all four families.
- `backend/simulation/data/reference_patch_canonical_fixtures.json` —
  regenerate the `robinson-triangles` `exact-depth-1` and `exact-depth-3`
  fixtures using `tools/regenerate_reference_fixtures.py`.
- `frontend/test-fixtures/topologies/robinson-triangles-depth-3.json` and
  `frontend/test-fixtures/topologies/fixture-manifest.json` — regenerate the
  frontend Robinson fixture using
  `tools/regenerate_frontend_topology_fixtures.py`. Bump
  `topologyRevision` accordingly.
- `frontend/test-fixtures/bootstrap-data.json` — regenerate via
  `tools/export_bootstrap_data.py`.
- `frontend/controls/tiling-preview-data.ts` — refresh the Penrose / Robinson
  thumbnails using `tools/generate_tiling_preview.py`.
- For Option 2 only: `frontend/canvas/family-dead-palette-manifest.json`,
  any palette manifests under `frontend/canvas/`, and any picker swatch
  metadata that lists kite/dart kinds.

Tests that lock in the current (non-canonical) numbers:

- `tests/unit/test_literature_reference_verification.py` — depth assertions
  (`depth-3 = 240` for P2, `480` for Robinson, `66` for P3) need to move to
  the canonical values.
- `tests/unit/test_literature_reference_verification_aperiodic.py` —
  `canonical-patch-fixture-mismatch` and depth-3 assertions for Robinson.
- `tests/unit/test_aperiodic_registry.py` — Robinson depth-3 patch
  comparison; the count and ID stream change.
- `tests/unit/test_report_tiling_verification_strength_tool.py` — the
  `known_deviation` assertion for `robinson-triangles` reverts to
  `true_substitution` and the `promotion_blocker` is back to `None`.
- `tests/unit/test_aperiodic_family_contracts.py` — implementation_status
  contracts.
- `tests/api/test_api_state_and_rules.py` — any default-rule or
  `maximum_patch_depth_for_tiling_family` assertions that depend on cell
  counts.

Validation tools to re-run:

```powershell
py -3 tools\validate_tilings.py
py -3 tools\verify_reference_tilings.py
npm run fixtures:reference:check
py -3 -m unittest discover -s tests
npm run test:frontend
npm run test:e2e:playwright:server
```

## Acceptance criteria

The fix is done when, in a single coherent change:

- `verify_reference_tilings.py` passes on canonical depth counts:
  `5/15/40/105` for P2 and P3, `10/30/80/210` for Robinson Triangles, with
  the relevant Bielefeld URLs as the cited sources.
- `implementation_status` for all four families is `true_substitution` and
  `promotion_blocker` is `None` again.
- The `notes=` deviation paragraphs added during the documentation pass are
  removed.
- The substitution matrix the implementation actually realises is
  `[[2,1],[1,1]]` (eigenvalue `phi^2`), confirmed by computing depth ratios.
- All Penrose / Robinson canonical patch fixtures, frontend topology
  fixtures, picker thumbnails, and bootstrap data are regenerated and
  reviewed.
- `TILING_KNOWN_DEVIATIONS.md` no longer lists Penrose / Robinson.
