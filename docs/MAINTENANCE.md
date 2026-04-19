# Maintenance Guide

This repo now has enough moving parts that maintenance guidance needs one home. Use this document for repo hygiene, guardrails, and “which doc owns what” decisions.

## Doc Ownership

- `README.md`: product overview, local setup, and the public command surface
- `docs/ARCHITECTURE.md`: runtime boundaries and subsystem ownership
- `docs/CODE_MAP.md`: navigation for specific files and call paths
- `docs/TESTING.md`: test strategy, failure classes, and browser-support details
- `docs/CODE_QUALITY_ROADMAP.md`: structural pressure points and refactor priorities
- `TODO.md`: concrete remaining work after the current cleanup passes

If a note is only about hygiene, guardrails, or how to maintain the repo, put it here instead of growing another planning document.

## Guardrails

Frontend checks:

```powershell
npm run lint:frontend
npm run format:frontend:check
```

Python checks:

```powershell
npm run lint:python
npm run format:python:check
npm run check:python
```

These Python checks are intentionally incremental for now. They cover the backend bootstrap payload slice plus the `tools/render_review/` package and its direct tests and entrypoints. Wider `ruff` adoption is still blocked by older compatibility facades that rely on import-for-export patterns and `sys.path` bootstrap shims.

Pre-commit mirrors the same incremental Python scope plus the frontend formatting check, so local hooks and scripted runs exercise the same rules.

## Tooling Ownership

Browser diagnosis and workbench implementation now lives under `tools/render_review/`:

- `review.py`
- `browser_check.py`
- `sweep.py`
- `workbench_support.py`
- `family_sample_workbench.py`
- `geometry_cleanup_workbench.py`
- `profiles.py`

The top-level files in `tools/` are now CLI entrypoints only:

- `tools/render_canvas_review.py`
- `tools/run_browser_check.py`
- `tools/run_render_review_sweep.py`
- `tools/run_family_sample_workbench.py`
- `tools/run_geometry_cleanup_workbench.py`

When adding shared render-review or workbench logic, put it in `tools/render_review/` and keep the top-level commands thin.
