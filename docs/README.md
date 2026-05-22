# Documentation Index

This folder has 20+ docs. They're grouped here so you can find what you
need without grepping for filenames.

## Start here

| Doc | What it is |
|---|---|
| [ONBOARDING.md](ONBOARDING.md) | First-time decision tree: *"I want to do X — read Y, run Z"* |
| [../examples/README.md](../examples/README.md) | Five short runnable Python scripts (build a patch, run a sim, render SVG, ...) |

## Architecture

| Doc | What it is |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Runtime boundaries: backend / frontend / standalone; request flow |
| [CODE_MAP.md](CODE_MAP.md) | File-level navigation; "if you want to change X, look at Y" |
| [TILING_ARCHITECTURE_NOTES.md](TILING_ARCHITECTURE_NOTES.md) | How the tiling family system is layered (registry, builder, reference spec) |
| [standalone-browser-runtime.md](standalone-browser-runtime.md) | How the Pyodide-in-browser path works |

## Add new content

| Doc | What it is |
|---|---|
| [ADDING_TOPOLOGIES.md](ADDING_TOPOLOGIES.md) | Add a new tiling family (5 files + fixture regen) |
| [ADDING_RULES.md](ADDING_RULES.md) | Add a new CA rule (subclass `AutomatonRule`) |
| [ADDING_PRESETS_AND_PATTERNS.md](ADDING_PRESETS_AND_PATTERNS.md) | Add a preset or pattern file |

## Testing

| Doc | What it is |
|---|---|
| [TESTING.md](TESTING.md) | Full testing strategy: layers, commands, CI mapping |
| [TESTING_CHANGES.md](TESTING_CHANGES.md) | "If you changed X, run these tests" recipes |
| [TESTING_TILINGS.md](TESTING_TILINGS.md) | Tiling-specific validation + diagnosis |

## Tilings reference

| Doc | What it is |
|---|---|
| [TILING_INVARIANTS.md](TILING_INVARIANTS.md) | What every tiling must satisfy + how it's checked |
| [TILING_VERIFICATION_STATUS.md](TILING_VERIFICATION_STATUS.md) | Per-family verification strength snapshot |
| [TILING_REFERENCE_SOURCES.md](TILING_REFERENCE_SOURCES.md) | Literature / URL sources per family |
| [TILING_KNOWN_DEVIATIONS.md](TILING_KNOWN_DEVIATIONS.md) | Where the app intentionally diverges from the literature |

## Process & ownership

| Doc | What it is |
|---|---|
| [MAINTENANCE.md](MAINTENANCE.md) | Releases, doc ownership, dependency pinning, guardrails |
| [CODE_QUALITY_ROADMAP.md](CODE_QUALITY_ROADMAP.md) | What's actively being cleaned up + what's *not* on the list |
| [TOOLS.md](TOOLS.md) | Every `tools/` script and what it does |

## Historical / internal

> Status: kept for context, not current operational guidance.

| Doc | What it is |
|---|---|
| [PENROSE_CANONICAL_SUBSTITUTION_PLAN.md](PENROSE_CANONICAL_SUBSTITUTION_PLAN.md) | Past investigation into a canonical Penrose rewrite; not the current implementation path |
| [TILING_DIAGNOSIS_TOOLING_NOTES.md](TILING_DIAGNOSIS_TOOLING_NOTES.md) | Process findings from one focused diagnosis session; treat as notes, not user-facing reference |

---

For top-level docs (`README.md`, `CONTRIBUTING.md`, `SECURITY.md`,
`CHANGELOG.md`, `TODO.md`), see the repo root.
