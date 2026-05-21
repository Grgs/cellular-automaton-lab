"""2D affine-transform math + orientation/chirality token derivation.

Each ``Affine`` is the row-major 6-tuple ``(a, b, c, d, e, f)`` representing
the 2x3 matrix ``[[a b c] [d e f]]`` applied to homogeneous ``(x, y, 1)``
vectors. Pure functions; no module-level state.
"""

from __future__ import annotations

import math

from .geometry import encode_float
from .types import Affine, Vec


def affine_multiply(left: Affine, right: Affine) -> Affine:
    return (
        (left[0] * right[0]) + (left[1] * right[3]),
        (left[0] * right[1]) + (left[1] * right[4]),
        (left[0] * right[2]) + (left[1] * right[5]) + left[2],
        (left[3] * right[0]) + (left[4] * right[3]),
        (left[3] * right[1]) + (left[4] * right[4]),
        (left[3] * right[2]) + (left[4] * right[5]) + left[5],
    )


def affine_apply(transform: Affine, point: Vec) -> Vec:
    return Vec(
        (transform[0] * point.x) + (transform[1] * point.y) + transform[2],
        (transform[3] * point.x) + (transform[4] * point.y) + transform[5],
    )


def affine_linear_determinant(transform: Affine) -> float:
    return (transform[0] * transform[4]) - (transform[1] * transform[3])


def affine_chirality_token(transform: Affine) -> str:
    """Derive a ``left`` / ``right`` chirality token from the linear determinant.

    A determinant of zero shouldn't happen for tile placements (it would mean a
    degenerate transform), so we treat it as the canonical chirality.
    """
    return "right" if affine_linear_determinant(transform) < 0 else "left"


def affine_orientation_token(
    transform: Affine,
    *,
    angle_step_degrees: float = 30.0,
) -> str:
    """Derive a discrete orientation token (degrees mod 360) from the rotation angle.

    The angle is recovered from the affine's first basis vector, then snapped to
    the nearest multiple of ``angle_step_degrees`` so cells with the same visual
    rotation collapse to a single token even with floating-point drift.
    Reflections are normalised by negating the cosine sign before the angle is
    extracted, so the token reflects ``rotation`` independently of
    ``chirality``.
    """
    determinant = affine_linear_determinant(transform)
    cosine = transform[0]
    sine = transform[3]
    if determinant < 0:
        # Undo the reflection so a reflected-then-rotated transform reports the
        # same orientation as the unreflected version. This keeps the chirality
        # axis and orientation axis independent for downstream consumers.
        sine = -sine
    angle_radians = math.atan2(sine, cosine)
    angle_degrees = math.degrees(angle_radians) % 360.0
    if angle_step_degrees <= 0:
        rounded = round(angle_degrees, 3)
    else:
        rounded = round(angle_degrees / angle_step_degrees) * angle_step_degrees
        rounded %= 360.0
    return str(int(rounded)) if float(rounded).is_integer() else str(rounded)


def affine_inverse(transform: Affine) -> Affine:
    determinant = (transform[0] * transform[4]) - (transform[1] * transform[3])
    if math.isclose(determinant, 0.0):
        raise ValueError("Cannot invert singular affine transform.")
    inverse_determinant = 1.0 / determinant
    a = transform[4] * inverse_determinant
    b = -transform[1] * inverse_determinant
    d = -transform[3] * inverse_determinant
    e = transform[0] * inverse_determinant
    c = -((a * transform[2]) + (b * transform[5]))
    f = -((d * transform[2]) + (e * transform[5]))
    return (a, b, c, d, e, f)


def translation(tx: float, ty: float) -> Affine:
    return (1.0, 0.0, float(tx), 0.0, 1.0, float(ty))


def translation_to(source: Vec, target: Vec) -> Affine:
    return translation(target.x - source.x, target.y - source.y)


def rotation(radians: float) -> Affine:
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (cosine, -sine, 0.0, sine, cosine, 0.0)


def scale(factor: float) -> Affine:
    return (float(factor), 0.0, 0.0, 0.0, float(factor), 0.0)


def id_from_anchor(prefix: str, anchor: Vec, orientation: int) -> str:
    return f"{prefix}:{orientation % 360}:{encode_float(anchor.x)}:{encode_float(anchor.y)}"


def id_from_transform(prefix: str, transform: Affine) -> str:
    return prefix + ":" + ":".join(encode_float(value) for value in transform)
