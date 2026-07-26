# Validation Planner

`python -m tools test plan` is a read-only, deterministic checklist builder. It proposes checks; it never runs them.

```powershell
python -m tools test plan --base origin/main
python -m tools test plan --changed frontend/controls/shell-clicks.ts
python -m tools test plan --format json
```

Without `--changed`, the planner combines committed changes from `BASE...HEAD` with staged, unstaged, and untracked paths. With `--changed`, it only inspects the supplied paths, which is useful when handing work to another task.

The output has three tiers:

- Focused checks: narrow checks selected from the changed paths.
- Before pushing: the one repository PR gate, `npm run check:ci-local`.
- CI-owned checks: platform coverage and clean-environment artifact work that remain in CI.

The mapping follows [Testing Changes](TESTING_CHANGES.md): documentation, shared frontend UI, backend/API, standalone runtime, tiling/catalog, generated fixtures, and test-only changes each receive the matching repository commands. Shared UI and catalog changes include both server and standalone browser coverage. Script names are read from `package.json`, and browser suite names are verified against the public Playwright suite manifest.
