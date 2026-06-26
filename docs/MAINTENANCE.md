# Maintenance Guide

This repo now has enough moving parts that maintenance guidance needs one home. Use this document for repo hygiene, guardrails, and “which doc owns what” decisions.

## Doc Ownership

- `README.md`: product overview, local setup, and the public command surface
- `CONTRIBUTING.md`: contributor setup, common workflow, and contribution expectations
- `SECURITY.md`: vulnerability-reporting expectations and security guardrail pointers
- `docs/ADDING_RULES.md`, `docs/ADDING_TOPOLOGIES.md`, `docs/ADDING_PRESETS_AND_PATTERNS.md`, `docs/TESTING_CHANGES.md`: task guides for contributors adding app behavior
- `docs/ARCHITECTURE.md`: runtime boundaries and subsystem ownership
- `docs/CODE_MAP.md`: navigation for specific files and call paths
- `docs/TESTING.md`: test strategy, failure classes, and browser-support details
- `docs/TOOLS.md`: single index of every script under `tools/`
- `docs/CODE_QUALITY_ROADMAP.md`: structural pressure points and refactor priorities
- `TODO.md`: concrete remaining work after the current cleanup passes
- `CHANGELOG.md`: curated narrative changelog of completed work
- `.github/ISSUE_TEMPLATE/` and `.github/PULL_REQUEST_TEMPLATE.md`: lightweight public contribution forms

If a note is only about hygiene, guardrails, or how to maintain the repo, put it here instead of growing another planning document.

## Guardrails

Frontend checks:

```powershell
npm run lint:frontend
npm run lint:frontend:eslint
npm run format:frontend
npm run format:frontend:check
```

Python checks:

```powershell
npm run lint:python
npm run format:python:check
npm run check:python
```

Python linting and formatting now cover the full repo-owned Python surface:

- `app.py`
- `backend/`
- `tests/`
- `tools/`

Pre-commit mirrors the same Python scope plus the frontend lint/format check, so local hooks and scripted runs exercise the same rules.

### Shell Pipelines Must Not Hide Failures

Any multi-line shell step that pipes a command whose exit code matters (`pytest ... | tee`, `tool | tail`, `coverage report --fail-under=N | tee`) must run under `pipefail`, or the failure is masked by the last stage of the pipe and the step passes green. Start such CI `run:` blocks with `set -o pipefail` (or set the step's `shell: bash`, which GitHub invokes with `-o pipefail`); apply the same rule in repo-owned `tools/` shell. This has bitten the coverage gate and the tiling-verify sweep before — a green step that was actually failing. When in doubt, prefer not piping the command whose status you care about.

## Public Release Process

The first clean public release line started at `v0.1.0` and continues as an ongoing preview series; `v0.5.0` is the current shipped tag. The public release surface is:

- a tagged GitHub source release
- the GitHub Pages standalone demo
- the repository checkout for local use

This repo does not publish npm or PyPI packages in the preview line.

Before cutting a public release:

1. Resolve or explicitly exclude in-flight work from the intended release commit.
2. Ensure the release candidate lives on a dedicated release branch rather than an actively changing local checkout.
3. Require a clean git tree before tagging. Do not tag from a dirty working tree.
4. Rebuild `static/dist/` and `output/standalone/` from the exact release commit so standalone provenance is fresh.
5. Run the release-confidence validation sweep on that same commit:

```powershell
npm run typecheck:frontend
npm run build:frontend
npm run test:frontend
npm run build:frontend:standalone
npm run smoke:standalone
npm run check:doc-links
npm run audit:supply-chain
py -3 -m mypy --config-file pyproject.toml
py -3 -m unittest discover -s tests -p "test_*.py"
python -m tools tilings validate
python -m tools tilings verify
py -3 -m pre_commit run --hook-stage pre-push --all-files
```

6. Merge the release-candidate PR into `main`, then fetch and fast-forward local `main` to the merged commit:

```powershell
git fetch origin --prune --tags
git switch main
git pull --ff-only
python -m tools repo release-check --version vX.Y.Z --phase pre-publish
```

The pre-publish check must pass before tagging. It intentionally expects the target tag and GitHub Release to be absent.

7. Require GitHub Actions CI to pass on the exact release commit, including the Pages build path.
8. Tag from the clean, synced `main` checkout and push the tag:

```powershell
git tag -a vX.Y.Z origin/main -m "vX.Y.Z preview release"
git push origin vX.Y.Z
```

Pushing the tag triggers the [Release workflow](../.github/workflows/release.yml). It validates the release prerequisites (release-notes file, version present in release-facing docs, tag commit contained in `main`), rebuilds `static/dist/` and `output/standalone/` from the tagged commit, checks the bundle-size budget, smoke-tests the standalone bundle in a real browser, and publishes the GitHub Release using `docs/releases/vX.Y.Z.md` as the notes, with the standalone bundle zip attached and the latest-release pointer updated. If the GitHub Release already exists (for example after a manual `gh release create`), the workflow only uploads the bundle asset.

After the workflow completes, verify publication:

```powershell
python -m tools repo release-check --version vX.Y.Z --phase post-publish
```

The post-publish check must pass before considering the release complete. It verifies the local tag, remote tag, GitHub Release, and latest-release pointer.

9. Verify the deployed GitHub Pages demo manually:
   - app loads successfully
   - one simulation run/pause/step flow works
   - one topology or rule switch works
   - one pattern import/export or persistence flow works
   - no obvious startup or console failure appears
10. Keep concise release notes in the matching file in [docs/releases/](releases/) for the target tag; the Release workflow uses that file as the GitHub Release notes (current tags: `v0.1.0`, `v0.2.0`, `v0.3.0`, `v0.4.0`, `v0.5.0`).
11. Tag only after the intended commit has passed the required validation and deploy path. Do not stop at a merged release PR; GitHub does not list a new release until the tag and GitHub Release exist.

Public docs must keep preview status and known limitations explicit. Do not imply package-registry support or long-term API stability before the project actually offers them.

## Python Dependency Pinning

Python dependencies are split into source and lockfile pairs:

- `requirements.in` / `requirements-dev.in`: human-edited direct dependencies with exact-version pins
- `requirements.txt` / `requirements-dev.txt`: autogenerated lockfiles with the full transitive graph pinned and per-file hashes

Local setup, CI, and `pre-commit` all install from the `.txt` lockfiles. The `.in` files are the source of truth when adding, removing, or upgrading a direct dependency. The lockfiles carry `--hash` entries for every pinned file, so pip verifies download integrity on install and refuses anything that is not pinned in the lockfile.

To regenerate the lockfiles after changing a `.in` file:

```powershell
py -3 -m pip install --user pip-tools
py -3 -m piptools compile --strip-extras --generate-hashes --allow-unsafe --output-file=requirements.txt requirements.in
py -3 -m piptools compile --strip-extras --generate-hashes --allow-unsafe --output-file=requirements-dev.txt requirements-dev.in
```

`--allow-unsafe` is required with hashes because `pip-audit` depends on `pip` itself, and hash mode needs every requirement pinned. Do not hand-edit the `.txt` files; in hash mode a single unpinned or unhashed entry makes the whole install fail.

To upgrade a single pinned package, edit the `.in` file and rerun the command above. To upgrade everything, add `--upgrade` to the `piptools compile` invocations.

Lockfiles are generated on the maintainer's local platform. Cross-platform installs work because `--generate-hashes` records hashes for every published file of a pinned version (all platform wheels plus the sdist), and the only platform-conditional transitive dep (`colorama`, pulled in by `click`) is pure-Python and installs harmlessly on Linux CI.

## Promoting Or Demoting A Tiling Family

Moving an aperiodic family between the `Experimental` and `Aperiodic` picker groups touches more surfaces than the manifest. Each was a separate CI failure or missed edit during the `pinwheel` promotion; change them together.

**Before promoting, prove faithfulness against an independent reference.** Automated gates (canonical-patch fixtures, counts, areas, adjacency) are generated from the same builder, so they confirm self-consistency, not correctness. Compare the rendered patch against the published source image/spec, or assert a falsifiable numeric criterion. For substitution tilings whose tiles must stay similar to a prototile, add `expected_triangle_side_ratios` to the family's reference spec so per-tile congruence is machine-enforced — this is what caught the `pinwheel` subdivision shear that every other gate passed.

Edit set:

- **Manifest** — [`backend/simulation/aperiodic_family_manifest.py`](../backend/simulation/aperiodic_family_manifest.py): flip `picker_group`, add or remove `promotion_blocker`, and set `polygon_surface_check=False` if the substitution is non-edge-to-edge (T-junctions split Shapely's polygon union even when the adjacency graph is sound).
- **Bootstrap fixture** — regenerate, do not hand-edit: `python -m tools bootstrap export frontend/test-fixtures/bootstrap-data.json`.
- **Backend tests** — [`test_geometry_manifest.py`](../tests/unit/test_geometry_manifest.py) (picker-group grouping), [`test_aperiodic_registry.py`](../tests/unit/test_aperiodic_registry.py) (promotion-blocker presence), [`test_report_tiling_verification_strength_tool.py`](../tests/unit/test_report_tiling_verification_strength_tool.py) (strength tags **and** the per-family `promotion_blocker:` block — easy to miss, since waiving a check also drops its strength tag), and [`test_api_bootstrap.py`](../tests/api/test_api_bootstrap.py).
- **Frontend tests** — [`aperiodic-family-registry.test.ts`](../frontend/aperiodic-family-registry.test.ts) (`isExperimentalAperiodicFamily`, status tone, blocker text) and [`controls-model/drawer.test.ts`](../frontend/controls-model/drawer.test.ts) (experimental blocker text). Use a still-experimental family as the example so these don't churn on every promotion.
- **Docs** — `docs/TILING_VERIFICATION_STATUS.md`, `docs/TILING_KNOWN_DEVIATIONS.md`, `README.md` preview-limitations, `TODO.md`, `docs/CODE_QUALITY_ROADMAP.md`, and `CHANGELOG.md`.

Then run `python -m tools repo generated-check`, `python -m tools tilings validate`, `python -m tools tilings verify`, the backend and frontend test suites, and a live picker check that the family appears in the intended group. The Windows CI job has caught stale fixtures and platform-specific surface-check differences that Linux-only local runs missed — do not treat a green local Linux run as sufficient for a manifest change.

## Generated File Freshness

Generated repo-owned files should be checked through the umbrella freshness command before review when a change touches CLI metadata, bootstrap data, topology fixtures, or reference fixtures:

```powershell
python -m tools repo generated-check
```

The command combines the focused freshness checks for `docs/TOOLS.md`, `frontend/test-fixtures/bootstrap-data.json`, frontend topology fixtures, the per-fixture frontend size ceiling, and literature reference fixtures. The size guard (`frontend-fixture-size`, also enforced by `python -m tools fixtures frontend --all --check`) fails when any checked-in frontend topology fixture exceeds `DEFAULT_MAX_FIXTURE_BYTES` (4 MB); shrink the fixture's depth/crop or intentionally raise the ceiling. Keep the focused commands available for targeted refresh work, but prefer the umbrella command when preparing maintenance or release-oriented changes.

## Tooling Ownership

Browser diagnosis and workbench implementation now lives under `tools/render_review/`:

- `review.py`
- `browser_check.py`
- `sweep.py`
- `diff_review.py`
- `workbench_support.py`
- `family_sample_workbench.py`
- `geometry_cleanup_workbench.py`
- `profiles.py`

The public tooling surface now lives under the unified Python CLI:

- `python -m tools browser review`
- `python -m tools browser check`
- `python -m tools browser sweep`
- `python -m tools browser diff`
- `python -m tools browser workbench-samples`
- `python -m tools browser workbench-cleanup`

When adding shared render-review or workbench logic, put it in `tools/render_review/`. When adding user-facing command wiring, put it in `tools/commands/browser.py` so the public surface stays centralized under `python -m tools ...`.
