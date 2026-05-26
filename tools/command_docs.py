from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class CommandDoc:
    path: tuple[str, ...]
    group: str
    summary: str
    details: str
    examples: tuple[str, ...]

    @property
    def label(self) -> str:
        return "python -m tools " + " ".join(self.path)


@dataclass(frozen=True)
class GroupDoc:
    key: str
    title: str
    intro: str


GROUPS: Final[tuple[GroupDoc, ...]] = (
    GroupDoc("build", "Build", "Build and inspect standalone frontend artifacts."),
    GroupDoc("tilings", "Tilings", "Validate, verify, preview, sketch, and scaffold tilings."),
    GroupDoc("fixtures", "Fixtures", "Regenerate or check checked-in fixture files."),
    GroupDoc("bootstrap", "Bootstrap", "Export bootstrapped backend metadata for standalone mode."),
    GroupDoc(
        "browser", "Browser", "Run browser-backed reviews, sweeps, workbenches, and smoke checks."
    ),
    GroupDoc(
        "test",
        "Tests",
        "Run Playwright suites, backend coverage, and standalone build introspection.",
    ),
    GroupDoc("security", "Security", "Run privacy, secret-scanning, and supply-chain checks."),
    GroupDoc("perf", "Performance", "Run engine and topology performance investigations."),
    GroupDoc("repo", "Repo", "Run repo-level maintenance commands."),
)


COMMANDS: Final[tuple[CommandDoc, ...]] = (
    CommandDoc(
        ("build", "standalone"),
        "build",
        "Build the standalone bundle into `output/standalone/` and write a build manifest.",
        "Python-first replacement for the old standalone build script. It stages the standalone shell, runs Vite, writes bootstrap data, bundles backend/config Python sources, and records source provenance in `build-manifest.json`.",
        ("python -m tools build standalone",),
    ),
    CommandDoc(
        ("build", "standalone-shell"),
        "build",
        "Render the standalone HTML shell to stdout or a file.",
        "Useful when inspecting the shared standalone wrapper independently from a full build.",
        (
            "python -m tools build standalone-shell",
            "python -m tools build standalone-shell output/.standalone-build-input/standalone.html",
        ),
    ),
    CommandDoc(
        ("build", "bundle-size"),
        "build",
        "Check standalone bundle budgets and emit optional JSON or text reports.",
        "Runs the standalone bundle budget gate against `output/standalone/` and supports baseline comparisons for CI/history tracking.",
        (
            "python -m tools build bundle-size",
            "python -m tools build bundle-size --format json",
        ),
    ),
    CommandDoc(
        ("tilings", "validate"),
        "tilings",
        "Run geometry/topology validation across catalog tilings.",
        "Cheap sanity validation for topology structure, adjacency, holes, and edge multiplicity.",
        ("python -m tools tilings validate",),
    ),
    CommandDoc(
        ("tilings", "verify"),
        "tilings",
        "Run literature-backed reference verification across tiling families.",
        "Stricter verification than `tilings validate`, including signatures, fixtures, and connectivity invariants.",
        ("python -m tools tilings verify",),
    ),
    CommandDoc(
        ("tilings", "report"),
        "tilings",
        "Report per-family verification strength in summary, detail, or JSON format.",
        "Aggregates implementation contracts, fixture coverage, and live verification results.",
        (
            "python -m tools tilings report",
            "python -m tools tilings report --format detail",
        ),
    ),
    CommandDoc(
        ("tilings", "preview"),
        "tilings",
        "Generate preview polygon data for the tiling picker.",
        "Supports periodic and aperiodic preview generation and discovery via `--list`.",
        (
            "python -m tools tilings preview --list",
            "python -m tools tilings preview --geometry kisrhombille",
        ),
    ),
    CommandDoc(
        ("tilings", "sketch"),
        "tilings",
        "Sketch and validate a candidate periodic tiling without wiring it into the catalog.",
        "Builds a patch from a sketch file, reports topology/geometry issues, and can emit SVG/JSON/reference-spec outputs.",
        (
            "python -m tools tilings sketch tools/sketch_examples/triangular_square_2uniform.py",
            "python -m tools tilings sketch path/to/sketch.py --svg out.svg --json out.json",
        ),
    ),
    CommandDoc(
        ("tilings", "scaffold-aperiodic"),
        "tilings",
        "Scaffold the boilerplate for a new aperiodic tiling family.",
        "Creates the generator skeleton, reference spec, tests, and registry/manifest inserts before real geometry is implemented.",
        (
            'python -m tools tilings scaffold-aperiodic --family-id widget-monotile --label "Widget Monotile" --kind widget --source-url https://example.org/widget',
        ),
    ),
    CommandDoc(
        ("fixtures", "reference"),
        "fixtures",
        "Regenerate or check literature reference fixtures.",
        "Supports `--check`, `--all`, targeted geometry/depth regeneration, and discovery with `--list-targets`.",
        (
            "python -m tools fixtures reference --all --mode both --check",
            "python -m tools fixtures reference --mode canonical --geometry pinwheel --depth 3",
        ),
    ),
    CommandDoc(
        ("fixtures", "frontend"),
        "fixtures",
        "Regenerate or check frontend representative topology fixtures.",
        "Supports `--check`, `--all`, targeted fixture names, and discovery with `--list-fixtures`.",
        (
            "python -m tools fixtures frontend --all --check",
            "python -m tools fixtures frontend --fixture shield-depth-3",
        ),
    ),
    CommandDoc(
        ("bootstrap", "export"),
        "bootstrap",
        "Export the backend bootstrap payload to JSON.",
        "Writes topology catalog, rule metadata, and canonical defaults to a file for standalone/runtime consumers.",
        ("python -m tools bootstrap export frontend/test-fixtures/bootstrap-data.json",),
    ),
    CommandDoc(
        ("browser", "review"),
        "browser",
        "Render one topology through the real browser canvas path and emit PNG/JSON artifacts.",
        "Supports named profiles, literature review, cached references, and visual metrics. Use `--list-profiles` for discovery.",
        (
            "python -m tools browser review --list-profiles",
            "python -m tools browser review --profile pinwheel-depth-3",
        ),
    ),
    CommandDoc(
        ("browser", "check"),
        "browser",
        "Own browser host startup/cleanup around one render review or targeted unittest.",
        "Managed runner for server or standalone browser checks with artifact manifests and failure bundling.",
        (
            "python -m tools browser check --host standalone --render-review --profile pinwheel-depth-3",
            "python -m tools browser check --host server --unittest tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_chair_topology_switch_renders_aperiodic_patch",
        ),
    ),
    CommandDoc(
        ("browser", "sweep"),
        "browser",
        "Run a small matrix of comparable render-review cases.",
        "Expands a render-review profile across hosts, themes, or sizes and writes one sweep manifest plus case artifacts.",
        ("python -m tools browser sweep --profile shield-depth-3 --hosts standalone,server",),
    ),
    CommandDoc(
        ("browser", "diff"),
        "browser",
        "Build an HTML/PNG comparison sheet from a sweep or by running a new sweep.",
        "Useful when reviewing host/theme/depth differences side by side.",
        (
            "python -m tools browser diff --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server",
            "python -m tools browser diff --sweep-manifest output/render-review-sweeps/<run>/sweep-manifest.json",
        ),
    ),
    CommandDoc(
        ("browser", "workbench-samples"),
        "browser",
        "Explore candidate representative samples for patch-depth families.",
        "Compares structural candidates and can optionally inject them into a browser-backed render review.",
        (
            "python -m tools browser workbench-samples --family shield --patch-depth 3",
            "python -m tools browser workbench-samples --family shield --patch-depth 3 --browser-review --host standalone",
        ),
    ),
    CommandDoc(
        ("browser", "workbench-cleanup"),
        "browser",
        "Explore cleanup-factor candidates for image-derived patch-depth families.",
        "Compares overlap severity, bounds drift, and optional browser-visible gutter risk.",
        (
            "python -m tools browser workbench-cleanup --family shield --patch-depth 3",
            "python -m tools browser workbench-cleanup --family shield --patch-depth 3 --browser-review --host standalone",
        ),
    ),
    CommandDoc(
        ("browser", "smoke-standalone"),
        "browser",
        "Run the standalone smoke test against a prebuilt bundle.",
        "Launches headless Chromium, waits for bootstrap readiness, and fails on unexpected startup errors.",
        (
            "python -m tools browser smoke-standalone",
            "python -m tools browser smoke-standalone --format json --output output/standalone-smoke.json",
        ),
    ),
    CommandDoc(
        ("test", "e2e"),
        "test",
        "Run Playwright suites through the Python CLI, or run the broader local e2e orchestrator.",
        "Use `--list-suites` to inspect suite names, `--suite` to run a specific suite, or `--orchestrated` to run the old frontend-plus-chunked-playwright workflow.",
        (
            "python -m tools test e2e --list-suites",
            "python -m tools test e2e --suite server",
            "python -m tools test e2e --orchestrated",
        ),
    ),
    CommandDoc(
        ("test", "coverage"),
        "test",
        "Run backend coverage for the unit suite, API suite, or both.",
        "Mirrors the CI coverage flow and supports XML/HTML outputs plus `--fail-under`.",
        (
            "python -m tools test coverage",
            "python -m tools test coverage --suite unit --fail-under 80",
        ),
    ),
    CommandDoc(
        ("test", "playwright-suites"),
        "test",
        "Print the public Playwright suite manifest.",
        "Structured replacement for the old manifest-print helper.",
        (
            "python -m tools test playwright-suites",
            "python -m tools test playwright-suites --format names",
        ),
    ),
    CommandDoc(
        ("test", "standalone-build-status"),
        "test",
        "Print standalone build freshness and provenance status.",
        "Reports whether `output/standalone/` is current for standalone-backed browser workflows.",
        (
            "python -m tools test standalone-build-status",
            "python -m tools test standalone-build-status --format summary",
        ),
    ),
    CommandDoc(
        ("security", "privacy"),
        "security",
        "Scan tracked repo files for personal-information leaks.",
        "Supports pre-commit filename arguments or full-repo mode with `--all-files`.",
        (
            "python -m tools security privacy --all-files",
            "python -m tools security privacy README.md docs/TOOLS.md",
        ),
    ),
    CommandDoc(
        ("security", "secrets"),
        "security",
        "Run `detect-secrets` against changed files or the full tracked repo.",
        "Wrapper around the repo baseline with the same changed-file/full-repo split used in pre-commit.",
        ("python -m tools security secrets --baseline .secrets.baseline --all-files",),
    ),
    CommandDoc(
        ("security", "supply-chain"),
        "security",
        "Run the combined Python and npm supply-chain audit.",
        "Runs `pip-audit` plus `npm audit` and can emit summary or JSON findings.",
        (
            "python -m tools security supply-chain",
            "python -m tools security supply-chain --severity moderate --format json",
        ),
    ),
    CommandDoc(
        ("perf", "bench"),
        "perf",
        "Run engine microbenchmarks across representative rule/topology scenarios.",
        "Benchmarks the optimized engine path against a reference-style helper path.",
        ("python -m tools perf bench",),
    ),
    CommandDoc(
        ("perf", "latency"),
        "perf",
        "Profile topology-build, backend-mutation, and browser-roundtrip latency.",
        "Uses a real Playwright browser and server host for end-to-end timing investigations.",
        ("python -m tools perf latency",),
    ),
    CommandDoc(
        ("repo", "processes"),
        "repo",
        "Inspect or clean up repo-scoped helper processes.",
        "Lists or kills server/standalone/browser helper processes and their ports.",
        (
            "python -m tools repo processes list",
            "python -m tools repo processes kill --stale-browser-hosts",
        ),
    ),
    CommandDoc(
        ("repo", "python-style"),
        "repo",
        "Run repo-owned Ruff style commands for Python sources.",
        "Supports `check`, `format-check`, and `format` over the repo Python surface.",
        (
            "python -m tools repo python-style check",
            "python -m tools repo python-style format-check",
        ),
    ),
    CommandDoc(
        ("repo", "tools-docs"),
        "repo",
        "Generate or check `docs/TOOLS.md` from the CLI registry.",
        "Use `--check` in tests/CI and `--write` when intentionally refreshing the generated tools reference.",
        (
            "python -m tools repo tools-docs --check",
            "python -m tools repo tools-docs --write",
        ),
    ),
)


COMMAND_INDEX: Final[dict[tuple[str, ...], CommandDoc]] = {doc.path: doc for doc in COMMANDS}


def command_doc(*path: str) -> CommandDoc:
    return COMMAND_INDEX[tuple(path)]
