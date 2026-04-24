from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AperiodicBuilderKind = Literal["compatibility_patch", "substitution_recipe"]
AperiodicImplementationStatus = Literal[
    "true_substitution",
    "exact_affine",
    "canonical_patch",
    "known_deviation",
]
AperiodicPickerGroup = Literal["Aperiodic", "Experimental"]


PENROSE_GEOMETRY = "penrose-p3-rhombs"
PENROSE_VERTEX_GEOMETRY = "penrose-p3-rhombs-vertex"
PENROSE_P2_GEOMETRY = "penrose-p2-kite-dart"
AMMANN_BEENKER_GEOMETRY = "ammann-beenker"
SPECTRE_GEOMETRY = "spectre"
TAYLOR_SOCOLAR_GEOMETRY = "taylor-socolar"
SPHINX_GEOMETRY = "sphinx"
HAT_MONOTILE_GEOMETRY = "hat-monotile"
CHAIR_GEOMETRY = "chair"
ROBINSON_TRIANGLES_GEOMETRY = "robinson-triangles"
TUEBINGEN_TRIANGLE_GEOMETRY = "tuebingen-triangle"
DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY = "dodecagonal-square-triangle"
SHIELD_GEOMETRY = "shield"
PINWHEEL_GEOMETRY = "pinwheel"

THICK_RHOMB_KIND = "thick-rhomb"
THIN_RHOMB_KIND = "thin-rhomb"
KITE_KIND = "kite"
DART_KIND = "dart"
AMMANN_RHOMB_KIND = "rhomb"
AMMANN_SQUARE_KIND = "square"
SPECTRE_KIND = "spectre"
TAYLOR_HALF_HEX_KIND = "taylor-half-hex"
SPHINX_KIND = "sphinx"
HAT_KIND = "hat"
CHAIR_KIND = "chair"
ROBINSON_THICK_KIND = "robinson-thick"
ROBINSON_THIN_KIND = "robinson-thin"
TUEBINGEN_THICK_KIND = "tuebingen-thick"
TUEBINGEN_THIN_KIND = "tuebingen-thin"
DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND = "dodecagonal-square-triangle-square"
DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND = "dodecagonal-square-triangle-triangle"
SHIELD_SHIELD_KIND = "shield-shield"
SHIELD_SQUARE_KIND = "shield-square"
SHIELD_TRIANGLE_KIND = "shield-triangle"
PINWHEEL_TRIANGLE_KIND = "pinwheel-triangle"

ROBINSON_TILE_FAMILY = "robinson"
TUEBINGEN_TILE_FAMILY = "tuebingen"
HAT_TILE_FAMILY = "hat"
DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY = DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY
SHIELD_TILE_FAMILY = "shield"
PINWHEEL_TILE_FAMILY = "pinwheel"


@dataclass(frozen=True)
class AperiodicFamilyManifestEntry:
    geometry: str
    catalog_label: str
    reference_label: str
    picker_group: AperiodicPickerGroup
    picker_order: int
    default_rule: str
    builder_kind: AperiodicBuilderKind
    implementation_status: AperiodicImplementationStatus
    public_cell_kinds: tuple[str, ...]
    promotion_blocker: str | None = None

    @property
    def experimental(self) -> bool:
        return self.picker_group == "Experimental"


APERIODIC_FAMILY_MANIFEST: dict[str, AperiodicFamilyManifestEntry] = {
    PENROSE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PENROSE_GEOMETRY,
        catalog_label="Penrose P3 Rhombs",
        reference_label="Penrose Rhombs",
        picker_group="Aperiodic",
        picker_order=220,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        implementation_status="true_substitution",
        public_cell_kinds=(THICK_RHOMB_KIND, THIN_RHOMB_KIND),
    ),
    PENROSE_P2_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PENROSE_P2_GEOMETRY,
        catalog_label="Penrose P2 Kite-Dart",
        reference_label="Penrose Kite-Dart",
        picker_group="Aperiodic",
        picker_order=210,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        implementation_status="true_substitution",
        public_cell_kinds=(KITE_KIND, DART_KIND),
    ),
    AMMANN_BEENKER_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=AMMANN_BEENKER_GEOMETRY,
        catalog_label="Ammann-Beenker",
        reference_label="Ammann-Beenker",
        picker_group="Aperiodic",
        picker_order=230,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        implementation_status="true_substitution",
        public_cell_kinds=(AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
    ),
    SPECTRE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=SPECTRE_GEOMETRY,
        catalog_label="Spectre",
        reference_label="Spectre",
        picker_group="Aperiodic",
        picker_order=240,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(SPECTRE_KIND,),
    ),
    HAT_MONOTILE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=HAT_MONOTILE_GEOMETRY,
        catalog_label="Hat",
        reference_label="Hat",
        picker_group="Aperiodic",
        picker_order=250,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(HAT_KIND,),
    ),
    TAYLOR_SOCOLAR_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=TAYLOR_SOCOLAR_GEOMETRY,
        catalog_label="Taylor-Socolar",
        reference_label="Taylor-Socolar",
        picker_group="Aperiodic",
        picker_order=270,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(TAYLOR_HALF_HEX_KIND,),
    ),
    SPHINX_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=SPHINX_GEOMETRY,
        catalog_label="Sphinx",
        reference_label="Sphinx",
        picker_group="Aperiodic",
        picker_order=280,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(SPHINX_KIND,),
    ),
    CHAIR_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=CHAIR_GEOMETRY,
        catalog_label="Chair",
        reference_label="Chair",
        picker_group="Aperiodic",
        picker_order=290,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(CHAIR_KIND,),
    ),
    ROBINSON_TRIANGLES_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=ROBINSON_TRIANGLES_GEOMETRY,
        catalog_label="Robinson Triangles",
        reference_label="Robinson Triangles",
        picker_group="Aperiodic",
        picker_order=300,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
    ),
    TUEBINGEN_TRIANGLE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=TUEBINGEN_TRIANGLE_GEOMETRY,
        catalog_label="Tuebingen Triangle",
        reference_label="Tuebingen Triangle",
        picker_group="Aperiodic",
        picker_order=310,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
    ),
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        catalog_label="Dodecagonal Square-Triangle",
        reference_label="Dodecagonal Square-Triangle",
        picker_group="Experimental",
        picker_order=320,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(
            DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
            DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
        ),
        promotion_blocker=(
            "Experimental until manual visual review accepts the Bielefeld rule-image substitution implementation."
        ),
    ),
    SHIELD_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=SHIELD_GEOMETRY,
        catalog_label="Shield",
        reference_label="Shield",
        picker_group="Aperiodic",
        picker_order=330,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(SHIELD_SHIELD_KIND, SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
    ),
    PINWHEEL_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PINWHEEL_GEOMETRY,
        catalog_label="Pinwheel",
        reference_label="Pinwheel",
        picker_group="Experimental",
        picker_order=340,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="exact_affine",
        public_cell_kinds=(PINWHEEL_TRIANGLE_KIND,),
        promotion_blocker=(
            "Experimental until manual visual review accepts the exact-affine implementation."
        ),
    ),
}

APERIODIC_FAMILY_IDS: tuple[str, ...] = tuple(
    geometry
    for geometry, _entry in sorted(
        APERIODIC_FAMILY_MANIFEST.items(),
        key=lambda item: item[1].picker_order,
    )
)
EXPERIMENTAL_APERIODIC_FAMILY_IDS: tuple[str, ...] = tuple(
    geometry
    for geometry in APERIODIC_FAMILY_IDS
    if APERIODIC_FAMILY_MANIFEST[geometry].experimental
)


def get_aperiodic_family_manifest_entry(geometry: str) -> AperiodicFamilyManifestEntry:
    try:
        return APERIODIC_FAMILY_MANIFEST[geometry]
    except KeyError as error:
        raise ValueError(f"Unsupported aperiodic family {geometry!r}.") from error


__all__ = [
    "AMMANN_BEENKER_GEOMETRY",
    "AMMANN_RHOMB_KIND",
    "AMMANN_SQUARE_KIND",
    "APERIODIC_FAMILY_IDS",
    "APERIODIC_FAMILY_MANIFEST",
    "CHAIR_GEOMETRY",
    "CHAIR_KIND",
    "DART_KIND",
    "DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY",
    "DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND",
    "DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY",
    "DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND",
    "EXPERIMENTAL_APERIODIC_FAMILY_IDS",
    "HAT_KIND",
    "HAT_MONOTILE_GEOMETRY",
    "HAT_TILE_FAMILY",
    "KITE_KIND",
    "PENROSE_GEOMETRY",
    "PENROSE_P2_GEOMETRY",
    "PENROSE_VERTEX_GEOMETRY",
    "PINWHEEL_GEOMETRY",
    "PINWHEEL_TILE_FAMILY",
    "PINWHEEL_TRIANGLE_KIND",
    "ROBINSON_THICK_KIND",
    "ROBINSON_THIN_KIND",
    "ROBINSON_TILE_FAMILY",
    "ROBINSON_TRIANGLES_GEOMETRY",
    "SHIELD_GEOMETRY",
    "SHIELD_SHIELD_KIND",
    "SHIELD_SQUARE_KIND",
    "SHIELD_TILE_FAMILY",
    "SHIELD_TRIANGLE_KIND",
    "SPECTRE_GEOMETRY",
    "SPECTRE_KIND",
    "SPHINX_GEOMETRY",
    "SPHINX_KIND",
    "TAYLOR_HALF_HEX_KIND",
    "TAYLOR_SOCOLAR_GEOMETRY",
    "THICK_RHOMB_KIND",
    "THIN_RHOMB_KIND",
    "TUEBINGEN_THICK_KIND",
    "TUEBINGEN_THIN_KIND",
    "TUEBINGEN_TILE_FAMILY",
    "TUEBINGEN_TRIANGLE_GEOMETRY",
    "AperiodicBuilderKind",
    "AperiodicFamilyManifestEntry",
    "AperiodicImplementationStatus",
    "AperiodicPickerGroup",
    "get_aperiodic_family_manifest_entry",
]
