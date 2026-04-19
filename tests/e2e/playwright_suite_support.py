import inspect
import json
import sys
import unittest
from collections import OrderedDict
from dataclasses import asdict, dataclass
from pathlib import Path


try:
    from tests.e2e.playwright_case_suite import (
        CellularAutomatonUITests,
        StandaloneCellularAutomatonUITests,
        StandaloneRuntimeFailureTests,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.playwright_case_suite import (
        CellularAutomatonUITests,
        StandaloneCellularAutomatonUITests,
        StandaloneRuntimeFailureTests,
    )


DEFAULT_PLAYWRIGHT_SERVER_SUBSET_COUNT = 4
DEFAULT_PLAYWRIGHT_SUBSET_COUNT = DEFAULT_PLAYWRIGHT_SERVER_SUBSET_COUNT

PLAYWRIGHT_FEATURE_NAMES = (
    "rules_and_picker",
    "overlays_and_editor",
    "topology_and_persistence",
    "pattern_and_showcase",
    "standalone_runtime",
)

PLAYWRIGHT_LOCAL_CASES = (
    CellularAutomatonUITests,
    StandaloneCellularAutomatonUITests,
    StandaloneRuntimeFailureTests,
)

PLAYWRIGHT_SERVER_CASES = (
    CellularAutomatonUITests,
)

PLAYWRIGHT_STANDALONE_CASES = (
    StandaloneCellularAutomatonUITests,
    StandaloneRuntimeFailureTests,
)


@dataclass(frozen=True)
class PlaywrightSuiteDefinition:
    name: str
    label: str
    module: str
    includes_standalone: bool
    requires_standalone_build: bool
    shardable: bool
    env: tuple[tuple[str, str], ...] = ()

    def payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["env"] = dict(self.env)
        return payload


def should_skip_playwright_under_discovery(pattern: str | None) -> bool:
    return pattern is not None


def _pattern_and_showcase_match(name: str) -> bool:
    return any(
        token in name
        for token in (
            "pattern",
            "clipboard",
            "copy_",
            "export_",
            "import_",
            "paste_",
            "showcase",
        )
    )


def _topology_and_persistence_match(name: str) -> bool:
    return any(
        token in name
        for token in (
            "switch_",
            "restart",
            "reload_",
            "topology_",
            "penrose",
        )
    )


def _overlays_and_editor_match(name: str) -> bool:
    return any(
        token in name
        for token in (
            "drawer",
            "overlay",
            "hud",
            "edit",
            "paint",
            "canvas_",
            "quick_start",
            "inspector",
        )
    )


def _test_id(case_cls: type[unittest.TestCase], name: str) -> str:
    return f"{case_cls.__name__}.{name}"


def _available_test_cases() -> dict[str, type[unittest.TestCase]]:
    return {
        case_cls.__name__: case_cls
        for case_cls in PLAYWRIGHT_LOCAL_CASES
    }


def _iter_case_test_names(case_classes: tuple[type[unittest.TestCase], ...]) -> list[str]:
    names: list[str] = []
    for case_cls in case_classes:
        for name, member in inspect.getmembers(case_cls, predicate=callable):
            if name.startswith("test_"):
                names.append(_test_id(case_cls, name))
    return sorted(names)


def iter_local_playwright_test_names() -> list[str]:
    return _iter_case_test_names(PLAYWRIGHT_LOCAL_CASES)


def iter_playwright_test_names() -> list[str]:
    return iter_local_playwright_test_names()


def iter_server_playwright_test_names() -> list[str]:
    return _iter_case_test_names(PLAYWRIGHT_SERVER_CASES)


def iter_standalone_runtime_test_names() -> list[str]:
    return _iter_case_test_names(PLAYWRIGHT_STANDALONE_CASES)


def _playwright_feature_map() -> OrderedDict[str, list[str]]:
    grouped: OrderedDict[str, list[str]] = OrderedDict(
        (feature_name, [])
        for feature_name in PLAYWRIGHT_FEATURE_NAMES
    )

    for test_id in iter_playwright_test_names():
        case_name, name = test_id.split(".", 1)
        if case_name.startswith("Standalone"):
            grouped["standalone_runtime"].append(test_id)
            continue
        if _pattern_and_showcase_match(name):
            grouped["pattern_and_showcase"].append(test_id)
            continue
        if _topology_and_persistence_match(name):
            grouped["topology_and_persistence"].append(test_id)
            continue
        if _overlays_and_editor_match(name):
            grouped["overlays_and_editor"].append(test_id)
            continue
        grouped["rules_and_picker"].append(test_id)

    return grouped


def _playwright_feature_modules() -> OrderedDict[str, str]:
    return OrderedDict(
        (
            ("rules_and_picker", "tests.e2e.test_playwright_rules_and_picker"),
            ("overlays_and_editor", "tests.e2e.test_playwright_overlays_and_editor"),
            ("topology_and_persistence", "tests.e2e.test_playwright_topology_and_persistence"),
            ("pattern_and_showcase", "tests.e2e.test_playwright_pattern_and_showcase"),
            ("standalone_runtime", "tests.e2e.test_playwright_standalone_runtime"),
        )
    )


def _playwright_suite_definitions() -> OrderedDict[str, PlaywrightSuiteDefinition]:
    feature_modules = _playwright_feature_modules()
    definitions: OrderedDict[str, PlaywrightSuiteDefinition] = OrderedDict(
        (
            (
                "all",
                PlaywrightSuiteDefinition(
                    name="all",
                    label="All browser suites",
                    module="tests.e2e.test_playwright_all",
                    includes_standalone=True,
                    requires_standalone_build=True,
                    shardable=False,
                ),
            ),
            (
                "server",
                PlaywrightSuiteDefinition(
                    name="server",
                    label="Server-host browser suites",
                    module="tests.e2e.test_playwright_server",
                    includes_standalone=False,
                    requires_standalone_build=False,
                    shardable=False,
                ),
            ),
            (
                "standalone",
                PlaywrightSuiteDefinition(
                    name="standalone",
                    label="Standalone browser suite",
                    module="tests.e2e.test_playwright_standalone_runtime",
                    includes_standalone=True,
                    requires_standalone_build=True,
                    shardable=False,
                ),
            ),
            (
                "subset",
                PlaywrightSuiteDefinition(
                    name="subset",
                    label="Server browser shard",
                    module="tests.e2e.playwright_chunk_subset",
                    includes_standalone=False,
                    requires_standalone_build=False,
                    shardable=True,
                ),
            ),
        )
    )
    for feature_name in PLAYWRIGHT_FEATURE_NAMES:
        definitions[feature_name] = PlaywrightSuiteDefinition(
            name=feature_name,
            label=feature_name.replace("_", " "),
            module=feature_modules[feature_name],
            includes_standalone=feature_name == "standalone_runtime",
            requires_standalone_build=feature_name == "standalone_runtime",
            shardable=False,
        )
    return definitions


def iter_public_playwright_suite_names() -> list[str]:
    return list(_playwright_suite_definitions())


def resolve_playwright_suite_definition(suite_name: str) -> PlaywrightSuiteDefinition:
    definitions = _playwright_suite_definitions()
    if suite_name not in definitions:
        raise ValueError(f"Unknown Playwright suite '{suite_name}'.")
    return definitions[suite_name]


def playwright_suite_manifest_payload() -> list[dict[str, object]]:
    return [
        definition.payload()
        for definition in _playwright_suite_definitions().values()
    ]


def playwright_suite_manifest_json() -> str:
    return json.dumps(playwright_suite_manifest_payload(), indent=2)


def build_named_playwright_suite(test_ids: list[str]) -> unittest.TestSuite:
    cases = _available_test_cases()
    suite = unittest.TestSuite()
    for test_id in test_ids:
        case_name, method_name = test_id.split(".", 1)
        suite.addTest(cases[case_name](method_name))
    return suite


def build_playwright_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for feature_name in PLAYWRIGHT_FEATURE_NAMES:
        suite.addTests(build_playwright_feature_suite(feature_name))
    return suite


def build_server_playwright_suite() -> unittest.TestSuite:
    return build_named_playwright_suite(iter_server_playwright_test_names())


def iter_playwright_feature_test_names(feature_name: str) -> list[str]:
    grouped = _playwright_feature_map()
    if feature_name not in grouped:
        raise ValueError(f"Unknown Playwright feature suite '{feature_name}'.")
    return grouped[feature_name][:]


def build_playwright_feature_suite(feature_name: str) -> unittest.TestSuite:
    return build_named_playwright_suite(iter_playwright_feature_test_names(feature_name))


def iter_server_playwright_subset_test_names(
    subset_index: int,
    subset_count: int = DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
) -> list[str]:
    if subset_count <= 0:
        raise ValueError("subset_count must be positive")
    if subset_index < 0 or subset_index >= subset_count:
        raise ValueError("subset_index must be within the configured subset count")
    names = iter_server_playwright_test_names()
    return names[subset_index::subset_count]


def iter_playwright_subset_test_names(
    subset_index: int,
    subset_count: int = DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
) -> list[str]:
    return iter_server_playwright_subset_test_names(subset_index, subset_count)


def build_server_playwright_subset(
    subset_index: int,
    subset_count: int = DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
) -> unittest.TestSuite:
    return build_named_playwright_suite(
        iter_server_playwright_subset_test_names(subset_index, subset_count)
    )


def build_playwright_subset(
    subset_index: int,
    subset_count: int = DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
) -> unittest.TestSuite:
    return build_server_playwright_subset(subset_index, subset_count)
