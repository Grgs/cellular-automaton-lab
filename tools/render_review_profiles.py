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


RENDER_REVIEW_PROFILES: dict[str, RenderReviewProfile] = {
    "pinwheel-depth-3": RenderReviewProfile(
        name="pinwheel-depth-3",
        family="pinwheel",
        patch_depth=3,
        literature_reference=LiteratureReference(
            citation_label="The pinwheel tilings of the plane",
            primary_source_url="https://annals.math.princeton.edu/1994/139-3/p05",
            secondary_source_urls=(
                "https://tilings.math.uni-bielefeld.de/substitution/pinwheel/",
            ),
            review_note=(
                "Compare the visible field for overall isotropy and boundary dominance; "
                "the review target is a representative interior pinwheel field rather than "
                "a boundary-dominated construction."
            ),
            cache_filename="pinwheel-reference.png",
        ),
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
            mode="image-derived-relaxed",
            expected_to_reduce_max_sampled_area=0.01,
            expected_to_reduce_max_sampled_count=4,
            review_note=(
                "The current Experimental shield model should now be overlap-free at the representative review epsilon. "
                "Only a tiny residual trace-noise budget is acceptable; anything larger is blocking."
            ),
        ),
    ),
    "dodecagonal-square-triangle-depth-3": RenderReviewProfile(
        name="dodecagonal-square-triangle-depth-3",
        family="dodecagonal-square-triangle",
        patch_depth=3,
        literature_reference=LiteratureReference(
            citation_label="Square-triangle",
            primary_source_url="https://tilings.math.uni-bielefeld.de/substitution/square-triangle/",
            review_note=(
                "Compare the dense central square-triangle mix for dodecagonal structure and "
                "the overall balance of square and triangle regions."
            ),
            cache_filename="dodecagonal-square-triangle-reference.png",
        ),
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


def resolve_overlap_policy(
    *,
    family: str,
    profile: RenderReviewProfile | None,
) -> OverlapPolicy:
    if profile is not None and profile.overlap_policy is not None:
        return profile.overlap_policy
    return OverlapPolicy(mode="strict")
