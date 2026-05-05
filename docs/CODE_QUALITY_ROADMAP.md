# Code Quality Roadmap

This document tracks the current structural work that would most improve long-term maintainability. Completed cleanup belongs in [CHANGELOG.md](../CHANGELOG.md), while concrete product and release follow-up lives in [TODO.md](../TODO.md).

## Current State

The app now has clear runtime boundaries:

- backend simulation state is authoritative
- frontend mutations are explicit
- topology catalog data is bootstrapped into the frontend
- server and standalone hosts share the same UI shell
- validation and literature verification are separate concepts
- interaction behavior is covered by unit tests and browser tests

Recent cleanup also split several former pressure points:

- pointer gestures now flow through explicit session modules
- canvas transient overlays have their own state and renderer
- drawer sections are built through section-owned model builders
- aperiodic implementation contracts are surfaced through backend-owned metadata
- literature-reference specs and verification are split into focused packages
- shared polygon adapter behavior lives in one frontend path
- backend/frontend payload drift is guarded by contract tests
- Playwright suite selection is centralized through the npm runner

## Cleanup Principles

- Keep state ownership explicit. Backend simulation state, frontend app state, and view-local canvas state should not blur together.
- Preserve plan/runtime splits. Pure planning code should remain testable without DOM, canvas, Flask, workers, or timers.
- Prefer small subsystem-owned constants and helpers over global configuration dumps.
- Do not hide mathematically weak tiling implementations behind stronger UI or verification wording.
- Browser tests should validate browser behavior only. Logic that can be proven in unit/API tests should stay out of Playwright.
- Every new interaction mode should flow through the gesture-session model.

## Active Priorities

### 1. Drawer Growth Control

The drawer composition is currently healthy: `frontend/controls-model/drawer.ts` composes section-owned builders, and right-click metadata lives in `frontend/controls-model/selection-inspector.ts`.

Next action:

- Split any new large drawer section into its own `frontend/controls-model/drawer-*.ts` builder instead of growing `drawer.ts`.
- Keep section tests local to the section model when possible.

### 2. Python Lint And Format Coverage

Python linting is still intentionally incremental. The guarded slice covers bootstrap/payload contracts, reference verification, render-review tooling, and related tests.

Next action:

- Expand `tools/run_python_style.py` only after the next target modules no longer rely on compatibility-heavy import-for-export patterns or `sys.path` bootstrap shims.
- Prefer widening the guarded slice in small, reviewable batches.

### 3. Aperiodic Implementation Status

The repo now exposes per-family implementation contracts, but some family status remains intentionally provisional.

Next action:

- Keep `pinwheel` in `Experimental` until manual visible review justifies promotion.
- Keep `dodecagonal-square-triangle` documented as a decorated periodic `3.12.12` square-triangle generator unless a faithful canonical Schlottmann marked-prototile implementation replaces it.
- Keep product status, verification status, and known-deviation docs aligned in the same change.

### 4. Verification Report Consumption

`tools/report_tiling_verification_strength.py` can already produce detailed and JSON output, but there is no current consumer for a CI artifact.

Next action:

- Publish the report as a CI artifact only when there is a reviewer, release, or dashboard workflow that uses it.
- Until then, keep it as an on-demand maintainer diagnostic.

### 5. Standalone Runtime Packaging

The standalone demo still loads Pyodide from a CDN. That is acceptable for the preview, but it remains a public limitation.

Next action:

- Keep the CDN dependency documented in README, release notes, and known limitations.
- Revisit offline bundling only if standalone offline use becomes a product goal.

## Completed Cleanup

The following roadmap items are considered done and should not be reopened without a new concrete problem:

- gesture and selection session split
- canvas transient overlay state and renderer split
- drawer inspector extraction and section-owned model builders
- aperiodic implementation contract layer
- literature-reference verifier/spec package split
- shared polygon adapter common path
- backend/frontend payload contract guard
- centralized Playwright suite manifest and npm runner path

## Do Not Do Yet

- Do not promote `dodecagonal-square-triangle` or `pinwheel` until their implementation and visual-review blockers are resolved.
- Do not centralize all constants into one global config file.
- Do not rewrite the app controller stack without a concrete ownership problem that the existing splits cannot handle.
- Do not replace Playwright coverage with unit tests for flows that genuinely require DOM, canvas, browser storage, or standalone worker execution.
