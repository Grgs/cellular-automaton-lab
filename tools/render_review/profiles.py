from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LiteratureReference:
    citation_label: str
    primary_source_url: str
    secondary_source_urls: tuple[str, ...] = ()
    review_note: str | None = None
    cache_filename: str | None = None


@dataclass(frozen=True)
class OverlapPolicy:
    mode: str
    expected_to_reduce_max_sampled_area: float | None = None
    expected_to_reduce_max_sampled_count: int | None = None
    review_note: str | None = None


@dataclass(frozen=True)
class ReviewChecklistItem:
    id: str
    label: str
    guidance: str


@dataclass(frozen=True)
class ExpectedWarning:
    id: str
    message: str
    sources: tuple[str, ...]
    host_kinds: tuple[str, ...] = ()
    note: str | None = None


@dataclass(frozen=True)
class RenderReviewProfile:
    name: str
    family: str
    patch_depth: int | None = None
    cell_size: int | None = None
    viewport_width: int = 1200
    viewport_height: int = 900
    theme: str = "light"
    literature_reference: LiteratureReference | None = None
    overlap_policy: OverlapPolicy | None = None
    review_checklist: tuple[ReviewChecklistItem, ...] = ()
    expected_warnings: tuple[ExpectedWarning, ...] = ()


STANDALONE_BACKEND_UNAVAILABLE_WARNING = ExpectedWarning(
    id="standalone-backend-topology-unavailable",
    message="Backend topology facts unavailable for host mode standalone.",
    sources=("consistency",),
    host_kinds=("standalone",),
    note="Standalone render review cannot compare live backend topology facts.",
)


RENDER_REVIEW_PROFILES: dict[str, RenderReviewProfile] = {
    "pinwheel-depth-3": RenderReviewProfile(
        name="pinwheel-depth-3",
        family="pinwheel",
        patch_depth=3,
        literature_reference=LiteratureReference(
            citation_label="The pinwheel tilings of the plane",
            primary_source_url="https://annals.math.princeton.edu/1994/139-3/p05",
            secondary_source_urls=("https://tilings.math.uni-bielefeld.de/substitution/pinwheel/",),
            review_note=(
                "Compare the visible field for overall isotropy and boundary dominance; "
                "the review target is a representative interior pinwheel field rather than "
                "a boundary-dominated construction."
            ),
            cache_filename="pinwheel-reference.png",
        ),
        review_checklist=(
            ReviewChecklistItem(
                id="interior-field-isotropy",
                label="Interior field reads isotropic",
                guidance="Check that the visible patch reads as an interior pinwheel field rather than a directional or rectangular crop.",
            ),
            ReviewChecklistItem(
                id="boundary-dominance",
                label="Boundary does not dominate",
                guidance="Check that boundary triangles do not visually outweigh the interior texture of the sample.",
            ),
            ReviewChecklistItem(
                id="orientation-mix",
                label="Orientation mix feels balanced",
                guidance="Check that multiple pinwheel orientations are evident in the field instead of one dominant directional band.",
            ),
        ),
        expected_warnings=(STANDALONE_BACKEND_UNAVAILABLE_WARNING,),
    ),
    "shield-depth-3": RenderReviewProfile(
        name="shield-depth-3",
        family="shield",
        patch_depth=3,
        literature_reference=LiteratureReference(
            citation_label="Shield",
            primary_source_url="https://tilings.math.uni-bielefeld.de/substitution/shield/",
            review_note=(
                "Compare the dense 12-fold central field for symmetry, density, and overall "
                "orientation balance rather than line-style details."
            ),
            cache_filename="shield-reference.png",
        ),
        overlap_policy=OverlapPolicy(
            mode="strict",
            review_note=(
                "Shield should now be overlap-free at the representative review epsilon. "
                "Any positive-area representative overlap is blocking."
            ),
        ),
        review_checklist=(
            ReviewChecklistItem(
                id="central-field-symmetry",
                label="Central field reads 12-fold",
                guidance="Check that the dense center reads as a symmetric 12-fold shield field rather than a lopsided cluster.",
            ),
            ReviewChecklistItem(
                id="density-balance",
                label="Density stays visually even",
                guidance="Check that the field stays dense without obvious sparse gutters or boundary-driven voids.",
            ),
            ReviewChecklistItem(
                id="orientation-balance",
                label="Orientations stay balanced",
                guidance="Check that shield, square, and triangle orientations feel balanced in the central field instead of collapsing into a directional bias.",
            ),
        ),
        expected_warnings=(STANDALONE_BACKEND_UNAVAILABLE_WARNING,),
    ),
    "dodecagonal-square-triangle-depth-3": RenderReviewProfile(
        name="dodecagonal-square-triangle-depth-3",
        family="dodecagonal-square-triangle",
        patch_depth=3,
        literature_reference=LiteratureReference(
            citation_label="Square-triangle",
            primary_source_url="https://tilings.math.uni-bielefeld.de/substitution/square-triangle/",
            review_note=(
                "Compare the finite literature-cropped square-triangle mix for dodecagonal "
                "structure and the overall balance of square and triangle regions; strict "
                "topology validation is currently proven through depth 11."
            ),
            cache_filename="dodecagonal-square-triangle-reference.png",
        ),
        review_checklist=(
            ReviewChecklistItem(
                id="dodecagonal-structure",
                label="Dodecagonal structure is visible",
                guidance="Check that the central field reads as a 12-fold square-triangle construction rather than an arbitrary dense polygon patch.",
            ),
            ReviewChecklistItem(
                id="square-triangle-balance",
                label="Square and triangle regions stay balanced",
                guidance="Check that neither squares nor triangles visually swamp the other across the representative window.",
            ),
            ReviewChecklistItem(
                id="central-density",
                label="Central density stays coherent",
                guidance="Check that the central mix stays dense and coherent without obvious missing sectors or off-center weighting.",
            ),
        ),
        expected_warnings=(STANDALONE_BACKEND_UNAVAILABLE_WARNING,),
    ),
}


def iter_render_review_profiles() -> tuple[RenderReviewProfile, ...]:
    return tuple(RENDER_REVIEW_PROFILES[name] for name in RENDER_REVIEW_PROFILES)


def describe_render_review_profile(profile: RenderReviewProfile) -> str:
    size_summary = (
        f"depth={profile.patch_depth}"
        if profile.patch_depth is not None
        else f"cell_size={profile.cell_size}"
    )
    return (
        f"{profile.name}: family={profile.family}, {size_summary}, "
        f"viewport={profile.viewport_width}x{profile.viewport_height}, theme={profile.theme}"
    )


def resolve_profile_reference_cache_path(
    profile: RenderReviewProfile,
    *,
    cache_dir: Path,
) -> Path | None:
    literature_reference = profile.literature_reference
    if literature_reference is None or literature_reference.cache_filename is None:
        return None
    return cache_dir / literature_reference.cache_filename


def resolve_render_review_profile(profile_name: str) -> RenderReviewProfile:
    try:
        return RENDER_REVIEW_PROFILES[profile_name]
    except KeyError as exc:
        available = ", ".join(sorted(RENDER_REVIEW_PROFILES))
        raise ValueError(
            f"Unknown render review profile {profile_name!r}. Available profiles: {available}"
        ) from exc


def find_render_review_profile(
    *,
    family: str,
    patch_depth: int | None = None,
    cell_size: int | None = None,
) -> RenderReviewProfile | None:
    for profile in iter_render_review_profiles():
        if profile.family != family:
            continue
        if profile.patch_depth != patch_depth:
            continue
        if profile.cell_size != cell_size:
            continue
        return profile
    return None


def resolve_overlap_policy(
    *,
    family: str,
    profile: RenderReviewProfile | None,
) -> OverlapPolicy:
    if profile is not None and profile.overlap_policy is not None:
        return profile.overlap_policy
    return OverlapPolicy(mode="strict")
