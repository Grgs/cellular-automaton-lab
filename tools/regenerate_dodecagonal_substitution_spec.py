from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_IMAGE = (
    ROOT / "docs" / "contracts" / "dodecagonal-square-triangle-generator" / "bielefeld-rule.png"
)
DEFAULT_OUTPUT_PATH = (
    ROOT / "backend" / "simulation" / "data" / "dodecagonal_square_triangle_substitution_spec.json"
)

SQRT3 = math.sqrt(3.0)
INFLATION_FACTOR = 2.0 + SQRT3
TRANSFORM_PRECISION = 12
EDGE_MATCH_TOLERANCE = 0.16
MIN_COMPONENT_PIXELS = 300

TILE_FAMILY = "dodecagonal-square-triangle"
SQUARE_KIND = "dodecagonal-square-triangle-square"
TRIANGLE_KIND = "dodecagonal-square-triangle-triangle"

PROTOTYPES: dict[str, tuple[tuple[float, float], ...]] = {
    "square-white": ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)),
    "square-light": ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)),
    "triangle-red": ((-0.5, -SQRT3 / 6.0), (0.5, -SQRT3 / 6.0), (0.0, SQRT3 / 3.0)),
    "triangle-yellow": (
        (-0.5, -SQRT3 / 6.0),
        (0.5, -SQRT3 / 6.0),
        (0.0, SQRT3 / 3.0),
    ),
    "triangle-blue": (
        (-0.5, -SQRT3 / 6.0),
        (0.5, -SQRT3 / 6.0),
        (0.0, SQRT3 / 3.0),
    ),
}

FILL_COLORS: dict[str, tuple[int, int, int, int]] = {
    "triangle-red": (138, 36, 34, 255),
    "triangle-yellow": (255, 204, 102, 255),
    "triangle-blue": (107, 115, 163, 255),
    "square-light": (189, 201, 227, 255),
    "square-white": (255, 255, 255, 255),
}

# Rule-image regions are intentionally explicit: the Bielefeld source is a
# raster export of five separated substitution diagrams, not structured data.
RULE_REGIONS: dict[str, tuple[int, int, int, int]] = {
    "triangle-red": (180, 0, 340, 145),
    "triangle-yellow": (180, 230, 340, 385),
    "triangle-blue": (180, 465, 340, 612),
    "square-light": (650, 80, 864, 285),
    "square-white": (650, 315, 864, 520),
}


class DodecagonalSubstitutionSpecError(ValueError):
    pass


@dataclass(frozen=True)
class _ImageComponent:
    label: str
    points: tuple[tuple[float, float], ...]
    center: tuple[float, float]
    transform: tuple[float, float, float, float, float, float]


def _rotate_point(point: tuple[float, float], degrees: int) -> tuple[float, float]:
    radians = math.radians(degrees)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    x_value, y_value = point
    return (
        (cosine * x_value) - (sine * y_value),
        (sine * x_value) + (cosine * y_value),
    )


def _affine_apply(
    transform: tuple[float, float, float, float, float, float],
    point: tuple[float, float],
) -> tuple[float, float]:
    return (
        (transform[0] * point[0]) + (transform[1] * point[1]) + transform[2],
        (transform[3] * point[0]) + (transform[4] * point[1]) + transform[5],
    )


def _affine_inverse(
    transform: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    a_value, b_value, tx_value, c_value, d_value, ty_value = transform
    determinant = (a_value * d_value) - (b_value * c_value)
    if math.isclose(determinant, 0.0):
        raise DodecagonalSubstitutionSpecError("Cannot invert singular affine transform.")
    return (
        d_value / determinant,
        -b_value / determinant,
        ((b_value * ty_value) - (d_value * tx_value)) / determinant,
        -c_value / determinant,
        a_value / determinant,
        ((c_value * tx_value) - (a_value * ty_value)) / determinant,
    )


def _affine_multiply(
    left: tuple[float, float, float, float, float, float],
    right: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    return (
        (left[0] * right[0]) + (left[1] * right[3]),
        (left[0] * right[1]) + (left[1] * right[4]),
        (left[0] * right[2]) + (left[1] * right[5]) + left[2],
        (left[3] * right[0]) + (left[4] * right[3]),
        (left[3] * right[1]) + (left[4] * right[4]),
        (left[3] * right[2]) + (left[4] * right[5]) + left[5],
    )


def _convex_hull(points: tuple[tuple[float, float], ...]) -> tuple[tuple[float, float], ...]:
    sorted_points = tuple(sorted(set(points)))
    if len(sorted_points) <= 1:
        return sorted_points

    def cross(
        origin: tuple[float, float],
        left: tuple[float, float],
        right: tuple[float, float],
    ) -> float:
        return ((left[0] - origin[0]) * (right[1] - origin[1])) - (
            (left[1] - origin[1]) * (right[0] - origin[0])
        )

    lower: list[tuple[float, float]] = []
    for point in sorted_points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper: list[tuple[float, float]] = []
    for point in reversed(sorted_points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return tuple(lower[:-1] + upper[:-1])


def _fit_similarity_to_support(
    label: str,
    points: tuple[tuple[float, float], ...],
    *,
    prototype: tuple[tuple[float, float], ...] | None = None,
) -> tuple[float, float, float, float, float, float]:
    resolved_prototype = prototype if prototype is not None else PROTOTYPES[label]
    hull = _convex_hull(points)
    best: tuple[float, int, float, tuple[float, float]] | None = None

    for angle in range(0, 360, 30):
        rotated = tuple(_rotate_point(point, angle) for point in resolved_prototype)
        support_points: list[tuple[float, float]] = []
        for x_value, y_value in rotated:
            length = math.hypot(x_value, y_value)
            direction = (x_value / length, y_value / length)
            support_points.append(
                max(hull, key=lambda point: (point[0] * direction[0]) + (point[1] * direction[1]))
            )

        support_center = (
            sum(x for x, _ in support_points) / len(support_points),
            sum(y for _, y in support_points) / len(support_points),
        )
        prototype_center = (
            sum(x for x, _ in rotated) / len(rotated),
            sum(y for _, y in rotated) / len(rotated),
        )

        numerator = 0.0
        denominator = 0.0
        for prototype_point, support_point in zip(rotated, support_points):
            prototype_delta = (
                prototype_point[0] - prototype_center[0],
                prototype_point[1] - prototype_center[1],
            )
            support_delta = (
                support_point[0] - support_center[0],
                support_point[1] - support_center[1],
            )
            numerator += (prototype_delta[0] * support_delta[0]) + (
                prototype_delta[1] * support_delta[1]
            )
            denominator += (prototype_delta[0] * prototype_delta[0]) + (
                prototype_delta[1] * prototype_delta[1]
            )

        scale = numerator / denominator
        if scale <= 0.0:
            continue
        translation = (
            support_center[0] - (scale * prototype_center[0]),
            support_center[1] - (scale * prototype_center[1]),
        )
        error = math.sqrt(
            sum(
                (
                    ((scale * prototype_point[0]) + translation[0] - support_point[0]) ** 2
                    + ((scale * prototype_point[1]) + translation[1] - support_point[1]) ** 2
                )
                for prototype_point, support_point in zip(rotated, support_points)
            )
            / len(support_points)
        )
        if best is None or error < best[0]:
            best = (error, angle, scale, translation)

    if best is None:
        raise DodecagonalSubstitutionSpecError(f"Could not fit component {label!r}.")

    _error, angle, scale, translation = best
    radians = math.radians(angle)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (
        scale * cosine,
        -scale * sine,
        translation[0],
        scale * sine,
        scale * cosine,
        translation[1],
    )


def _extract_components(source_image: Path) -> tuple[_ImageComponent, ...]:
    image = Image.open(source_image).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    components: list[_ImageComponent] = []

    for label, color in FILL_COLORS.items():
        seen: set[tuple[int, int]] = set()
        for y_value in range(height):
            for x_value in range(width):
                if (x_value, y_value) in seen or pixels[x_value, y_value] != color:
                    continue
                queue: deque[tuple[int, int]] = deque(((x_value, y_value),))
                seen.add((x_value, y_value))
                points: list[tuple[float, float]] = []
                while queue:
                    current_x, current_y = queue.popleft()
                    points.append((float(current_x), float(-current_y)))
                    for delta_x, delta_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        next_x = current_x + delta_x
                        next_y = current_y + delta_y
                        if (
                            not (0 <= next_x < width and 0 <= next_y < height)
                            or (next_x, next_y) in seen
                            or pixels[next_x, next_y] != color
                        ):
                            continue
                        seen.add((next_x, next_y))
                        queue.append((next_x, next_y))

                if len(points) <= MIN_COMPONENT_PIXELS:
                    continue
                point_tuple = tuple(points)
                center = (
                    sum(x for x, _ in point_tuple) / len(point_tuple),
                    sum(y for _, y in point_tuple) / len(point_tuple),
                )
                components.append(
                    _ImageComponent(
                        label=label,
                        points=point_tuple,
                        center=center,
                        transform=_fit_similarity_to_support(label, point_tuple),
                    )
                )

    if len(components) != 106:
        raise DodecagonalSubstitutionSpecError(
            f"Expected 106 rule-image components, found {len(components)}."
        )
    return tuple(components)


def _components_in_region(
    components: tuple[_ImageComponent, ...],
    region: tuple[int, int, int, int],
) -> tuple[_ImageComponent, ...]:
    left, top, right, bottom = region
    return tuple(
        component
        for component in components
        if left <= component.center[0] <= right and top <= -component.center[1] <= bottom
    )


def _edge_match(
    left_vertices: tuple[tuple[float, float], ...],
    right_vertices: tuple[tuple[float, float], ...],
) -> tuple[float, int, int, bool]:
    best: tuple[float, int, int, bool] | None = None
    for left_index, left_start in enumerate(left_vertices):
        left_end = left_vertices[(left_index + 1) % len(left_vertices)]
        for right_index, right_start in enumerate(right_vertices):
            right_end = right_vertices[(right_index + 1) % len(right_vertices)]
            reversed_error = math.dist(left_start, right_end) + math.dist(left_end, right_start)
            same_error = math.dist(left_start, right_start) + math.dist(left_end, right_end)
            if best is None or reversed_error < best[0]:
                best = (reversed_error, left_index, right_index, True)
            if best is None or same_error < best[0]:
                best = (same_error, left_index, right_index, False)
    if best is None:
        raise DodecagonalSubstitutionSpecError("Could not compare child edges.")
    return best


def _snap_child_linear(
    local_transform: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float]:
    angle = math.degrees(math.atan2(local_transform[3], local_transform[0])) % 360.0
    snapped_angle = int(round(angle / 30.0) * 30) % 360
    radians = math.radians(snapped_angle)
    return (
        math.cos(radians) / INFLATION_FACTOR,
        -math.sin(radians) / INFLATION_FACTOR,
        math.sin(radians) / INFLATION_FACTOR,
        math.cos(radians) / INFLATION_FACTOR,
    )


def _vertices_for_child(
    child: dict[str, object],
    translation: tuple[float, float] | None = None,
) -> tuple[tuple[float, float], ...]:
    linear = cast(tuple[float, float, float, float], child["linear"])
    tx_value, ty_value = (
        translation
        if translation is not None
        else cast(tuple[float, float], child["approx_translation"])
    )
    return tuple(
        (
            (linear[0] * x_value) + (linear[1] * y_value) + tx_value,
            (linear[2] * x_value) + (linear[3] * y_value) + ty_value,
        )
        for x_value, y_value in PROTOTYPES[str(child["label"])]
    )


def _exactify_rule(
    parent_label: str,
    children: tuple[_ImageComponent, ...],
) -> list[dict[str, object]]:
    parent_prototype = tuple(
        (x_value * INFLATION_FACTOR, y_value * INFLATION_FACTOR)
        for x_value, y_value in PROTOTYPES[parent_label]
    )
    parent_transform = _fit_similarity_to_support(
        parent_label,
        tuple(point for child in children for point in child.points),
        prototype=parent_prototype,
    )
    parent_super_transform = (
        parent_transform[0] * INFLATION_FACTOR,
        parent_transform[1] * INFLATION_FACTOR,
        parent_transform[2],
        parent_transform[3] * INFLATION_FACTOR,
        parent_transform[4] * INFLATION_FACTOR,
        parent_transform[5],
    )
    inverse_parent = _affine_inverse(parent_super_transform)

    rule_children: list[dict[str, object]] = []
    for child in children:
        local_transform = _affine_multiply(inverse_parent, child.transform)
        rule_children.append(
            {
                "label": child.label,
                "linear": _snap_child_linear(local_transform),
                "approx_translation": (local_transform[2], local_transform[5]),
            }
        )

    approximate_vertices = tuple(_vertices_for_child(child) for child in rule_children)
    edge_pairs: dict[tuple[int, int], tuple[int, int, bool]] = {}
    for left_index, left_vertices in enumerate(approximate_vertices):
        for right_index in range(left_index + 1, len(approximate_vertices)):
            error, left_edge, right_edge, reversed_direction = _edge_match(
                left_vertices,
                approximate_vertices[right_index],
            )
            if error < EDGE_MATCH_TOLERANCE:
                edge_pairs[(left_index, right_index)] = (
                    left_edge,
                    right_edge,
                    reversed_direction,
                )

    adjacency: defaultdict[int, list[int]] = defaultdict(list)
    for left_index, right_index in edge_pairs:
        adjacency[left_index].append(right_index)
        adjacency[right_index].append(left_index)

    translations: dict[int, tuple[float, float]] = {}
    for root_index in range(len(rule_children)):
        if root_index in translations:
            continue
        translations[root_index] = cast(
            tuple[float, float], rule_children[root_index]["approx_translation"]
        )
        queue: deque[int] = deque((root_index,))
        while queue:
            current_index = queue.popleft()
            current_child = rule_children[current_index]
            current_linear = cast(tuple[float, float, float, float], current_child["linear"])
            current_translation = translations[current_index]
            for next_index in adjacency[current_index]:
                if next_index in translations:
                    continue
                pair_key = (
                    (current_index, next_index)
                    if current_index < next_index
                    else (next_index, current_index)
                )
                current_edge, next_edge, reversed_direction = edge_pairs[pair_key]
                if current_index > next_index:
                    current_edge, next_edge = next_edge, current_edge

                next_child = rule_children[next_index]
                next_linear = cast(tuple[float, float, float, float], next_child["linear"])
                current_point = PROTOTYPES[str(current_child["label"])][current_edge]
                next_edge_vertex = (
                    (next_edge + 1) % len(PROTOTYPES[str(next_child["label"])])
                    if reversed_direction
                    else next_edge
                )
                next_point = PROTOTYPES[str(next_child["label"])][next_edge_vertex]
                current_world = (
                    (current_linear[0] * current_point[0])
                    + (current_linear[1] * current_point[1])
                    + current_translation[0],
                    (current_linear[2] * current_point[0])
                    + (current_linear[3] * current_point[1])
                    + current_translation[1],
                )
                next_without_translation = (
                    (next_linear[0] * next_point[0]) + (next_linear[1] * next_point[1]),
                    (next_linear[2] * next_point[0]) + (next_linear[3] * next_point[1]),
                )
                translations[next_index] = (
                    current_world[0] - next_without_translation[0],
                    current_world[1] - next_without_translation[1],
                )
                queue.append(next_index)

    boundary_vertices: list[tuple[float, float]] = []
    internal_edges: set[tuple[int, int]] = set()
    for (left_index, right_index), (left_edge, right_edge, _reversed) in edge_pairs.items():
        internal_edges.add((left_index, left_edge))
        internal_edges.add((right_index, right_edge))

    for child_index, child in enumerate(rule_children):
        vertices = _vertices_for_child(child, translations[child_index])
        for edge_index, left in enumerate(vertices):
            if (child_index, edge_index) in internal_edges:
                continue
            boundary_vertices.append(left)
            boundary_vertices.append(vertices[(edge_index + 1) % len(vertices)])

    deltas: list[tuple[float, float]] = []
    for parent_vertex in PROTOTYPES[parent_label]:
        length = math.hypot(parent_vertex[0], parent_vertex[1])
        direction = (parent_vertex[0] / length, parent_vertex[1] / length)
        boundary_vertex = max(
            boundary_vertices,
            key=lambda point: (point[0] * direction[0]) + (point[1] * direction[1]),
        )
        deltas.append(
            (
                parent_vertex[0] - boundary_vertex[0],
                parent_vertex[1] - boundary_vertex[1],
            )
        )
    boundary_delta = (
        sum(x for x, _ in deltas) / len(deltas),
        sum(y for _, y in deltas) / len(deltas),
    )

    return [
        {
            "label": str(child["label"]),
            "transform": [
                round(value, TRANSFORM_PRECISION)
                for value in (
                    cast(tuple[float, float, float, float], child["linear"])[0],
                    cast(tuple[float, float, float, float], child["linear"])[1],
                    translations[index][0] + boundary_delta[0],
                    cast(tuple[float, float, float, float], child["linear"])[2],
                    cast(tuple[float, float, float, float], child["linear"])[3],
                    translations[index][1] + boundary_delta[1],
                )
            ],
        }
        for index, child in enumerate(rule_children)
    ]


def regenerate_substitution_spec_payload(
    source_image: Path = DEFAULT_SOURCE_IMAGE,
) -> dict[str, object]:
    if not source_image.exists():
        raise DodecagonalSubstitutionSpecError(f"Missing Bielefeld rule image: {source_image}")

    components = _extract_components(source_image)
    rules: dict[str, list[dict[str, object]]] = {}
    for parent_label, region in RULE_REGIONS.items():
        children = _components_in_region(components, region)
        if not children:
            raise DodecagonalSubstitutionSpecError(
                f"Rule image region for {parent_label!r} did not contain children."
            )
        rules[parent_label] = _exactify_rule(parent_label, children)

    return {
        "source": {
            "name": "Bielefeld square-triangle substitution rule image",
            "url": "https://tilings.math.uni-bielefeld.de/img/substitution/square-triangle/rule.png",
            "path": str(source_image.relative_to(ROOT)),
        },
        "tile_family": TILE_FAMILY,
        "inflation_factor": {
            "expression": "2 + sqrt(3)",
            "value": round(INFLATION_FACTOR, TRANSFORM_PRECISION),
        },
        "root_label": "square-white",
        "prototypes": {
            label: [
                [round(x, TRANSFORM_PRECISION), round(y, TRANSFORM_PRECISION)] for x, y in vertices
            ]
            for label, vertices in PROTOTYPES.items()
        },
        "public_mapping": {
            "square-white": {"kind": SQUARE_KIND, "chirality": None},
            "square-light": {"kind": SQUARE_KIND, "chirality": None},
            "triangle-red": {"kind": TRIANGLE_KIND, "chirality": "red"},
            "triangle-yellow": {"kind": TRIANGLE_KIND, "chirality": "yellow"},
            "triangle-blue": {"kind": TRIANGLE_KIND, "chirality": "blue"},
        },
        "rules": rules,
        "notes": (
            "This spec is recovered from the public Bielefeld rule image and freezes the "
            "geometric five-state substitution used by the runtime. The colored states are "
            "preserved; the public API still collapses them to square/triangle kinds."
        ),
    }


def _format_payload(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def payload_has_drift(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    source_image: Path = DEFAULT_SOURCE_IMAGE,
) -> bool:
    if not output_path.exists():
        return True
    current = json.loads(output_path.read_text(encoding="utf-8"))
    regenerated = regenerate_substitution_spec_payload(source_image)
    return current != regenerated


def write_substitution_spec(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    source_image: Path = DEFAULT_SOURCE_IMAGE,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _format_payload(regenerate_substitution_spec_payload(source_image)),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate the backend-owned dodecagonal square-triangle substitution "
            "spec JSON from the checked-in Bielefeld rule image."
        )
    )
    parser.add_argument(
        "--source-image",
        type=Path,
        default=DEFAULT_SOURCE_IMAGE,
        help="Path to the checked-in Bielefeld rule PNG source.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Destination JSON path. Defaults to the checked-in backend spec file.",
    )
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source_image = Path(args.source_image)
    output_path = Path(args.output)
    try:
        if bool(args.check):
            if payload_has_drift(output_path, source_image=source_image):
                print("Dodecagonal substitution spec drift detected:")
                print(f"  source: {source_image}")
                print(f"  output: {output_path}")
                return 1
            print("Dodecagonal substitution spec is up to date.")
            return 0

        write_substitution_spec(output_path, source_image=source_image)
        print("Regenerated dodecagonal substitution spec:")
        print(f"  source: {source_image}")
        print(f"  output: {output_path}")
        return 0
    except DodecagonalSubstitutionSpecError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
