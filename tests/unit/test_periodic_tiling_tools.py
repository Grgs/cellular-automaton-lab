from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from backend.simulation.periodic_face_tilings import (
    PERIODIC_FACE_TILING_GEOMETRIES,
    _ordered_periodic_geometries,
)
from backend.simulation.topology_implementation_registry import get_topology_implementation
from tools.add_periodic_tiling import (
    InstallMetadata,
    PlannedWrite,
    apply_install_plan,
    build_install_plan,
)
from tools.generate_tiling_preview import update_preview_source
from tools.inspect_tiling_svg import inspect_svg, render_sketch_starter
from tools.regenerate_periodic_catalog import (
    discover_catalog_sources,
    refresh_bootstrap_budget_source,
)

ROOT = Path(__file__).resolve().parents[2]


class PeriodicRegistryDiscoveryTests(unittest.TestCase):
    def test_every_descriptor_is_automatically_a_periodic_implementation(self) -> None:
        for geometry in PERIODIC_FACE_TILING_GEOMETRIES:
            with self.subTest(geometry=geometry):
                implementation = get_topology_implementation(geometry)
                self.assertEqual(implementation.geometry_key, geometry)
                self.assertEqual(implementation.builder_kind, "periodic_face")
                self.assertEqual(implementation.render_kind, "polygon_periodic")

    def test_orphan_descriptor_remains_importable_for_reconciliation(self) -> None:
        ordered = _ordered_periodic_geometries(frozenset({"square", "orphan-periodic"}))

        self.assertIn("orphan-periodic", ordered)
        self.assertEqual(ordered[-1], "orphan-periodic")


class PreviewSourceUpdateTests(unittest.TestCase):
    def test_adds_then_replaces_one_generated_entry(self) -> None:
        source = (
            "export const POLYGON_PREVIEW_DATA: Readonly<Record<string, string>> = {\n"
            '    existing: "0:0,0 1,0 1,1",\n'
            "};\n"
        )

        added, changed = update_preview_source(source, "new-tiling", "toneClay:0,0 1,0 0,1")
        current, changed_again = update_preview_source(added, "new-tiling", "toneCream:0,0 2,0 0,2")
        unchanged, is_stale = update_preview_source(current, "new-tiling", "toneCream:0,0 2,0 0,2")

        self.assertTrue(changed)
        self.assertTrue(changed_again)
        self.assertFalse(is_stale)
        self.assertEqual(unchanged, current)
        self.assertEqual(current.count('"new-tiling"'), 1)
        self.assertIn("toneCream:0,0 2,0 0,2", current)


class InspectTilingSvgTests(unittest.TestCase):
    def test_classifies_regular_polygons_and_reports_repeated_translations(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
          <g style="stroke:#000;fill-opacity:00"><path d="M 0,0 3,0 3,3 0,3"/></g>
          <polygon points="0,0 1,0 1,1 0,1"/>
          <polygon points="2,0 3,0 3,1 2,1"/>
          <polygon points="0,2 1,2 1,3 0,3"/>
          <polygon points="2,2 3,2 3,3 2,3"/>
          <polygon points="4,0 5,0 5.5,0.866025 4.5,0.866025"/>
        </svg>"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "squares.svg"
            path.write_text(svg, encoding="utf-8")
            inspection = inspect_svg(path)
            starter = render_sketch_starter(path, inspection)

        self.assertEqual(inspection.kind_counts, {"polygon-4": 1, "square": 4})
        self.assertEqual(inspection.regular_polygon_count, 4)
        self.assertIn((2.0, 0.0, 2), inspection.candidate_translations)
        self.assertIn((0.0, 2.0, 2), inspection.candidate_translations)
        self.assertIn('GEOMETRY = "replace-me"', starter)
        self.assertIn("Reduce this sampled patch", starter)
        compile(starter, "starter.py", "exec")


class AddPeriodicTilingTests(unittest.TestCase):
    def _write_root_inputs(self, root: Path) -> Path:
        manifest_path = root / "backend/simulation/topology_family_manifest.py"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(
            (ROOT / "backend/simulation/topology_family_manifest.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        palette_path = root / "frontend/canvas/family-dead-palette-manifest.json"
        palette_path.parent.mkdir(parents=True)
        palette_path.write_text('{\n  "families": [\n  ]\n}\n', encoding="utf-8")
        preview_path = root / "frontend/controls/tiling-preview-data.ts"
        preview_path.parent.mkdir(parents=True)
        preview_path.write_text(
            "export const POLYGON_PREVIEW_DATA: Readonly<Record<string, string>> = {\n};\n",
            encoding="utf-8",
        )
        sketch_path = root / "candidate.py"
        sketch_path.write_text(
            """from typing import Any
GEOMETRY = "tool-test-square"
LABEL = "Tool Test Square"
BASE_EDGE = 1.0
CELL_WIDTH = 1.0
CELL_HEIGHT = 1.0
FACES: list[dict[str, Any]] = [
    {"slot": "s", "kind": "square", "prefix": "s", "vertices": ((0, 0), (1, 0), (1, 1), (0, 1))},
]
""",
            encoding="utf-8",
        )
        return sketch_path

    def test_build_plan_covers_every_handled_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sketch_path = self._write_root_inputs(root)
            metadata = InstallMetadata(
                source_url="https://example.org/square.svg",
                picker_order=999,
                default_cell_size=12,
                min_cell_size=8,
                max_cell_size=20,
                default_rule="life-b2-s23",
                palette_tokens={"square": "toneStone"},
            )
            writes = build_install_plan(sketch_path, metadata, root=root, patch_size=3)

        relative_paths = {write.path.relative_to(root).as_posix() for write in writes}
        self.assertEqual(
            relative_paths,
            {
                "backend/simulation/data/periodic_face_patterns/tool-test-square.json",
                "backend/simulation/reference_specs/periodic/tool_test_square.py",
                "backend/simulation/topology_family_manifest.py",
                "frontend/canvas/family-dead-palette-manifest.json",
                "frontend/controls/tiling-preview-data.ts",
                "tools/sketch_examples/tool_test_square.py",
            },
        )
        manifest = next(
            write.content for write in writes if write.path.name == "topology_family_manifest.py"
        )
        palette = next(
            write.content
            for write in writes
            if write.path.name == "family-dead-palette-manifest.json"
        )
        preview = next(
            write.content for write in writes if write.path.name == "tiling-preview-data.ts"
        )
        compile(manifest, "topology_family_manifest.py", "exec")
        json.loads(palette)
        self.assertIn("TOOL_TEST_SQUARE_GEOMETRY", manifest)
        self.assertIn("picker_order=999", manifest)
        self.assertIn("toneStone:", preview)

    def test_apply_plan_rolls_back_when_generation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "existing.txt"
            created = root / "created.txt"
            bootstrap = root / "frontend/test-fixtures/bootstrap-data.json"
            existing.write_text("before", encoding="utf-8")
            bootstrap.parent.mkdir(parents=True)
            bootstrap.write_text("bootstrap-before", encoding="utf-8")
            writes = (
                PlannedWrite(existing, "after"),
                PlannedWrite(created, "created"),
            )

            with mock.patch(
                "tools.add_periodic_tiling._run", side_effect=RuntimeError("generation failed")
            ):
                with self.assertRaisesRegex(RuntimeError, "generation failed"):
                    apply_install_plan(writes, root=root)

            self.assertEqual(existing.read_text(encoding="utf-8"), "before")
            self.assertFalse(created.exists())
            self.assertEqual(bootstrap.read_text(encoding="utf-8"), "bootstrap-before")

    def test_reconcile_upserts_an_existing_installation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sketch_path = self._write_root_inputs(root)
            original_metadata = InstallMetadata(
                source_url="https://example.org/square.svg",
                picker_order=999,
                default_cell_size=12,
                min_cell_size=8,
                max_cell_size=20,
                default_rule="life-b2-s23",
                palette_tokens={"square": "toneStone"},
            )
            for write in build_install_plan(
                sketch_path,
                original_metadata,
                root=root,
                patch_size=3,
            ):
                write.path.parent.mkdir(parents=True, exist_ok=True)
                write.path.write_text(write.content, encoding="utf-8")

            manifest_path = root / "backend/simulation/topology_family_manifest.py"
            manifest_path.write_text(
                manifest_path.read_text(encoding="utf-8").replace(
                    "TOOL_TEST_SQUARE_GEOMETRY",
                    "LEGACY_TOOL_TEST_SQUARE_GEOMETRY",
                ),
                encoding="utf-8",
            )
            reference_path = (
                root / "backend/simulation/reference_specs/periodic/tool_test_square.py"
            )
            legacy_reference_path = reference_path.with_name("legacy_square_reference.py")
            reference_path.rename(legacy_reference_path)

            updated_metadata = InstallMetadata(
                source_url="https://example.org/rebased-square.svg",
                picker_order=1001,
                default_cell_size=14,
                min_cell_size=9,
                max_cell_size=22,
                default_rule="conway",
                palette_tokens={"square": "toneCream"},
            )
            writes = build_install_plan(
                sketch_path,
                updated_metadata,
                root=root,
                patch_size=3,
                reconcile=True,
            )

        contents = {write.path.relative_to(root).as_posix(): write.content for write in writes}
        manifest = contents["backend/simulation/topology_family_manifest.py"]
        palette = json.loads(contents["frontend/canvas/family-dead-palette-manifest.json"])
        compile(manifest, "topology_family_manifest.py", "exec")
        self.assertEqual(manifest.count("LEGACY_TOOL_TEST_SQUARE_GEOMETRY:"), 1)
        self.assertNotIn("    TOOL_TEST_SQUARE_GEOMETRY:", manifest)
        self.assertIn("picker_order=1001", manifest)
        self.assertIn("CELL_SIZE_CONTROL, 14, 9, 22", manifest)
        family = next(
            item for item in palette["families"] if item["geometry"] == "tool-test-square"
        )
        self.assertEqual(len(family["variants"]), 1)
        self.assertEqual(family["variants"][0]["color"]["token"], "toneCream")
        self.assertIn(
            "rebased-square.svg",
            contents["backend/simulation/reference_specs/periodic/legacy_square_reference.py"],
        )


class RegeneratePeriodicCatalogTests(unittest.TestCase):
    def test_discovers_all_descriptors_and_generated_sources(self) -> None:
        inventory = discover_catalog_sources(ROOT)

        self.assertTrue(inventory.descriptor_geometries <= inventory.reference_geometries)
        self.assertEqual(
            {source.geometry for source in inventory.sources},
            {
                "uniform-2-10-36-3262",
                "uniform-2-12-3262-346",
                "uniform-2-19-v1-36-346",
                "uniform-2-2-3122-34312",
                "uniform-3-4-36-3262-63",
            },
        )

    def test_bootstrap_budget_only_grows_when_headroom_is_low(self) -> None:
        source = json.dumps(
            {
                "categories": [
                    {"name": "bootstrap-data", "raw": 100, "gzip": 20},
                ]
            }
        )

        refreshed = json.loads(refresh_bootstrap_budget_source(source, b"x" * 100))
        category = refreshed["categories"][0]
        self.assertGreaterEqual(category["raw"], 115)
        self.assertGreaterEqual(category["gzip"], 20)

        stable_source = json.dumps(
            {
                "categories": [
                    {"name": "bootstrap-data", "raw": 10_000, "gzip": 1_000},
                ]
            }
        )
        stable = json.loads(refresh_bootstrap_budget_source(stable_source, b"small"))
        self.assertEqual(stable["categories"][0]["raw"], 10_000)
        self.assertEqual(stable["categories"][0]["gzip"], 1_000)


if __name__ == "__main__":
    unittest.main()
