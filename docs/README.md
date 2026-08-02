# Documentation Index

Documentation is grouped by purpose. Start with the smallest document that
answers your question, then follow its links into the detailed references.

## Start here

| Doc | What it is |
|---|---|
| [ONBOARDING.md](ONBOARDING.md) | First-time decision tree: *"I want to do X — read Y, run Z"* |
| [DESIGN.md](DESIGN.md) | Product goals, durable design decisions, tradeoffs, and rejected alternatives |
| [../examples/README.md](../examples/README.md) | Five short runnable Python scripts (build a patch, run a sim, render SVG, ...) |

## Using the app

| Doc | What it is |
|---|---|
| [COMPARISON_WALL.md](COMPARISON_WALL.md) | Configure, play, edit, fork, analyze, save, and share comparison-wall runs |
| [standalone-browser-runtime.md](standalone-browser-runtime.md) | Build, run, test, and deploy the Pyodide-in-browser host |

## Architecture

| Doc | What it is |
|---|---|
| [DESIGN.md](DESIGN.md) | Why the system uses a topology-first Python core, Flask adapter, and Pyodide worker |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Current runtime boundaries, ownership, and state flow |
| [CODE_MAP.md](CODE_MAP.md) | File-level navigation; "if you want to change X, look at Y" |
| [TILING_ARCHITECTURE_NOTES.md](TILING_ARCHITECTURE_NOTES.md) | How the tiling family system is layered (registry, builder, reference spec) |

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

## Current project records

These are useful when working on the corresponding area, but are not the
starting point for understanding the whole system.

| Doc | What it is |
|---|---|
| [UI_WORKBENCH_REDESIGN.md](UI_WORKBENCH_REDESIGN.md) | Completed Compare workbench program decisions and delivery record |
| [UI_USER_TESTING_NOTES.md](UI_USER_TESTING_NOTES.md) | Dated browser user-flow test session and follow-up |
| [VALIDATION_PLANNER.md](VALIDATION_PLANNER.md) | Contract for the read-only change-aware validation planner |
| [contracts/](contracts/) | Focused implementation contracts and provenance for complex generators |

## Historical investigations

> Status: kept for context, not current operational guidance.

| Doc | What it is |
|---|---|
| [PENROSE_CANONICAL_SUBSTITUTION_PLAN.md](PENROSE_CANONICAL_SUBSTITUTION_PLAN.md) | Past investigation into a canonical Penrose rewrite; not the current implementation path |
| [TILING_DIAGNOSIS_TOOLING_NOTES.md](TILING_DIAGNOSIS_TOOLING_NOTES.md) | Process findings from one focused diagnosis session; treat as notes, not user-facing reference |

## Document boundaries

- Put product-level rationale and durable tradeoffs in [DESIGN.md](DESIGN.md).
- Put current subsystem ownership and runtime flow in [ARCHITECTURE.md](ARCHITECTURE.md).
- Put file paths and call traces in [CODE_MAP.md](CODE_MAP.md).
- Put active work in [../TODO.md](../TODO.md), completed work in
  [../CHANGELOG.md](../CHANGELOG.md), and dated release behavior in
  [releases/](releases/).
- Do not rewrite old release notes to match current behavior. Add a current-doc
  correction instead when the implementation has moved on.

---

For top-level docs (`README.md`, `CONTRIBUTING.md`, `SECURITY.md`,
`CHANGELOG.md`, `TODO.md`), see the repo root.
