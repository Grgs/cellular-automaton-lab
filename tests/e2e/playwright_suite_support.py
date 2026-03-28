import inspect
import sys
import unittest
from collections import OrderedDict
from pathlib import Path


try:
    from tests.e2e.playwright_case_suite import CellularAutomatonUITests
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.playwright_case_suite import CellularAutomatonUITests


DEFAULT_PLAYWRIGHT_SUBSET_COUNT = 6

PLAYWRIGHT_FEATURE_NAMES = (
    "rules_and_picker",
    "overlays_and_editor",
    "topology_and_persistence",
    "pattern_and_showcase",
)


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
            "switching_to_",
            "server_restart",
            "patch_depth",
            "topology_",
            "archimedean",
            "kagome",
            "penrose",
            "snub",
            "triangle",
            "hexlife_click",
            "trilife",
            "hexwhirlpool_cell_size",
        )
    )


def _overlays_and_editor_match(name: str) -> bool:
    return any(
        token in name
        for token in (
            "drawer",
            "overlay",
            "hud",
            "grid_click",
            "edit",
            "paint",
            "brush",
            "line_",
            "rectangle_",
            "fill_",
            "top_bar",
            "mobile",
            "theme",
            "workspace_empty_click",
            "running_",
            "rule_notes",
            "rule_palette_section",
            "canvas_",
            "viewport_",
            "empty_click",
            "inspector",
        )
    )


def _playwright_feature_map() -> OrderedDict[str, list[str]]:
    grouped: OrderedDict[str, list[str]] = OrderedDict(
        (feature_name, [])
        for feature_name in PLAYWRIGHT_FEATURE_NAMES
    )

    for name in iter_playwright_test_names():
        if _pattern_and_showcase_match(name):
            grouped["pattern_and_showcase"].append(name)
            continue
        if _topology_and_persistence_match(name):
            grouped["topology_and_persistence"].append(name)
            continue
        if _overlays_and_editor_match(name):
            grouped["overlays_and_editor"].append(name)
            continue
        grouped["rules_and_picker"].append(name)

    return grouped


def iter_playwright_test_names() -> list[str]:
    return sorted(
        name
        for name, member in inspect.getmembers(CellularAutomatonUITests, predicate=callable)
        if name.startswith("test_")
    )


def build_named_playwright_suite(test_names: list[str]) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for name in test_names:
        suite.addTest(CellularAutomatonUITests(name))
    return suite


def build_playwright_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for feature_name in PLAYWRIGHT_FEATURE_NAMES:
        suite.addTests(build_playwright_feature_suite(feature_name))
    return suite


def iter_playwright_feature_test_names(feature_name: str) -> list[str]:
    grouped = _playwright_feature_map()
    if feature_name not in grouped:
        raise ValueError(f"Unknown Playwright feature suite '{feature_name}'.")
    return grouped[feature_name][:]


def build_playwright_feature_suite(feature_name: str) -> unittest.TestSuite:
    return build_named_playwright_suite(iter_playwright_feature_test_names(feature_name))


def iter_playwright_subset_test_names(
    subset_index: int,
    subset_count: int = DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
) -> list[str]:
    if subset_count <= 0:
        raise ValueError("subset_count must be positive")
    if subset_index < 0 or subset_index >= subset_count:
        raise ValueError("subset_index must be within the configured subset count")
    names = iter_playwright_test_names()
    return names[subset_index::subset_count]


def build_playwright_subset(
    subset_index: int,
    subset_count: int = DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
) -> unittest.TestSuite:
    return build_named_playwright_suite(
        iter_playwright_subset_test_names(subset_index, subset_count)
    )
