"""Scaffold the boilerplate files for a new aperiodic tiling family.

This automates the mechanical part of `docs/ADDING_TOPOLOGIES.md` for an
aperiodic patch family. It does NOT solve the geometry (that's the
creative work) -- it stamps out the wiring so the new family loads, runs
through the registry, and reports its placeholder shape end-to-end.

Files created:

- ``backend/simulation/aperiodic_<family>.py``: generator skeleton with a
  trivial single-triangle root and TODO markers for the substitution rule.
- ``backend/simulation/reference_specs/aperiodic/<family>.py``: stub
  ReferenceFamilySpec.
- ``tests/unit/test_aperiodic_<family>.py``: minimal test skeleton.

The default generator skeleton targets the triangle-similarity
``ExactSimilaritySubstitution`` framework. The repo also has the hat-style
baked-metatile and affine-substitution frameworks; for those, pass
``--wiring-only`` to get a framework-neutral generator stub (a single triangle
that loads end-to-end) plus all the catalog wiring, and skip the
triangle-coupled test skeleton. See ``docs/ADDING_TOPOLOGIES.md`` for choosing
a framework.

Files edited (surgical anchor-based inserts):

- ``backend/simulation/aperiodic_family_manifest.py``: GEOMETRY + KIND +
  TILE_FAMILY constants and the manifest entry.
- ``backend/simulation/aperiodic_registry.py``: builder import + dispatch
  entry.
- ``backend/simulation/topology_family_manifest.py``: geometry constant
  import + sizing-policy entry.
- ``backend/simulation/reference_specs/aperiodic/__init__.py``: spec
  module wiring.

After scaffolding, the next steps (printed by the tool) are:

1. Implement the actual substitution geometry in the generator file.
2. Add a dead-palette entry under ``frontend/canvas/family-dead-palette-manifest.json``.
3. Regenerate fixtures / picker thumbnail / bootstrap data via the
   existing tools (also printed).

Usage::

    py -3 tools/scaffold_aperiodic_family.py \
        --family-id widget-monotile \
        --label "Widget Monotile" \
        --kind widget \
        --source-url https://example.org/widget

Use ``--dry-run`` to preview changes without writing.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Imported lazily so this module is importable without the full backend.
from backend.simulation.aperiodic_family_manifest import APERIODIC_FAMILY_MANIFEST
from tools._common import write_text_lf  # noqa: E402

_FAMILY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


class ScaffoldError(ValueError):
    pass


@dataclass(frozen=True)
class ScaffoldSpec:
    """Resolved naming + metadata for a new aperiodic family."""

    family_id: str  # "pinwheel-2-1"
    label: str  # "Pinwheel 2-1"
    kinds: tuple[str, ...]  # ("small", "large")
    source_url: str | None
    picker_order: int
    picker_group: str  # "Experimental"

    @property
    def snake(self) -> str:
        """Snake-case identifier for module / function names."""
        return self.family_id.replace("-", "_")

    @property
    def upper(self) -> str:
        """Upper snake-case for the GEOMETRY / KIND constants."""
        return self.snake.upper()

    @property
    def geometry_const(self) -> str:
        return f"{self.upper}_GEOMETRY"

    @property
    def tile_family_const(self) -> str:
        return f"{self.upper}_TILE_FAMILY"

    @property
    def builder_name(self) -> str:
        return f"build_{self.snake}_patch"

    @property
    def generator_module(self) -> str:
        return f"aperiodic_{self.snake}"

    def kind_const(self, kind: str) -> str:
        """``small`` -> ``PINWHEEL_2_1_SMALL_KIND``."""
        return f"{self.upper}_{kind.upper().replace('-', '_')}_KIND"

    def kind_value(self, kind: str) -> str:
        """``small`` for family ``pinwheel-2-1`` -> ``pinwheel-2-1-small``."""
        return f"{self.family_id}-{kind}"


def _normalize_kinds(raw_kinds: list[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for kind in raw_kinds:
        kind_lower = kind.strip().lower()
        if not _FAMILY_ID_PATTERN.match(kind_lower):
            raise ScaffoldError(
                f"Cell kind {kind!r} must be lowercase, kebab-case (letters, digits, hyphens)."
            )
        cleaned.append(kind_lower)
    if not cleaned:
        raise ScaffoldError("At least one --kind is required.")
    if len(set(cleaned)) != len(cleaned):
        raise ScaffoldError("Duplicate --kind values.")
    return tuple(cleaned)


def _default_picker_order(existing_orders: list[int]) -> int:
    if not existing_orders:
        return 200
    return max(existing_orders) + 5


def build_spec(
    *,
    family_id: str,
    label: str,
    kinds: list[str],
    source_url: str | None,
    picker_order: int | None,
    picker_group: str,
) -> ScaffoldSpec:
    if not _FAMILY_ID_PATTERN.match(family_id):
        raise ScaffoldError(
            f"--family-id {family_id!r} must be lowercase kebab-case (letters, digits, hyphens)."
        )
    if family_id in APERIODIC_FAMILY_MANIFEST:
        raise ScaffoldError(
            f"--family-id {family_id!r} is already registered in APERIODIC_FAMILY_MANIFEST."
        )
    if picker_group not in ("Aperiodic", "Experimental"):
        raise ScaffoldError(
            f"--picker-group must be 'Aperiodic' or 'Experimental' (got {picker_group!r})."
        )
    if not label.strip():
        raise ScaffoldError("--label cannot be empty.")
    resolved_order = (
        picker_order
        if picker_order is not None
        else _default_picker_order(
            [entry.picker_order for entry in APERIODIC_FAMILY_MANIFEST.values()]
        )
    )
    return ScaffoldSpec(
        family_id=family_id,
        label=label.strip(),
        kinds=_normalize_kinds(kinds),
        source_url=source_url.strip() if source_url else None,
        picker_order=resolved_order,
        picker_group=picker_group,
    )


# ---------------------------------------------------------------------------
# File rendering helpers
# ---------------------------------------------------------------------------


def render_generator_module(spec: ScaffoldSpec) -> str:
    kind_consts_block = "\n".join(
        f"KIND_{kind.upper().replace('-', '_')} = {spec.kind_const(kind)}" for kind in spec.kinds
    )
    children_lines = ",\n    ".join(
        f"(KIND_{kind.upper().replace('-', '_')}, _BASE_TRIANGLE)" for kind in spec.kinds
    )
    source_line = (
        f"\nSource: {spec.source_url}\n" if spec.source_url else "\nTODO: cite a source URL.\n"
    )
    kind_const_imports = ",\n    ".join(spec.kind_const(kind) for kind in spec.kinds)
    return f'''"""Exact-arithmetic generator for the {spec.label} substitution.

TODO: replace this placeholder skeleton with the real prototile geometry
and subdivision rule. The shape below is a single trivial unit triangle
with the subdivision rule "each parent maps to one child per kind, all
equal to the parent" -- it is structurally valid (so the family loads
end-to-end) but mathematically meaningless.
{source_line}"""

from __future__ import annotations

from fractions import Fraction

from backend.simulation.aperiodic_exact_similarity import (
    ExactSimilaritySubstitution,
    ExactTriangle,
)
from backend.simulation.aperiodic_family_manifest import (
    {kind_const_imports},
    {spec.tile_family_const},
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    ExactPatchRecord,
)


# Tokens re-exported for callers that already imported them from this module.
TILE_FAMILY = {spec.tile_family_const}
{kind_consts_block}


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)


# TODO: replace with the real prototile shape. The default is a unit
# right triangle so the wiring loads.
_BASE_TRIANGLE: ExactTriangle = (
    (_ZERO, _ZERO),
    (_ONE, _ZERO),
    (_ZERO, _ONE),
)


# TODO: define the children of the substitution in local coordinates of
# ``_BASE_TRIANGLE``. Each entry is ``(kind, triangle)``.
_ALL_CHILDREN: tuple[tuple[str, ExactTriangle], ...] = (
    {children_lines},
)


# TODO: define the patch seed (one entry per root triangle).
_ROOT_TRIANGLES: tuple[ExactTriangle, ...] = (_BASE_TRIANGLE,)


# TODO: real inflation factor for the substitution (e.g. ``math.sqrt(5)``
# for Conway-Radin pinwheel).
INFLATION_FACTOR = 1.0


_SUBSTITUTION = ExactSimilaritySubstitution(
    base_triangle=_BASE_TRIANGLE,
    children=_ALL_CHILDREN,
    roots=_ROOT_TRIANGLES,
    id_prefix="{spec.family_id}",
    tile_family=TILE_FAMILY,
    root_kind=KIND_{spec.kinds[0].upper().replace("-", "_")},
    inflation_factor=INFLATION_FACTOR,
)


def _subdivide(parent: ExactTriangle) -> tuple[tuple[str, ExactTriangle], ...]:
    """Per-parent subdivision (re-exported for test imports)."""
    return _SUBSTITUTION.subdivide(parent)


def collect_{spec.snake}_exact_records(patch_depth: int) -> tuple[ExactPatchRecord, ...]:
    return _SUBSTITUTION.collect_exact_records(patch_depth)


def {spec.builder_name}(patch_depth: int) -> AperiodicPatch:
    """Build an AperiodicPatch for the {spec.label} substitution.

    TODO: confirm whether ``segment_overlap`` (non-edge-to-edge) or the
    default ``shared_edge`` neighbor mode is appropriate, and configure
    it on ``_SUBSTITUTION`` accordingly.
    """
    return _SUBSTITUTION.build_patch(patch_depth)
'''


def render_reference_spec(spec: ScaffoldSpec) -> str:
    kind_imports = ",\n    ".join(
        [spec.geometry_const] + [spec.kind_const(kind) for kind in spec.kinds]
    )
    metadata_block = ",\n            ".join(
        f"""MetadataRequirement(
                kind={spec.kind_const(kind)},
                fields=("tile_family", "orientation_token", "chirality_token"),
            )"""
        for kind in spec.kinds
    )
    source_tuple = (
        f'("{spec.source_url}",)'
        if spec.source_url
        else "(\n            # TODO: add literature URL\n        )"
    )
    return f"""from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    {kind_imports},
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label


# TODO: replace placeholder depth_expectations with the real per-depth
# cell counts and adjacency requirements once the substitution geometry
# is finalized.
SPECS = {{
    {spec.geometry_const}: ReferenceFamilySpec(
        geometry={spec.geometry_const},
        display_name=_reference_label({spec.geometry_const}),
        source_urls={source_tuple},
        canonical_root_seed_policy="TODO: describe the seed",
        allowed_public_cell_kinds=_public_cell_kinds({spec.geometry_const}),
        required_metadata=(
            {metadata_block},
        ),
        depth_expectations={{
            # TODO: replace with per-depth ReferenceDepthExpectation entries
            # (exact_total_cells, expected_kind_counts, required_adjacency_pairs)
            # derived from the actual substitution; see e.g. pinwheel_2_1.py.
            0: ReferenceDepthExpectation(exact_total_cells=1),
        }},
        notes=("TODO: cite the substitution source and describe the seed.",),
    ),
}}
"""


def render_test_skeleton(spec: ScaffoldSpec) -> str:
    return f"""from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.{spec.generator_module} import (
    _ALL_CHILDREN,
    _BASE_TRIANGLE,
    _subdivide,
    {spec.builder_name},
    collect_{spec.snake}_exact_records,
)


class {spec.snake.title().replace("_", "")}GeneratorTests(unittest.TestCase):
    def test_patch_at_depth_zero_has_root_count(self) -> None:
        patch = {spec.builder_name}(0)
        self.assertGreater(len(patch.cells), 0)

    def test_subdivide_returns_declared_kinds(self) -> None:
        children = _subdivide(_BASE_TRIANGLE)
        kinds = {{kind for kind, _ in children}}
        self.assertEqual(kinds, {{kind for kind, _ in _ALL_CHILDREN}})

    def test_collect_exact_records_returns_records(self) -> None:
        records = collect_{spec.snake}_exact_records(0)
        self.assertGreater(len(records), 0)


if __name__ == "__main__":
    unittest.main()
"""


# ---------------------------------------------------------------------------
# Anchor-based inserts into existing source files
# ---------------------------------------------------------------------------


def _insert_before(text: str, anchor: str, insertion: str, *, filename: str) -> str:
    if anchor not in text:
        raise ScaffoldError(
            f"Cannot find anchor in {filename}: {anchor!r}. "
            "The file may have been refactored; rerun the scaffold against an unmodified tree."
        )
    occurrences = text.count(anchor)
    if occurrences != 1:
        raise ScaffoldError(
            f"Anchor not unique in {filename} ({occurrences} occurrences): {anchor!r}."
        )
    return text.replace(anchor, insertion + anchor, 1)


def _insert_sorted_line_in_import_block(
    text: str,
    import_header: str,
    line: str,
    *,
    filename: str,
) -> str:
    occurrences = text.count(import_header)
    if occurrences != 1:
        raise ScaffoldError(
            f"Import block header not unique in {filename} "
            f"({occurrences} occurrences): {import_header!r}."
        )
    body_start = text.index(import_header) + len(import_header)
    body_end = text.find(")\n", body_start)
    if body_end == -1:
        raise ScaffoldError(f"Cannot find closing parenthesis for import block in {filename}.")

    lines = text[body_start:body_end].splitlines(keepends=True)
    if line in lines:
        return text
    lines.append(line)
    return text[:body_start] + "".join(sorted(lines)) + text[body_end:]


def patch_family_manifest(text: str, spec: ScaffoldSpec) -> str:
    # 1. Geometry constant: append after the last `*_GEOMETRY = "..."` line.
    geom_const_block = f'{spec.geometry_const} = "{spec.family_id}"\n'
    geom_anchor_match = list(re.finditer(r'^[A-Z0-9_]+_GEOMETRY = "[^"]+"\n', text, re.MULTILINE))
    if not geom_anchor_match:
        raise ScaffoldError("Cannot find any *_GEOMETRY constant in aperiodic_family_manifest.py.")
    insertion_point = geom_anchor_match[-1].end()
    text = text[:insertion_point] + geom_const_block + text[insertion_point:]

    # 2. Kind constants: append after the last `*_KIND = "..."` line.
    kind_lines = "".join(
        f'{spec.kind_const(kind)} = "{spec.kind_value(kind)}"\n' for kind in spec.kinds
    )
    kind_anchor_match = list(re.finditer(r'^[A-Z0-9_]+_KIND = "[^"]+"\n', text, re.MULTILINE))
    if not kind_anchor_match:
        raise ScaffoldError("Cannot find any *_KIND constant in aperiodic_family_manifest.py.")
    insertion_point = kind_anchor_match[-1].end()
    text = text[:insertion_point] + kind_lines + text[insertion_point:]

    # 3. Tile family: append after the last `*_TILE_FAMILY = ...` line.
    tile_family_line = f'{spec.tile_family_const} = "{spec.family_id}"\n'
    tile_anchor_match = list(re.finditer(r"^[A-Z0-9_]+_TILE_FAMILY = .+\n", text, re.MULTILINE))
    if not tile_anchor_match:
        raise ScaffoldError(
            "Cannot find any *_TILE_FAMILY constant in aperiodic_family_manifest.py."
        )
    insertion_point = tile_anchor_match[-1].end()
    text = text[:insertion_point] + tile_family_line + text[insertion_point:]

    # 4. Manifest entry: insert before the closing `}` of APERIODIC_FAMILY_MANIFEST.
    public_kinds_tuple = ", ".join(spec.kind_const(kind) for kind in spec.kinds)
    if len(spec.kinds) == 1:
        public_kinds_tuple += ","
    entry_block = f"""    {spec.geometry_const}: AperiodicFamilyManifestEntry(
        geometry={spec.geometry_const},
        catalog_label="{spec.label}",
        reference_label="{spec.label}",
        picker_group="{spec.picker_group}",
        picker_order={spec.picker_order},
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        # TODO: switch implementation_status to true_substitution / exact_affine
        # once the geometry is finalized; leave as canonical_patch for the
        # placeholder skeleton so verifier doesn't gate on partial work.
        implementation_status="canonical_patch",
        public_cell_kinds=({public_kinds_tuple}),
        promotion_blocker=(
            "Experimental until {spec.label} geometry is implemented and visually reviewed."
        ),
    ),
"""
    closing_anchor = "}\n\nAPERIODIC_FAMILY_IDS"  # `APERIODIC_FAMILY_MANIFEST = { ... }` close
    return _insert_before(
        text, closing_anchor, entry_block, filename="aperiodic_family_manifest.py"
    )


def patch_registry(text: str, spec: ScaffoldSpec) -> str:
    # 1. Add geometry to the manifest-import block.
    text = _insert_sorted_line_in_import_block(
        text,
        "from backend.simulation.aperiodic_family_manifest import (\n",
        f"    {spec.geometry_const},\n",
        filename="aperiodic_registry.py",
    )

    # 2. Builder import: append after the last `from backend.simulation.aperiodic_*` import.
    builder_import_line = (
        f"from backend.simulation.{spec.generator_module} import {spec.builder_name}\n"
    )
    builder_anchor_matches = list(
        re.finditer(
            r"^from backend\.simulation\.aperiodic_[a-z0-9_]+ import build_[a-z0-9_]+_patch\n",
            text,
            re.MULTILINE,
        )
    )
    if not builder_anchor_matches:
        raise ScaffoldError("Cannot find aperiodic builder imports in aperiodic_registry.py.")
    insertion_point = builder_anchor_matches[-1].end()
    text = text[:insertion_point] + builder_import_line + text[insertion_point:]

    # 3. Builders dict entry: insert before the `}` closing _APERIODIC_PATCH_BUILDERS.
    entry_line = f"    {spec.geometry_const}: {spec.builder_name},\n"
    closing_anchor = "}\n\n_APERIODIC_FAMILIES"
    return _insert_before(text, closing_anchor, entry_line, filename="aperiodic_registry.py")


def patch_topology_family_manifest(text: str, spec: ScaffoldSpec) -> str:
    # 1. Add geometry to the manifest-import block.
    text = _insert_sorted_line_in_import_block(
        text,
        "from backend.simulation.aperiodic_family_manifest import (\n",
        f"    {spec.geometry_const},\n",
        filename="topology_family_manifest.py",
    )

    # 2. TOPOLOGY_FAMILY_MANIFEST entry: insert before its closing `}` block.
    entry_block = f"""    {spec.geometry_const}: _translated_aperiodic_family(
        {spec.geometry_const},
        # TODO: tune patch depth ceiling once cell-count growth is known.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 4),
    ),
"""
    closing_anchor = "}\n\nGEOMETRY_MINIMUM_GRID_DIMENSIONS"
    return _insert_before(text, closing_anchor, entry_block, filename="topology_family_manifest.py")


def patch_reference_specs_init(text: str, spec: ScaffoldSpec) -> str:
    # 1. Add `from . import <family>`
    text = _insert_sorted_line_in_import_block(
        text,
        "from . import (\n",
        f"    {spec.snake},\n",
        filename="reference_specs/aperiodic/__init__.py",
    )

    # 2. Add `**<family>.SPECS,` inside APERIODIC_REFERENCE_FAMILY_SPECS dict.
    specs_line = f"    **{spec.snake}.SPECS,\n"
    closing_anchor = "}\n\n__all__ = "
    return _insert_before(
        text,
        closing_anchor,
        specs_line,
        filename="reference_specs/aperiodic/__init__.py",
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlannedWrite:
    """A pending file write — created or edited."""

    path: Path
    contents: str
    is_new: bool


def render_neutral_generator_module(spec: ScaffoldSpec) -> str:
    """Render a framework-neutral generator stub for ``--wiring-only``.

    Unlike :func:`render_generator_module`, this does not assume the
    triangle-similarity (:class:`ExactSimilaritySubstitution`) framework. It
    emits a single trivial triangle through ``patch_from_records`` so the family
    wires up and loads end-to-end, leaving the author free to drop in any
    framework (baked metatile, affine substitution, exact similarity, ...).
    """
    source_line = (
        f"\nSource: {spec.source_url}\n" if spec.source_url else "\nTODO: cite a source URL.\n"
    )
    first_kind_const = spec.kind_const(spec.kinds[0])
    return f'''"""Generator for the {spec.label} aperiodic family.

TODO: replace this framework-neutral placeholder with the real prototile
geometry and substitution rule. It emits a single trivial triangle so the
family loads end-to-end; choose whichever substitution framework fits (see
docs/ADDING_TOPOLOGIES.md, "Choosing an aperiodic generator framework").
{source_line}"""

from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    {first_kind_const},
    {spec.tile_family_const},
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    patch_from_records,
)


def {spec.builder_name}(patch_depth: int) -> AperiodicPatch:
    # TODO: build the real depth-``patch_depth`` patch. Placeholder: one tile.
    records: list[PatchRecord] = [
        {{
            "id": "{spec.family_id}:0",
            "kind": {first_kind_const},
            "center": (0.0, 0.0),
            "vertices": ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)),
            "tile_family": {spec.tile_family_const},
        }}
    ]
    return patch_from_records(max(0, int(patch_depth)), records)
'''


def plan_writes(
    spec: ScaffoldSpec, repo_root: Path, *, wiring_only: bool = False
) -> list[PlannedWrite]:
    plans: list[PlannedWrite] = []

    # New files
    generator_path = repo_root / "backend" / "simulation" / f"{spec.generator_module}.py"
    if generator_path.exists():
        raise ScaffoldError(f"Generator already exists: {generator_path}")
    generator_source = (
        render_neutral_generator_module(spec) if wiring_only else render_generator_module(spec)
    )
    plans.append(PlannedWrite(generator_path, generator_source, is_new=True))

    ref_spec_path = (
        repo_root / "backend" / "simulation" / "reference_specs" / "aperiodic" / f"{spec.snake}.py"
    )
    if ref_spec_path.exists():
        raise ScaffoldError(f"Reference spec already exists: {ref_spec_path}")
    plans.append(PlannedWrite(ref_spec_path, render_reference_spec(spec), is_new=True))

    # The default test skeleton imports the triangle-substitution generator's
    # private API (_BASE_TRIANGLE / _subdivide / ...), so it only fits the
    # ExactSimilaritySubstitution framework. In --wiring-only mode the author
    # supplies their own generator and writes a focused test to match it.
    if not wiring_only:
        test_path = repo_root / "tests" / "unit" / f"test_aperiodic_{spec.snake}.py"
        if test_path.exists():
            raise ScaffoldError(f"Test skeleton already exists: {test_path}")
        plans.append(PlannedWrite(test_path, render_test_skeleton(spec), is_new=True))

    # Edited files
    manifest_path = repo_root / "backend" / "simulation" / "aperiodic_family_manifest.py"
    plans.append(
        PlannedWrite(
            manifest_path,
            patch_family_manifest(manifest_path.read_text(encoding="utf-8"), spec),
            is_new=False,
        )
    )

    registry_path = repo_root / "backend" / "simulation" / "aperiodic_registry.py"
    plans.append(
        PlannedWrite(
            registry_path,
            patch_registry(registry_path.read_text(encoding="utf-8"), spec),
            is_new=False,
        )
    )

    topology_manifest_path = repo_root / "backend" / "simulation" / "topology_family_manifest.py"
    plans.append(
        PlannedWrite(
            topology_manifest_path,
            patch_topology_family_manifest(
                topology_manifest_path.read_text(encoding="utf-8"), spec
            ),
            is_new=False,
        )
    )

    ref_init_path = (
        repo_root / "backend" / "simulation" / "reference_specs" / "aperiodic" / "__init__.py"
    )
    plans.append(
        PlannedWrite(
            ref_init_path,
            patch_reference_specs_init(ref_init_path.read_text(encoding="utf-8"), spec),
            is_new=False,
        )
    )

    return plans


def apply_writes(plans: list[PlannedWrite]) -> None:
    for plan in plans:
        plan.path.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(plan.path, plan.contents)


def format_generated_python(plans: list[PlannedWrite]) -> None:
    """Run ruff import-fix + format on the touched Python files.

    The rendered templates and the anchor-based import inserts are not
    guaranteed to land in ruff's preferred import order, so without this the
    scaffolded files would fail the ``ruff check`` / ``ruff format`` pre-commit
    hooks until the author fixed them by hand. Best-effort: a missing ruff is
    reported, not fatal.
    """
    python_files = [str(plan.path) for plan in plans if plan.path.suffix == ".py"]
    if not python_files:
        return
    commands = (
        [sys.executable, "-m", "ruff", "check", "--fix", "--quiet", *python_files],
        [sys.executable, "-m", "ruff", "format", "--quiet", *python_files],
    )
    for command in commands:
        try:
            subprocess.run(command, check=False)
        except FileNotFoundError:
            print(
                "  (ruff not found; run `ruff check --fix` and `ruff format` on the "
                "generated files before committing)",
                file=sys.stderr,
            )
            return


def print_followups(spec: ScaffoldSpec, *, wiring_only: bool = False) -> None:
    print()
    print("Next steps (in order):")
    print(
        f"  1. Implement the substitution geometry in backend/simulation/{spec.generator_module}.py"
    )
    if wiring_only:
        print(
            "     (replace the framework-neutral single-triangle placeholder with your "
            "real generator; see docs/ADDING_TOPOLOGIES.md for choosing a framework)."
        )
    else:
        print(
            "     (replace the placeholder _BASE_TRIANGLE / _ALL_CHILDREN / "
            "_ROOT_TRIANGLES / INFLATION_FACTOR)."
        )
    print(
        f"  2. Fill in real per-depth expectations in "
        f"backend/simulation/reference_specs/aperiodic/{spec.snake}.py"
    )
    print("  3. Add dead-palette entries to frontend/canvas/family-dead-palette-manifest.json")
    print(f"     for kinds: {', '.join(spec.kinds)}")
    print()
    print("Then regenerate generated artifacts:")
    print(f"  python -m tools tilings preview --aperiodic --geometry {spec.family_id} --write")
    print(
        f"  python -m tools fixtures reference --mode canonical --geometry {spec.family_id} --depth 1"
    )
    print(
        f"  python -m tools fixtures reference --mode canonical --geometry {spec.family_id} --depth 3"
    )
    print(f"  python -m tools fixtures frontend --fixture {spec.family_id}-depth-3")
    print("  python -m tools bootstrap export frontend/test-fixtures/bootstrap-data.json")
    print()
    print("Then validate:")
    print("  python -m tools tilings validate")
    print("  python -m tools tilings verify")
    if wiring_only:
        print(
            f"  (no test skeleton was generated; add a focused "
            f"tests/unit/test_aperiodic_{spec.snake}.py for your generator)"
        )
    else:
        print(f"  python -m pytest tests/unit/test_aperiodic_{spec.snake}.py")
    print()
    print("Inherited catalog-wide coverage (do not create duplicate per-family tests):")
    print("  - registration, implementation dispatch, topology structure, and graph validity")
    print("  - reference-spec coverage, picker preview coverage, and frontend adapter dispatch")
    print("Keep the generated family test focused on substitution-specific behavior and fixtures.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scaffold the boilerplate for a new aperiodic tiling family.",
    )
    parser.add_argument(
        "--family-id",
        required=True,
        help="Kebab-case identifier (e.g. 'pinwheel-2-1'). Becomes the geometry key.",
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Human-readable label (e.g. 'Pinwheel 2-1').",
    )
    parser.add_argument(
        "--kind",
        action="append",
        default=[],
        dest="kinds",
        help=("Cell kind name in kebab-case (e.g. 'small-triangle'). Repeat for multiple kinds."),
    )
    parser.add_argument(
        "--source-url",
        default=None,
        help="Literature citation URL (e.g. Bielefeld substitution page).",
    )
    parser.add_argument(
        "--picker-order",
        type=int,
        default=None,
        help="Picker ordering value. Defaults to max(existing)+5.",
    )
    parser.add_argument(
        "--picker-group",
        choices=("Aperiodic", "Experimental"),
        default="Experimental",
        help=(
            "Picker group. Defaults to 'Experimental'; promote to 'Aperiodic' "
            "manually once the family is reviewed."
        ),
    )
    parser.add_argument(
        "--wiring-only",
        action="store_true",
        help=(
            "Skip the triangle-substitution generator body and test skeleton: write a "
            "framework-neutral generator stub (single triangle, loads end-to-end) plus all "
            "the catalog/registry wiring. Use this when the family needs a different "
            "substitution framework than ExactSimilaritySubstitution (e.g. the hat-style "
            "baked metatile or affine substitution paths)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned writes without modifying any files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        spec = build_spec(
            family_id=args.family_id,
            label=args.label,
            kinds=list(args.kinds),
            source_url=args.source_url,
            picker_order=args.picker_order,
            picker_group=args.picker_group,
        )
        plans = plan_writes(spec, ROOT, wiring_only=args.wiring_only)
    except ScaffoldError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    for plan in plans:
        action = "CREATE" if plan.is_new else "EDIT  "
        print(f"  {action} {plan.path.relative_to(ROOT)}")

    if args.dry_run:
        print("\nDry run: no files written. Re-run without --dry-run to apply.")
        return 0

    apply_writes(plans)
    format_generated_python(plans)
    print(f"\nScaffolded {spec.label!r} ({spec.family_id}).")
    print_followups(spec, wiring_only=args.wiring_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
