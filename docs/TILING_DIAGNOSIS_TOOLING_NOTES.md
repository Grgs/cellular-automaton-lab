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

5. Artifact-readiness settle detection
   - Status: landed.
   - Render-review capture no longer treats “overlay hidden” as a sufficient
     settle gate.
   - The browser harness now waits for a stable readiness tuple that includes:
     - cleared blocking activity from controller state
     - non-placeholder `gridSizeText`
     - non-empty `generationText`
     - stable topology revision, cell count, and render cell size across three
       polls
   - Summaries and manifests now carry `settleDiagnostics` so a captured image
     can be tied back to the final readiness snapshot.
   - The motivating failure case was a dark standalone `shield` run that
     captured `Building tiling...` even though the command completed.

6. Visual-quality metrics beyond occupancy
   - Status: landed for the first advisory slice.
   - Render-review payloads now include:
     - visible occupied-field aspect ratio
     - edge density
     - boundary dominance
     - gutter score
     - orientation diversity when orientation tokens are present
     - 12-sector occupancy and radial-symmetry score when render diagnostics
       expose aggregate center/sector inputs
   - These metrics are advisory only; they do not yet introduce thresholds or
     pass/fail gates.

7. Trial manifest / diagnosis journal
   - When running an experiment loop, emit one summary file that records:
     - commands used
     - outputs generated
     - key metrics
     - operator notes

### Lower Priority

8. One-command side-by-side diff review
   - Build on the existing montage support so the tool can emit one HTML or image
     sheet for a set of runs rather than only one rendered image vs one reference.

9. Optional browser-test success snapshots
   - Preserve a final settled screenshot for targeted browser tests when requested,
     not only on failure.

## Conclusion

The current tooling is good enough to run a diagnosis loop without stale
processes. The remaining problem is observability quality, not command
orchestration.

For the `pinwheel` example, the consistency-report layer is now the primary
cross-check, the sweep tool is now the primary comparison path, the family
sample workbench is now the primary structural candidate-exploration path, and
literature-review mode now makes profile-based citation and montage workflows
repeatable without checking reference images into git. The next tooling
investment should be geometry-cleanup exploration and stronger profile-owned
review expectations, not more host/process orchestration.

## Shield Pass Gaps

The later `shield` pass exposed a different class of diagnosis problem: the
tooling was good enough to preserve artifacts and compare runs, but still weak
at explaining where the visible distortion came from or how to search for a
better representative sample efficiently.

### 1. Backend-to-frontend transform visibility is weak

The shield pass had visible shape changes coming from more than one layer:

- backend trace-gap compensation in the image-derived geometry
- frontend shield-only polygon shrink and framing normalization

That split had to be reconstructed by reading code in both the backend builder
and the frontend adapter. There is still no diagnostic report that shows, for
one family, the topology-space polygon, backend-normalized polygon, and final
render-space polygon side by side.

Status: partially landed for the first slice. The browser diagnostics path now
records topology-space bounds, render metrics, and stable sample-cell
transforms from the live frontend adapter path. Deeper backend-vs-source
transform breakdowns are still deferred.

### 2. Candidate-sample exploration is too manual

Switching shield away from graph-distance cropping required trying multiple
center-window rules and thresholds, then checking:

- selected cell count
- connected-component count
- hole behavior
- visible bounds and aspect

That exploration was still done with one-off probes and manual readback. There
is no family sample workbench that can sweep candidate windows and summarize the
structural consequences directly.

Status: landed for the structural-first slice. The family sample workbench now:

- builds shipped baseline candidates for any patch-depth family
- sweeps `shield` representative-window thresholds as first-class candidates
- emits structural summaries with count, connectivity, holes, bounds, and
  explicit validation diagnostics
- can optionally run browser-backed review against injected candidate topology
  payloads rather than only the shipped family/depth sample

The remaining gap is narrower. Candidate window exploration is now first-class;
the next missing tool is a geometry-cleanup workbench for small topology-space
cleanup factors.

### 3. Standalone build freshness is still too easy to misread

During shield acceptance, server and standalone temporarily disagreed:

- server reflected the rebuilt representative sample at `40 / 81 / 443`
- standalone was still rendering the older `36 / 80 / 444` bundle

The consistency-report tooling exposed the mismatch, but it did not identify an
out-of-date standalone build as the likely cause. Build provenance needs to be
visible in review manifests if those discrepancies are going to be actionable
quickly.

Status: landed for the first slice. Render-review summaries and manifests now
carry runtime provenance, and standalone builds now emit a build manifest that
can be compared to the current checkout.

The same shield work also exposed a second harness problem: the old settle gate
could still capture an intermediate loading frame after the overlay briefly
cleared. That artifact-readiness gap is now closed. The render-review harness
waits for a stable readiness tuple and records `settleDiagnostics` in summaries
and manifests, so future visual diagnosis should build on that stronger gate
rather than falling back to DOM-only heuristics.

### 4. Visual-quality metrics are too thin for centered dense fields

The shield review question was not just “did it render?” It was whether the
field read like a balanced central 12-fold patch without obvious gutters or
lopsided boundary dominance.

Current review metrics still say very little about:

- radial symmetry
- angular-sector occupancy
- empty-space or gutter intensity
- boundary dominance around the visible field

Status: partially landed. Render-review now emits advisory visual metrics for
boundary dominance, gutter score, orientation diversity, 12-sector occupancy,
and radial symmetry. The remaining gap is not the presence of metrics, but the
lack of family-owned thresholds, expectations, and workbench-style exploration
for candidate representative samples.

### 5. Render-space overlap tooling is too binary for image-derived families

Shield is still a traced, compensated family rather than an exact edge-sharing
substitution. The existing overlap tooling is strongest when the correct answer
is simply “no positive-area overlap anywhere.”

For shield, that is not the full story. The pass required manually treating it
as a relaxed family and interpreting overlap results in that context. The
tooling still lacks family-specific overlap policies that explain what kind of
contact or compensation is acceptable.

The current overlap helper also stops short of being a diagnosis tool. In the
latest shield pass, the existing fixture test confirmed that overlap existed,
but did not report:

- how many representative cells were involved
- which kind pairs dominated the overlap set
- whether the overlap areas were epsilon-scale noise or large structural
  intrusions
- whether the same cell ids already surfaced by the render transform report
  were part of the overlap hotspots

Using the current tooling required a temporary debug test to extract that data.
That run showed:

- at least 200 positive-area overlaps in the first capped sample over 443
  representative cells
- large overlap areas, including values around `2e5`, which rules out a simple
  epsilon/tolerance story
- the dominant overlap classes were triangle/triangle, square/triangle, and
  shield/triangle
- transform-report sample ids such as `shield:ref:1378` and `shield:ref:1400`
  were already part of the overlap set, but the tooling did not connect those
  views automatically

Status: landed in a later slice. Render review, managed browser checks, and
sweeps now emit `overlapHotspots` with pair summaries, dominant kind pairs,
transform-sample hits, and family-aware policy labeling.

The current remaining gap is narrower: overlap diagnosis is now good enough to
show where the problem is, but geometry cleanup is still exploratory work. The
shield overlap fix ended up needing:

- a minimal topology-space inward trace cleanup to remove the remaining
  positive-area intersections from the shipped geometry
- a draw-only seam bridge so visual gap hiding stays out of the geometry cache

That cleanup choice was still selected with an ad hoc Shapely sweep over scale
factors rather than a first-class workbench. The missing follow-up tool is a
geometry-cleanup workbench that can report overlap count, max overlap area,
bounds drift, and likely gutter risk for small cleanup factors without a custom
one-off script.

### 6. Frontend representative fixture regeneration is still ad hoc

Backend reference fixtures have first-class regeneration and verification paths.
The frontend representative shield fixture did not.

Updating the frontend sample still depended on an ad hoc export step rather than
one canonical regeneration command. That is avoidable process debt for every
family that needs browser-visible sample refreshes.

### 7. Literature-review mode still lacks family-specific acceptance prompts

The literature workflow now preserves citations, notes, and local-cache support,
but if the cache image is missing the tool mostly warns and continues.

That is correct behavior, but it leaves too much operator memory in the loop.
For shield specifically, the missing tool is a short profile-owned checklist for
what to inspect even when the local literature image is absent, such as central
symmetry, odd-depth rotation plausibility, and visible gutter severity.
