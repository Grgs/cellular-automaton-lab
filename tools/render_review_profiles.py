from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderReviewProfile:
    name: str
    family: str
    patch_depth: int | None = None
    cell_size: int | None = None
    viewport_width: int = 1200
    viewport_height: int = 900
    theme: str = "light"


RENDER_REVIEW_PROFILES: dict[str, RenderReviewProfile] = {
    "pinwheel-depth-3": RenderReviewProfile(
        name="pinwheel-depth-3",
        family="pinwheel",
        patch_depth=3,
    ),
    "shield-depth-3": RenderReviewProfile(
        name="shield-depth-3",
        family="shield",
        patch_depth=3,
    ),
    "dodecagonal-square-triangle-depth-3": RenderReviewProfile(
        name="dodecagonal-square-triangle-depth-3",
        family="dodecagonal-square-triangle",
        patch_depth=3,
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


def resolve_render_review_profile(profile_name: str) -> RenderReviewProfile:
    try:
        return RENDER_REVIEW_PROFILES[profile_name]
    except KeyError as exc:
        available = ", ".join(sorted(RENDER_REVIEW_PROFILES))
        raise ValueError(
            f"Unknown render review profile {profile_name!r}. Available profiles: {available}"
        ) from exc
