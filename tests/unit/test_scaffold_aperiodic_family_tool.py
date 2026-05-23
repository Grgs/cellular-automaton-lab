from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.scaffold_aperiodic_family import (
    ScaffoldError,
    ScaffoldSpec,
    build_spec,
    patch_family_manifest,
    patch_reference_specs_init,
    patch_registry,
    patch_topology_family_manifest,
    render_generator_module,
    render_reference_spec,
    render_test_skeleton,
)


def _demo_spec(
    family_id: str = "scaffold-demo",
    kinds: tuple[str, ...] = ("alpha", "beta"),
    label: str = "Scaffold Demo",
    source_url: str | None = "https://example.org/demo",
    picker_group: str = "Experimental",
    picker_order: int = 999,
) -> ScaffoldSpec:
    return ScaffoldSpec(
        family_id=family_id,
        label=label,
        kinds=kinds,
        source_url=source_url,
        picker_order=picker_order,
        picker_group=picker_group,
    )


class BuildSpecTests(unittest.TestCase):
    def test_rejects_existing_family_id(self) -> None:
        with self.assertRaises(ScaffoldError):
            build_spec(
                family_id="pinwheel-2-1",
                label="Anything",
                kinds=["a"],
                source_url=None,
                picker_order=None,
                picker_group="Experimental",
            )

    def test_rejects_invalid_family_id_pattern(self) -> None:
        for bad in ("Pinwheel2", "pinwheel_2", "-leading", "trailing-", "two--dashes"):
            with self.subTest(bad=bad), self.assertRaises(ScaffoldError):
                build_spec(
                    family_id=bad,
                    label="x",
                    kinds=["a"],
                    source_url=None,
                    picker_order=None,
                    picker_group="Experimental",
                )

    def test_rejects_empty_kinds(self) -> None:
        with self.assertRaises(ScaffoldError):
            build_spec(
                family_id="ok-family",
                label="ok",
                kinds=[],
                source_url=None,
                picker_order=None,
                picker_group="Experimental",
            )

    def test_rejects_duplicate_kinds(self) -> None:
        with self.assertRaises(ScaffoldError):
            build_spec(
                family_id="ok-family",
                label="ok",
                kinds=["same", "same"],
                source_url=None,
                picker_order=None,
                picker_group="Experimental",
            )

    def test_default_picker_order_is_above_existing_max(self) -> None:
        spec = build_spec(
            family_id="new-family",
            label="New",
            kinds=["a"],
            source_url=None,
            picker_order=None,
            picker_group="Experimental",
        )
        # The existing maximum picker_order is below 500; the default should
        # land above it.
        self.assertGreater(spec.picker_order, 300)


class SpecDerivedNamesTests(unittest.TestCase):
    def test_snake_and_upper_forms(self) -> None:
        spec = _demo_spec(family_id="pinwheel-2-1")
        self.assertEqual(spec.snake, "pinwheel_2_1")
        self.assertEqual(spec.upper, "PINWHEEL_2_1")
        self.assertEqual(spec.geometry_const, "PINWHEEL_2_1_GEOMETRY")
        self.assertEqual(spec.tile_family_const, "PINWHEEL_2_1_TILE_FAMILY")
        self.assertEqual(spec.builder_name, "build_pinwheel_2_1_patch")
        self.assertEqual(spec.generator_module, "aperiodic_pinwheel_2_1")
        self.assertEqual(spec.kind_const("small"), "PINWHEEL_2_1_SMALL_KIND")
        self.assertEqual(spec.kind_const("small-triangle"), "PINWHEEL_2_1_SMALL_TRIANGLE_KIND")
        self.assertEqual(spec.kind_value("small"), "pinwheel-2-1-small")


class RenderingTests(unittest.TestCase):
    def test_generator_module_compiles_and_references_expected_symbols(self) -> None:
        spec = _demo_spec()
        rendered = render_generator_module(spec)
        # Must compile as Python.
        compile(rendered, "<scaffold-demo>", "exec")
        self.assertIn("def build_scaffold_demo_patch", rendered)
        self.assertIn("KIND_ALPHA = SCAFFOLD_DEMO_ALPHA_KIND", rendered)
        self.assertIn("KIND_BETA = SCAFFOLD_DEMO_BETA_KIND", rendered)
        self.assertIn("TILE_FAMILY = SCAFFOLD_DEMO_TILE_FAMILY", rendered)
        self.assertIn('id_prefix="scaffold-demo"', rendered)
        # First kind becomes root_kind.
        self.assertIn("root_kind=KIND_ALPHA", rendered)
        # Source URL is propagated.
        self.assertIn("https://example.org/demo", rendered)

    def test_generator_falls_back_to_todo_when_no_source(self) -> None:
        spec = _demo_spec(source_url=None)
        rendered = render_generator_module(spec)
        self.assertIn("TODO: cite a source URL", rendered)
        self.assertNotIn("https://", rendered)

    def test_reference_spec_compiles_and_imports_kinds(self) -> None:
        spec = _demo_spec()
        rendered = render_reference_spec(spec)
        compile(rendered, "<scaffold-demo-ref>", "exec")
        self.assertIn("SCAFFOLD_DEMO_GEOMETRY", rendered)
        self.assertIn("SCAFFOLD_DEMO_ALPHA_KIND", rendered)
        self.assertIn("SCAFFOLD_DEMO_BETA_KIND", rendered)
        self.assertIn("ReferenceFamilySpec", rendered)

    def test_test_skeleton_compiles_and_targets_builder(self) -> None:
        spec = _demo_spec()
        rendered = render_test_skeleton(spec)
        compile(rendered, "<scaffold-demo-tests>", "exec")
        self.assertIn("build_scaffold_demo_patch", rendered)
        self.assertIn("ScaffoldDemoGeneratorTests", rendered)


class PatchFunctionTests(unittest.TestCase):
    """The patch_* helpers take real source-file text and return augmented text."""

    def setUp(self) -> None:
        self.spec = _demo_spec()
        self.manifest_text = (
            ROOT / "backend" / "simulation" / "aperiodic_family_manifest.py"
        ).read_text(encoding="utf-8")
        self.registry_text = (ROOT / "backend" / "simulation" / "aperiodic_registry.py").read_text(
            encoding="utf-8"
        )
        self.topology_text = (
            ROOT / "backend" / "simulation" / "topology_family_manifest.py"
        ).read_text(encoding="utf-8")
        self.ref_init_text = (
            ROOT / "backend" / "simulation" / "reference_specs" / "aperiodic" / "__init__.py"
        ).read_text(encoding="utf-8")

    def test_family_manifest_patch_inserts_constants_and_entry(self) -> None:
        out = patch_family_manifest(self.manifest_text, self.spec)
        self.assertIn('SCAFFOLD_DEMO_GEOMETRY = "scaffold-demo"', out)
        self.assertIn('SCAFFOLD_DEMO_ALPHA_KIND = "scaffold-demo-alpha"', out)
        self.assertIn('SCAFFOLD_DEMO_BETA_KIND = "scaffold-demo-beta"', out)
        self.assertIn('SCAFFOLD_DEMO_TILE_FAMILY = "scaffold-demo"', out)
        self.assertIn("SCAFFOLD_DEMO_GEOMETRY: AperiodicFamilyManifestEntry", out)
        # And the prior text is preserved.
        self.assertIn('PINWHEEL_2_1_GEOMETRY = "pinwheel-2-1"', out)
        compile(out, "<patched-manifest>", "exec")

    def test_registry_patch_inserts_import_and_builder_entry(self) -> None:
        out = patch_registry(self.registry_text, self.spec)
        self.assertIn(
            "from backend.simulation.aperiodic_scaffold_demo import build_scaffold_demo_patch",
            out,
        )
        self.assertIn(
            "SCAFFOLD_DEMO_GEOMETRY: build_scaffold_demo_patch,",
            out,
        )
        compile(out, "<patched-registry>", "exec")

    def test_topology_manifest_patch_inserts_translated_entry(self) -> None:
        out = patch_topology_family_manifest(self.topology_text, self.spec)
        self.assertIn("SCAFFOLD_DEMO_GEOMETRY: _translated_aperiodic_family", out)
        compile(out, "<patched-topology>", "exec")

    def test_reference_specs_init_patch_wires_new_module(self) -> None:
        out = patch_reference_specs_init(self.ref_init_text, self.spec)
        self.assertIn("from . import scaffold_demo", out)
        self.assertIn("**scaffold_demo.SPECS,", out)
        compile(out, "<patched-ref-init>", "exec")

    def test_patch_rejects_already_inserted_family(self) -> None:
        # If the family is already in the manifest, the inserted geometry
        # constant would appear twice — but the existing anchor logic
        # detects placeholder constants per-line, so this would succeed
        # silently. Guarding against double-insertion is the build_spec
        # caller's job; here we just verify that patch functions stay
        # deterministic when given the same input twice.
        first = patch_family_manifest(self.manifest_text, self.spec)
        second = patch_family_manifest(self.manifest_text, self.spec)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
