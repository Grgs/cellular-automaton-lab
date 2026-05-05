# Contributing

Cellular Automaton Lab is a `v0.1.x` preview project. Contributions are welcome, but the repository is still the public integration surface: there is no npm package, PyPI package, plugin API, or long-term compatibility promise yet.

## First 30 Minutes

1. Install dependencies:

```powershell
py -3 -m pip install -r requirements-dev.txt
npm install
py -3 -m playwright install chromium
```

2. Build and run the app:

```powershell
npm run build:frontend
py -3 .\app.py
```

3. Open [http://127.0.0.1:5000](http://127.0.0.1:5000), choose Square + Conway, paint a few cells, then step or run the simulation.

4. Read the guide that matches your change:

- [Adding rules](docs/ADDING_RULES.md)
- [Adding topologies](docs/ADDING_TOPOLOGIES.md)
- [Adding presets and patterns](docs/ADDING_PRESETS_AND_PATTERNS.md)
- [Choosing tests for changes](docs/TESTING_CHANGES.md)

## Common Commands

Use the npm script surface first; it wraps the repo-owned Python launchers and keeps local and CI commands aligned.

```powershell
npm run check:frontend
npm run check:python
npm run check:doc-links
```

For a broader local sweep:

```powershell
npm run check:ci-local
```

For focused change-specific commands, use [docs/TESTING_CHANGES.md](docs/TESTING_CHANGES.md). For every script under `tools/`, use [docs/TOOLS.md](docs/TOOLS.md).

## Contribution Expectations

- Keep changes scoped to the behavior or documentation being changed.
- Prefer existing subsystem patterns over new abstractions.
- Keep topology IDs, rule IDs, and sparse pattern payload fields stable once they are public.
- Add or update tests at the cheapest layer that proves the changed contract.
- Regenerate checked-in fixtures only through repo-owned commands, not by hand.
- Update known-limitation docs when a tiling implementation is approximate, experimental, or intentionally not literature-canonical.

## Documentation Ownership

- `README.md`: product overview, local setup, and the public command surface
- `CONTRIBUTING.md`: contributor setup and workflow entrypoint
- `docs/ARCHITECTURE.md`: runtime boundaries and subsystem ownership
- `docs/CODE_MAP.md`: file-level navigation and call paths
- `docs/TESTING.md`: test strategy and browser diagnosis
- `docs/MAINTENANCE.md`: guardrails, release process, and documentation ownership
- `TODO.md`: current implementation follow-up
- `CHANGELOG.md`: completed work

## Pull Requests

Before opening a PR, run the narrow checks that match your change and record them in the PR description. For release-facing or cross-boundary changes, run the broader release-confidence commands listed in [README.md](README.md).

Do not promote `pinwheel` or `dodecagonal-square-triangle` status unless the implementation and visible-review blockers in [TODO.md](TODO.md) and [docs/TILING_KNOWN_DEVIATIONS.md](docs/TILING_KNOWN_DEVIATIONS.md) are resolved in the same change.
