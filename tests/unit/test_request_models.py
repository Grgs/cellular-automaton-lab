import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

try:
    from backend.web.request_models import (
        CellUpdatesPayloadModel,
        ConfigUpdateRequestModel,
        IdCellTargetModel,
        IdCellUpdateModel,
        ResetRequestModel,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.web.request_models import (
        CellUpdatesPayloadModel,
        ConfigUpdateRequestModel,
        IdCellTargetModel,
        IdCellUpdateModel,
        ResetRequestModel,
    )


class RequestModelTests(unittest.TestCase):
    def test_config_update_model_normalizes_blank_optional_fields(self) -> None:
        payload = ConfigUpdateRequestModel.model_validate({
            "speed": "",
            "rule": "",
            "topology_spec": {
                "tiling_family": "",
                "adjacency_mode": "",
                "sizing_mode": "",
                "width": "",
                "height": None,
                "patch_depth": "",
            },
        })

        self.assertIsNone(payload.speed)
        self.assertIsNone(payload.rule)
        assert payload.topology_spec is not None
        self.assertIsNone(payload.topology_spec.tiling_family)
        self.assertIsNone(payload.topology_spec.adjacency_mode)
        self.assertIsNone(payload.topology_spec.sizing_mode)
        self.assertIsNone(payload.topology_spec.width)
        self.assertIsNone(payload.topology_spec.height)
        self.assertIsNone(payload.topology_spec.patch_depth)

    def test_reset_request_model_parses_topology_spec_shape(self) -> None:
        payload = ResetRequestModel.model_validate({
            "topology_spec": {
                "tiling_family": "hex",
                "adjacency_mode": "edge",
                "width": "12",
                "height": 9,
                "patch_depth": "",
                "unsafe_size_override": "true",
            },
            "speed": "7.5",
            "rule": "hexlife",
            "randomize": True,
        })

        assert payload.topology_spec is not None
        self.assertEqual(payload.topology_spec.tiling_family, "hex")
        self.assertEqual(payload.topology_spec.adjacency_mode, "edge")
        self.assertEqual(payload.topology_spec.width, 12)
        self.assertEqual(payload.topology_spec.height, 9)
        self.assertEqual(payload.speed, 7.5)
        self.assertEqual(payload.rule, "hexlife")
        self.assertIsNone(payload.topology_spec.patch_depth)
        self.assertTrue(payload.topology_spec.unsafe_size_override)
        self.assertTrue(payload.randomize)

    def test_cell_target_model_requires_id_shape(self) -> None:
        self.assertEqual(
            IdCellTargetModel.model_validate({"id": "o:1:1"}).model_dump(),
            {"id": "o:1:1"},
        )

        with self.assertRaises(ValidationError):
            IdCellTargetModel.model_validate({"id": 123})

    def test_cell_update_model_requires_id_shape(self) -> None:
        self.assertEqual(
            IdCellUpdateModel.model_validate({"id": "tu:1:1", "state": True}).model_dump(),
            {"id": "tu:1:1", "state": 1},
        )

    def test_cell_updates_payload_requires_non_empty_list(self) -> None:
        payload = CellUpdatesPayloadModel.model_validate({
            "cells": [{"id": "c:1:1", "state": 1}],
        })
        self.assertEqual(
            [cell.to_payload() for cell in payload.cells],
            [{"id": "c:1:1", "state": 1}],
        )

        with self.assertRaises(ValidationError):
            CellUpdatesPayloadModel.model_validate({"cells": []})
        with self.assertRaises(ValidationError):
            CellUpdatesPayloadModel.model_validate({"cells": "bad"})


if __name__ == "__main__":
    unittest.main()
