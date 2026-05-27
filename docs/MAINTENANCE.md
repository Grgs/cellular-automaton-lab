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

## Public Release Process

The first clean public release line started at `v0.1.0` and continues as an ongoing preview series; `v0.4.0` is the current shipped tag. The public release surface is:

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
py -3 -m mypy --config-file mypy.ini
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
8. Tag and publish the GitHub Release from the clean, synced `main` checkout:

```powershell
git tag -a vX.Y.Z origin/main -m "vX.Y.Z preview release"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file docs/releases/vX.Y.Z.md --latest
python -m tools repo release-check --version vX.Y.Z --phase post-publish
```

The post-publish check must pass before considering the release complete. It verifies the local tag, remote tag, GitHub Release, and latest-release pointer.

9. Verify the deployed GitHub Pages demo manually:
   - app loads successfully
   - one simulation run/pause/step flow works
   - one topology or rule switch works
   - one pattern import/export or persistence flow works
   - no obvious startup or console failure appears
10. Keep concise release notes in the matching file in [docs/releases/](releases/) for the target tag and use that file as the `gh release create --notes-file` input (current tags: `v0.1.0`, `v0.2.0`, `v0.3.0`, `v0.4.0`).
11. Tag only after the intended commit has passed the required validation and deploy path. Do not stop at a merged release PR; GitHub does not list a new release until the tag and GitHub Release exist.

Public docs must keep preview status and known limitations explicit. Do not imply package-registry support or long-term API stability before the project actually offers them.

## Python Dependency Pinning

Python dependencies are split into source and lockfile pairs:

- `requirements.in` / `requirements-dev.in`: human-edited direct dependencies with exact-version pins
- `requirements.txt` / `requirements-dev.txt`: autogenerated lockfiles with the full transitive graph pinned

Local setup, CI, and `pre-commit` all install from the `.txt` lockfiles. The `.in` files are the source of truth when adding, removing, or upgrading a direct dependency.

To regenerate the lockfiles after changing a `.in` file:

```powershell
py -3 -m pip install --user pip-tools
py -3 -m piptools compile --strip-extras --output-file=requirements.txt requirements.in
py -3 -m piptools compile --strip-extras --output-file=requirements-dev.txt requirements-dev.in
```

To upgrade a single pinned package, edit the `.in` file and rerun the command above. To upgrade everything, add `--upgrade` to the `piptools compile` invocations.

Lockfiles are generated on the maintainer's local platform. Cross-platform installs work because all current pinned packages publish wheels for both Windows and Linux at the resolved versions, and the only platform-conditional transitive dep (`colorama`, pulled in by `click`) is pure-Python and installs harmlessly on Linux CI.

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
