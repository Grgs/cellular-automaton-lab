import unittest
from typing import ClassVar

from flask import Flask, request

from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.web.requests import (
    RequestValidationError,
    get_payload,
    parse_cell_id,
    parse_cell_target,
    parse_cell_updates,
    parse_optional_float,
    parse_optional_int,
    parse_required_int,
    parse_rule_name,
    parse_state_value,
    parse_topology_spec,
)


class RequestParsingTests(unittest.TestCase):
    app: ClassVar[Flask]
    rule_registry: ClassVar[RuleRegistry]
    conway: ClassVar[AutomatonRule]
    wireworld: ClassVar[AutomatonRule]

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = Flask(__name__)
        cls.rule_registry = RuleRegistry()
        cls.conway = cls.rule_registry.get("conway")
        cls.wireworld = cls.rule_registry.get("wireworld")

    def test_get_payload_returns_dict_for_object_json(self) -> None:
        with self.app.test_request_context(json={"width": 10}):
            self.assertEqual(get_payload(request), {"width": 10})

    def test_get_payload_returns_empty_dict_for_non_object_json(self) -> None:
        with self.app.test_request_context(json=[1, 2, 3]):
            self.assertEqual(get_payload(request), {})

    def test_parse_optional_numbers_accept_blank_values(self) -> None:
        payload = {"width": "", "speed": None}
        self.assertIsNone(parse_optional_int(payload, "width"))
        self.assertIsNone(parse_optional_float(payload, "speed"))

    def test_parse_optional_numbers_convert_numeric_strings(self) -> None:
        payload = {"width": "12", "speed": "7.5"}
        self.assertEqual(parse_optional_int(payload, "width"), 12)
        self.assertEqual(parse_optional_float(payload, "speed"), 7.5)

    def test_parse_optional_numbers_raise_validation_errors(self) -> None:
        with self.assertRaises(RequestValidationError):
            parse_optional_int({"width": "abc"}, "width")
        with self.assertRaises(RequestValidationError):
            parse_optional_float({"speed": "fast"}, "speed")

    def test_parse_required_int_validates_presence_and_type(self) -> None:
        self.assertEqual(parse_required_int({"x": "4"}, "x"), 4)

        with self.assertRaises(RequestValidationError):
            parse_required_int({}, "x")
        with self.assertRaises(RequestValidationError):
            parse_required_int({"x": "bad"}, "x")

    def test_parse_state_value_accepts_rule_defined_states(self) -> None:
        self.assertEqual(parse_state_value({"state": True}, self.conway), 1)
        self.assertEqual(parse_state_value({"state": 0}, self.conway), 0)
        self.assertEqual(parse_state_value({"state": "3"}, self.wireworld), 3)

        with self.assertRaises(RequestValidationError):
            parse_state_value({"state": 2}, self.conway)
        with self.assertRaises(RequestValidationError):
            parse_state_value({"state": "bad"}, self.wireworld)

    def test_parse_cell_id_validates_presence_and_type(self) -> None:
        self.assertEqual(parse_cell_id({"id": "c:1:1"}), "c:1:1")

        with self.assertRaises(RequestValidationError):
            parse_cell_id({})
        with self.assertRaises(RequestValidationError):
            parse_cell_id({"id": ""})
        with self.assertRaises(RequestValidationError):
            parse_cell_id({"id": 123})

    def test_parse_cell_target_accepts_ids_only(self) -> None:
        self.assertEqual(parse_cell_target({"id": "o:1:1"}), {"id": "o:1:1"})

        with self.assertRaises(RequestValidationError):
            parse_cell_target({})
        with self.assertRaises(RequestValidationError):
            parse_cell_target({"id": 123})
        with self.assertRaises(RequestValidationError):
            parse_cell_target({"x": "4", "y": 7})

    def test_parse_cell_updates_validates_and_parses_cells(self) -> None:
        parsed = parse_cell_updates(
            {"cells": [{"id": "tu:1:2", "state": 3}, {"id": "o:2:3", "state": 1}]},
            self.wireworld,
        )
        self.assertEqual(
            parsed,
            [
                {"id": "tu:1:2", "state": 3},
                {"id": "o:2:3", "state": 1},
            ],
        )

        with self.assertRaises(RequestValidationError):
            parse_cell_updates({"cells": []}, self.wireworld)
        with self.assertRaises(RequestValidationError):
            parse_cell_updates({"cells": ["bad"]}, self.wireworld)
        with self.assertRaises(RequestValidationError):
            parse_cell_updates({"cells": [{"id": "tu:1:1", "state": 9}]}, self.wireworld)
        with self.assertRaises(RequestValidationError):
            parse_cell_updates({"cells": [{"id": 1, "state": 1}]}, self.wireworld)
        with self.assertRaises(RequestValidationError):
            parse_cell_updates({"cells": [{"id": "tu:1:1"}]}, self.wireworld)
        with self.assertRaises(RequestValidationError):
            parse_cell_updates({"cells": [{"x": 1, "y": 1, "state": 3}]}, self.wireworld)

    def test_parse_rule_name_accepts_known_rules_and_blank_values(self) -> None:
        self.assertEqual(parse_rule_name({"rule": "conway"}, self.rule_registry), "conway")
        self.assertEqual(parse_rule_name({"rule": "wireworld"}, self.rule_registry), "wireworld")
        self.assertIsNone(parse_rule_name({}, self.rule_registry))
        self.assertIsNone(parse_rule_name({"rule": ""}, self.rule_registry))

    def test_parse_rule_name_rejects_unknown_rules(self) -> None:
        with self.assertRaises(RequestValidationError):
            parse_rule_name({"rule": "missing"}, self.rule_registry)
        with self.assertRaises(RequestValidationError):
            parse_rule_name({"rule": 123}, self.rule_registry)

    def test_parse_topology_spec_accepts_known_values_and_rejects_unknown_ones(self) -> None:
        self.assertEqual(
            parse_topology_spec({"topology_spec": {"tiling_family": "square", "adjacency_mode": "edge", "width": 10, "height": 6}}),
            {
                "tiling_family": "square",
                "adjacency_mode": "edge",
                "sizing_mode": "grid",
                "width": 10,
                "height": 6,
                "patch_depth": None,
            },
        )
        self.assertEqual(
            parse_topology_spec({"topology_spec": {"tiling_family": "penrose-p3-rhombs", "adjacency_mode": "vertex", "patch_depth": 4}}),
            {
                "tiling_family": "penrose-p3-rhombs",
                "adjacency_mode": "vertex",
                "sizing_mode": "patch_depth",
                "width": None,
                "height": None,
                "patch_depth": 4,
            },
        )
        self.assertEqual(
            parse_topology_spec({"topology_spec": {"tiling_family": "square", "adjacency_mode": "vertex"}}),
            {
                "tiling_family": "square",
                "adjacency_mode": "edge",
                "sizing_mode": "grid",
                "width": None,
                "height": None,
                "patch_depth": None,
            },
        )
        self.assertIsNone(parse_topology_spec({}))

        with self.assertRaises(RequestValidationError):
            parse_topology_spec({"topology_spec": {"tiling_family": "zigzag"}})
        with self.assertRaises(RequestValidationError):
            parse_topology_spec({"topology_spec": {"tiling_family": "square", "width": "bad"}})
        with self.assertRaises(RequestValidationError):
            parse_topology_spec({"topology_spec": []})


if __name__ == "__main__":
    unittest.main()
