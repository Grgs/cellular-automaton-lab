# Tiling Diagnosis Tooling Notes

This note captures process findings from one focused tiling-fix attempt where the
goal was not to land a tiling change, but to learn which tools are still missing
for efficient diagnosis.

The example family for this pass was `pinwheel`.

## Example Diagnosis Loop

The concrete loop used in this pass was:

1. Render the current representative sample with the browser-backed review tool:

   ```powershell
   python tools/render_canvas_review.py --profile pinwheel-depth-3
   ```

2. Run the same review path through the managed host runner so startup, cleanup,
   and artifacts are owned by one command:

   ```powershell
   python tools/run_browser_check.py --host standalone --render-review --profile pinwheel-depth-3
   ```

3. Sweep one obvious control manually to see whether the visible result changes:

   ```powershell
   python tools/render_canvas_review.py --family pinwheel --patch-depth 4 --out /tmp/pinwheel-depth-4.png --summary-out /tmp/pinwheel-depth-4.json
   ```

4. Run one targeted browser test through the managed host:

   ```powershell
   python tools/run_browser_check.py --host standalone --unittest tests.e2e.playwright_case_suite.StandaloneCellularAutomatonUITests.test_pinwheel_topology_switch_renders_aperiodic_patch
   ```

5. Inspect the family builder and reference spec to locate the likely fix
   boundary:
   - runtime patch builder: `backend/simulation/aperiodic_pinwheel.py`
   - source-backed expectations: `backend/simulation/reference_specs/aperiodic.py`

## Findings From The Example Pass

### 1. Success-path artifacts are now available, but comparison loops still need orchestration

The managed runner now supports `--success-artifacts` for successful
`--unittest` runs, and managed `--render-review` runs already keep their PNG and
JSON output inside the run artifact directory.

That closes the earlier “passing runs are too thin” gap. The remaining friction
is not basic preservation, but comparing several preserved runs coherently.

### 2. Render-review summaries do not yet expose enough visual-quality signals

For `pinwheel`, the current summary reported:

- full viewport coverage
- one dominant fill color
- a render cell size

That is enough for rough occupancy checks, but not enough to answer the actual
question: does the rendered pattern look like the intended literature sample?

The current summary says almost nothing about:

- orientation diversity in the visible field
- boundary dominance
- rectangularity vs isotropy of the visible patch
- whether the visual field changed meaningfully across parameter changes

### 3. There is no backend/frontend consistency report in the diagnosis loop

This pass found a concrete mismatch candidate:

- backend topology build:
  - depth 3: `250` cells
  - depth 4: `1250` cells
- render-review summaries:
  - depth 3: `Depth 3 • 600 tiles`
  - depth 4: `Depth 4 • 600 tiles`

That does not prove a bug on its own, but the current tooling does not explain
the discrepancy. The review flow should surface:

- backend topology cell count
- frontend grid summary text
- any adapter/render-side cell count or visible-polygon count

Without that cross-check, it is too easy to spend time chasing a visual problem
when the current review output may already be masking a count or state mismatch.

### 4. Manual parameter sweeps are still awkward

Trying `pinwheel` at depth 3 and depth 4 required:

- manual command edits
- manual output paths
- manual comparison of two JSON files

The current tools are good for a single review, but not for a short experiment
loop where multiple depths, themes, or host modes need to be compared.

### 5. Review profiles still stop short of being full diagnosis bundles

Profiles already encode the family/depth/viewport/theme. They do not yet encode:

- a canonical local reference image path
- expected review assertions for the sample
- preferred host mode
- any family-specific notes about what visual property is under review

That means every serious visual review still depends on extra operator memory.

## Tooling Backlog

### High Priority

1. Render-review consistency report
   - Status: landed.
   - The render-review summary now records:
     - backend topology cell count and dimensions when a live backend client exists
     - browser-state topology facts from a read-only diagnostics hook
     - frontend grid summary text and parsed expectations
   - The tool now warns when those layers disagree in suspicious ways, but does not fail the review command by default.

2. Success-path artifact bundle option
   - Status: landed.
   - Managed `--render-review` runs now keep PNG/JSON artifacts in the run
     directory by default.
   - Managed `--unittest --success-artifacts` runs can now preserve:
     - `canvas.png`
     - `page.png`
     - `render-summary.json`

3. Review sweep tool
   - Status: landed.
   - The sweep tool now runs a profile across a small matrix such as:
     - patch depths
     - host kinds
     - themes
   - It emits one top-level sweep manifest plus one directory tree of comparable
     PNG/JSON pairs.

### Medium Priority

4. Profile-attached references and review notes
   - Status: landed with a metadata-first copyright boundary.
   - Render-review profiles now carry:
     - citation labels
     - source URLs
     - short review notes
     - a default cache filename for an operator-provided local reference image
   - The repo does not ship literature images; the local cache under
     `output/literature-reference-cache/` is the convenience layer.

5. Visual-quality metrics beyond occupancy
   - Add metrics oriented toward diagnosis rather than smoke checking, such as:
     - orientation-token diversity for visible cells
     - bounding-box aspect ratio of the visible field
     - simple edge-density or boundary-dominance measures

6. Trial manifest / diagnosis journal
   - When running an experiment loop, emit one summary file that records:
     - commands used
     - outputs generated
     - key metrics
     - operator notes

### Lower Priority

7. One-command side-by-side diff review
   - Build on the existing montage support so the tool can emit one HTML or image
     sheet for a set of runs rather than only one rendered image vs one reference.

8. Optional browser-test success snapshots
   - Preserve a final settled screenshot for targeted browser tests when requested,
     not only on failure.

## Conclusion

The current tooling is good enough to run a diagnosis loop without stale
processes. The remaining problem is observability quality, not command
orchestration.

For the `pinwheel` example, the consistency-report layer is now the primary
cross-check, the sweep tool is now the primary comparison path, and
literature-review mode now makes profile-based citation and montage workflows
repeatable without checking reference images into git. The next tooling
investment should be richer visual-quality metrics and more structured review
expectations, not more host/process orchestration.
