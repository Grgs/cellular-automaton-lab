import unittest

from backend.defaults import (
    APP_DEFAULTS,
    DEFAULT_CELL_SIZE,
    DEFAULT_HEIGHT,
    DEFAULT_RULE_NAME,
    DEFAULT_SPEED,
    DEFAULT_THEME,
    DEFAULT_WIDTH,
    MAX_CELL_SIZE,
    MAX_GRID_SIZE,
    MAX_SPEED,
    MIN_CELL_SIZE,
    MIN_GRID_SIZE,
    MIN_SPEED,
    THEME_STORAGE_KEY,
    UI_STORAGE_KEY,
    load_defaults,
)


class DefaultsTests(unittest.TestCase):
    def test_defaults_file_contains_expected_sections(self) -> None:
        defaults = load_defaults()

        self.assertIn("simulation", defaults)
        self.assertIn("ui", defaults)
        self.assertIn("theme", defaults)

    def test_module_constants_are_loaded_from_defaults_file(self) -> None:
        self.assertEqual(DEFAULT_WIDTH, APP_DEFAULTS["simulation"]["topology_spec"]["width"])
        self.assertEqual(DEFAULT_HEIGHT, APP_DEFAULTS["simulation"]["topology_spec"]["height"])
        self.assertEqual(DEFAULT_SPEED, APP_DEFAULTS["simulation"]["speed"])
        self.assertEqual(DEFAULT_RULE_NAME, APP_DEFAULTS["simulation"]["rule"])
        self.assertEqual(MIN_GRID_SIZE, APP_DEFAULTS["simulation"]["min_grid_size"])
        self.assertEqual(MAX_GRID_SIZE, APP_DEFAULTS["simulation"]["max_grid_size"])
        self.assertEqual(MIN_SPEED, APP_DEFAULTS["simulation"]["min_speed"])
        self.assertEqual(MAX_SPEED, APP_DEFAULTS["simulation"]["max_speed"])
        self.assertEqual(DEFAULT_CELL_SIZE, APP_DEFAULTS["ui"]["cell_size"])
        self.assertEqual(MIN_CELL_SIZE, APP_DEFAULTS["ui"]["min_cell_size"])
        self.assertEqual(MAX_CELL_SIZE, APP_DEFAULTS["ui"]["max_cell_size"])
        self.assertEqual(UI_STORAGE_KEY, APP_DEFAULTS["ui"]["storage_key"])
        self.assertEqual(DEFAULT_THEME, APP_DEFAULTS["theme"]["default"])
        self.assertEqual(THEME_STORAGE_KEY, APP_DEFAULTS["theme"]["storage_key"])


if __name__ == "__main__":
    unittest.main()
