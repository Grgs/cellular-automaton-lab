"""Render rule evolution frames for visual troubleshooting.

Backs ``python -m tools rules review``. The tool intentionally uses the
backend simulation engine and a lightweight Pillow renderer so rule authors can
inspect repeatable generation snapshots without clicking through the app.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.engine import SimulationEngine
from backend.simulation.rule_context_frames import topology_frame_for
from backend.simulation.seeding.shapes import NAMED_PATTERNS, PATTERN_NAMES, place_pattern
from backend.simulation.seeding.traversal import (
    DEFAULT_TRAVERSAL,
    TRAVERSALS,
    paint_bits,
)
from backend.simulation.topology_boards import board_from_cells_by_id, empty_board
from backend.simulation.topology_types import LatticeCell, SimulationBoard, parse_regular_cell_id

DEFAULT_SEED = "01100 11000 01000"
DEFAULT_GENERATIONS = (0, 5, 15, 30)
DEFAULT_OUTPUT_DIR = Path("output/rule-review")
DEFAULT_WIDTH = 95
DEFAULT_HEIGHT = 45
DEFAULT_PATCH_DEPTH = 4
DEFAULT_CELL_SIZE = 8
FRAME_PADDING = 14
LABEL_HEIGHT = 28
BACKGROUND = "#f8f1e5"
MONTAGE_GAP = 16
MONTAGE_BG = "#e4e8ec"

WHIRLPOOL_PRESETS = frozenset(("anchored-source-vortex", "dual-source-vortex"))


@dataclass(frozen=True)
class CartesianSeedCell:
    x: int
    y: int
    state: int


@dataclass(frozen=True)
class FrameReview:
    generation: int
    image_path: Path
    state_counts: dict[int, int]
    live_cells: int
    changed_cells: int | None
    bounding_box: dict[str, int] | None

    def to_dict(self, *, root: Path) -> dict[str, object]:
        return {
            "generation": self.generation,
            "image": str(self.image_path.relative_to(root)),
            "state_counts": {str(key): value for key, value in sorted(self.state_counts.items())},
            "live_cells": self.live_cells,
            "changed_cells": self.changed_cells,
            "bounding_box": self.bounding_box,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools rules review",
        description="Render selected generations for one rule/topology/seed as PNG frames.",
    )
    parser.add_argument(
        "--rule",
        default="conway",
        help="Rule name to run (default: conway).",
    )
    parser.add_argument(
        "--geometry",
        default="square",
        help="Topology geometry key (default: square).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Grid width for regular tilings (default: {DEFAULT_WIDTH}).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Grid height for regular tilings (default: {DEFAULT_HEIGHT}).",
    )
    parser.add_argument(
        "--patch-depth",
        type=int,
        default=DEFAULT_PATCH_DEPTH,
        help=f"Patch depth for aperiodic tilings (default: {DEFAULT_PATCH_DEPTH}).",
    )
    seed_group = parser.add_mutually_exclusive_group()
    seed_group.add_argument(
        "--seed",
        default=None,
        help=f"Binary seed bits mapped through --traversal. Default when no seed source is given: {DEFAULT_SEED!r}.",
    )
    seed_group.add_argument(
        "--pattern",
        choices=PATTERN_NAMES,
        default=None,
        help="Named geometric seed pattern.",
    )
    seed_group.add_argument(
        "--preset",
        choices=sorted(WHIRLPOOL_PRESETS),
        default=None,
        help="Curated rule preset. Currently supports square Whirlpool presets.",
    )
    seed_group.add_argument(
        "--cells-json",
        type=Path,
        default=None,
        help="JSON object mapping cell ids to states, or a list of {id,state} objects.",
    )
    parser.add_argument(
        "--traversal",
        choices=sorted(TRAVERSALS),
        default=DEFAULT_TRAVERSAL,
        help=f"Seed bit traversal (default: {DEFAULT_TRAVERSAL}).",
    )
    parser.add_argument(
        "--generations",
        default=",".join(str(value) for value in DEFAULT_GENERATIONS),
        help="Comma-separated generations to render (default: 0,5,15,30).",
    )
    parser.add_argument(
        "--cell-size",
        type=int,
        default=DEFAULT_CELL_SIZE,
        help=f"Approximate rendered pixels per cell (default: {DEFAULT_CELL_SIZE}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for PNG/JSON artifacts (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Artifact filename prefix (default: derived from rule, geometry, and seed source).",
    )
    return parser


def _parse_generations(value: str) -> tuple[int, ...]:
    generations = sorted({int(part.strip()) for part in value.split(",") if part.strip()})
    if not generations:
        raise ValueError("at least one generation is required")
    if generations[0] < 0:
        raise ValueError("generations must be non-negative")
    return tuple(generations)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        return (31, 36, 48)
    return tuple(int(text[index : index + 2], 16) for index in (0, 2, 4))


def _state_colors(rule: AutomatonRule) -> dict[int, tuple[int, int, int]]:
    return {
        definition.value: _hex_to_rgb(definition.color) for definition in rule.state_definitions()
    }


def _seed_source_name(args: argparse.Namespace) -> str:
    if args.preset:
        return str(args.preset)
    if args.pattern:
        return str(args.pattern)
    if args.cells_json:
        return args.cells_json.stem
    return "seed"


def _default_prefix(args: argparse.Namespace) -> str:
    return "-".join(
        part.replace("_", "-")
        for part in (str(args.rule), str(args.geometry), _seed_source_name(args))
    )


def _load_cells_json(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return {str(cell_id): int(state) for cell_id, state in payload.items()}
    if isinstance(payload, list):
        result: dict[str, int] = {}
        for item in payload:
            if not isinstance(item, dict) or "id" not in item or "state" not in item:
                raise ValueError("--cells-json list items must contain id and state")
            result[str(item["id"])] = int(item["state"])
        return result
    raise ValueError("--cells-json must contain an object or a list")


def _source_name_supported(args: argparse.Namespace) -> None:
    if args.preset is None:
        return
    if args.rule != "whirlpool":
        raise ValueError("--preset currently supports --rule whirlpool only")
    if args.geometry != "square":
        raise ValueError("--preset currently supports --geometry square only")


def _seed_board(args: argparse.Namespace, rule: AutomatonRule) -> SimulationBoard:
    _source_name_supported(args)
    board = empty_board(args.geometry, args.width, args.height, args.patch_depth)
    frame = topology_frame_for(board.topology)
    if args.cells_json:
        return board_from_cells_by_id(
            args.geometry,
            args.width,
            args.height,
            _load_cells_json(args.cells_json),
            args.patch_depth,
        )
    if args.preset:
        cells_by_id = {
            f"c:{cell.x}:{cell.y}": cell.state
            for cell in _build_whirlpool_preset(args.preset, args.width, args.height)
        }
    elif args.pattern:
        cells_by_id = place_pattern(frame, NAMED_PATTERNS[args.pattern])
        cells_by_id = {cell_id: rule.default_paint_state for cell_id in cells_by_id}
    else:
        traversal = TRAVERSALS[args.traversal](frame)
        cells_by_id = paint_bits(
            traversal,
            args.seed or DEFAULT_SEED,
            live=rule.default_paint_state,
        )

    for cell_id, state in cells_by_id.items():
        if board.topology.has_cell(cell_id):
            board.set_state_for(cell_id, state)
    return board


def _state_counts(states: list[int]) -> dict[int, int]:
    return dict(Counter(state for state in states if state != 0))


def _changed_cells(previous: list[int] | None, current: list[int]) -> int | None:
    if previous is None:
        return None
    return sum(1 for left, right in zip(previous, current, strict=True) if left != right)


def _bounding_box(board: SimulationBoard) -> dict[str, int] | None:
    coords: list[tuple[int, int]] = []
    for cell, state in zip(board.topology.cells, board.cell_states, strict=True):
        if state == 0:
            continue
        parsed = parse_regular_cell_id(cell.id)
        if parsed is not None:
            coords.append(parsed)
    if not coords:
        return None
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    return {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)}


def _cell_points(cell: LatticeCell) -> tuple[tuple[float, float], ...]:
    if cell.vertices:
        return tuple((float(x), float(y)) for x, y in cell.vertices)
    if cell.center:
        return ((float(cell.center[0]), float(cell.center[1])),)
    parsed = parse_regular_cell_id(cell.id)
    if parsed is not None:
        return ((float(parsed[0]), float(parsed[1])),)
    return ()


def _topology_bounds(board: SimulationBoard) -> tuple[float, float, float, float]:
    points = [point for cell in board.topology.cells for point in _cell_points(cell)]
    if not points:
        return (0.0, 0.0, 1.0, 1.0)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if min_x == max_x:
        max_x = min_x + 1.0
    if min_y == max_y:
        max_y = min_y + 1.0
    return min_x, min_y, max_x, max_y


def _render_frame(
    board: SimulationBoard,
    rule: AutomatonRule,
    generation: int,
    path: Path,
    *,
    cell_size: int,
) -> None:
    min_x, min_y, max_x, max_y = _topology_bounds(board)
    width = max(1, int(math.ceil((max_x - min_x + 1) * cell_size))) + FRAME_PADDING * 2
    height = (
        max(1, int(math.ceil((max_y - min_y + 1) * cell_size))) + FRAME_PADDING * 2 + LABEL_HEIGHT
    )
    scale = min(
        (width - FRAME_PADDING * 2) / (max_x - min_x + 1),
        (height - LABEL_HEIGHT - FRAME_PADDING * 2) / (max_y - min_y + 1),
    )
    image = Image.new("RGB", (width, height), _hex_to_rgb(BACKGROUND))
    draw = ImageDraw.Draw(image)
    colors = _state_colors(rule)

    def transform(point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        return (
            FRAME_PADDING + (x - min_x + 0.5) * scale,
            LABEL_HEIGHT + FRAME_PADDING + (y - min_y + 0.5) * scale,
        )

    draw.text((FRAME_PADDING, 7), f"{rule.name}  g{generation}", fill=(18, 24, 32))
    marker_radius = max(1.0, scale * 0.45)
    for cell, state in zip(board.topology.cells, board.cell_states, strict=True):
        if state == 0:
            continue
        fill = colors.get(state, (31, 36, 48))
        if cell.vertices and len(cell.vertices) >= 3:
            draw.polygon([transform(vertex) for vertex in cell.vertices], fill=fill)
            continue
        points = _cell_points(cell)
        if not points:
            continue
        cx, cy = transform(points[0])
        draw.rectangle(
            (
                round(cx - marker_radius),
                round(cy - marker_radius),
                round(cx + marker_radius),
                round(cy + marker_radius),
            ),
            fill=fill,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _write_montage(frame_paths: list[Path], output_path: Path) -> None:
    frames = [Image.open(path).convert("RGB") for path in frame_paths]
    width = sum(frame.width for frame in frames) + MONTAGE_GAP * (len(frames) + 1)
    height = max(frame.height for frame in frames) + MONTAGE_GAP * 2
    montage = Image.new("RGB", (width, height), _hex_to_rgb(MONTAGE_BG))
    x = MONTAGE_GAP
    for frame in frames:
        montage.paste(frame, (x, MONTAGE_GAP))
        x += frame.width + MONTAGE_GAP
    output_path.parent.mkdir(parents=True, exist_ok=True)
    montage.save(output_path)
    for frame in frames:
        frame.close()


def run_review(args: argparse.Namespace) -> dict[str, object]:
    generations = _parse_generations(args.generations)
    if args.width <= 0 or args.height <= 0:
        raise ValueError("--width and --height must be positive")
    if args.cell_size <= 0:
        raise ValueError("--cell-size must be positive")

    rule = RuleRegistry().get(args.rule)
    if not rule.supports_tiling_family(args.geometry):
        raise ValueError(f"rule {rule.name!r} does not support geometry {args.geometry!r}")

    prefix = args.prefix or _default_prefix(args)
    output_dir = args.output_dir
    frames_dir = output_dir / prefix
    board = _seed_board(args, rule)
    engine = SimulationEngine()
    reviews: list[FrameReview] = []
    previous_states: list[int] | None = None
    target_generations = set(generations)
    max_generation = max(generations)

    for generation in range(max_generation + 1):
        if generation in target_generations:
            image_path = frames_dir / f"g{generation:04d}.png"
            _render_frame(board, rule, generation, image_path, cell_size=args.cell_size)
            counts = _state_counts(board.cell_states)
            reviews.append(
                FrameReview(
                    generation=generation,
                    image_path=image_path,
                    state_counts=counts,
                    live_cells=sum(counts.values()),
                    changed_cells=_changed_cells(previous_states, board.cell_states),
                    bounding_box=_bounding_box(board),
                )
            )
        previous_states = board.cell_states.copy()
        if generation < max_generation:
            board = engine.step_board(board, rule)

    montage_path = output_dir / f"{prefix}-montage.png"
    _write_montage([review.image_path for review in reviews], montage_path)
    summary_path = output_dir / f"{prefix}-summary.json"
    summary: dict[str, object] = {
        "rule": rule.name,
        "geometry": args.geometry,
        "width": args.width,
        "height": args.height,
        "patch_depth": args.patch_depth,
        "seed_source": _seed_source_name(args),
        "generations": list(generations),
        "montage": str(montage_path.relative_to(output_dir)),
        "frames": [review.to_dict(root=output_dir) for review in reviews],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {
        "summary": summary,
        "summary_path": str(summary_path),
        "montage_path": str(montage_path),
    }


def _build_whirlpool_preset(name: str, width: int, height: int) -> list[CartesianSeedCell]:
    if name == "anchored-source-vortex":
        return _build_vortex_seed(
            width,
            height,
            arms=[
                {
                    "angle_origin": -0.64,
                    "twist": 1.58,
                    "normalized_radii": [0.2, 0.26, 0.32, 0.39, 0.46, 0.53],
                    "angular_offsets": [-1.08, -0.82, -0.55, -0.28, -0.02, 0.22, 0.49, 0.78],
                    "gap_ranges": [(0.0, 0.34)],
                }
            ],
            arcs=[
                {
                    "state": 3,
                    "angle_origin": -0.64,
                    "normalized_radii": [0.22, 0.26, 0.3],
                    "angular_offsets": [0.52, 0.76, 0.98],
                }
            ],
            sources=[
                {"angle_origin": -0.64, "normalized_radius": 0.28, "angular_offset": 0.14},
                {"angle_origin": -0.64, "normalized_radius": 0.52, "angular_offset": 0.62},
            ],
        )
    if name == "dual-source-vortex":
        return _build_vortex_seed(
            width,
            height,
            arms=[
                {
                    "angle_origin": -0.58,
                    "twist": 1.54,
                    "normalized_radii": [0.2, 0.27, 0.34, 0.41, 0.49, 0.57],
                    "angular_offsets": [-1.06, -0.78, -0.5, -0.22, 0.04, 0.31, 0.59, 0.88],
                    "gap_ranges": [(0.08, 0.42)],
                }
            ],
            arcs=[
                {
                    "state": 3,
                    "angle_origin": -0.58,
                    "normalized_radii": [0.24, 0.29],
                    "angular_offsets": [0.56, 0.82, 1.05],
                }
            ],
            sources=[
                {"angle_origin": -0.58, "normalized_radius": 0.31, "angular_offset": 0.08},
                {"angle_origin": 1.68, "normalized_radius": 0.43, "angular_offset": 0.0},
            ],
        )
    raise ValueError(f"unknown Whirlpool preset: {name}")


def _square_grid_center(width: int, height: int) -> tuple[float, float]:
    return (width - 1) / 2, (height - 1) / 2


def _square_max_radius(width: int, height: int) -> float:
    cx, cy = _square_grid_center(width, height)
    corners = ((0.0, 0.0), (width - 1.0, 0.0), (0.0, height - 1.0), (width - 1.0, height - 1.0))
    return max(*(math.hypot(x - cx, y - cy) for x, y in corners), 1.0)


def _wrap_angle(angle: float) -> float:
    while angle <= -math.pi:
        angle += 2 * math.pi
    while angle > math.pi:
        angle -= 2 * math.pi
    return angle


def _inside_any_range(value: float, ranges: list[tuple[float, float]]) -> bool:
    return any(start <= value <= end for start, end in ranges)


def _nearest_untaken(
    width: int,
    height: int,
    taken: set[tuple[int, int]],
    target_x: float,
    target_y: float,
) -> tuple[int, int] | None:
    best: tuple[float, int, int] | None = None
    for y in range(height):
        for x in range(width):
            if (x, y) in taken:
                continue
            distance = (x - target_x) ** 2 + (y - target_y) ** 2
            if best is None or distance < best[0]:
                best = (distance, x, y)
    if best is None:
        return None
    return best[1], best[2]


def _place_polar_sample(
    *,
    width: int,
    height: int,
    center: tuple[float, float],
    max_radius: float,
    taken: set[tuple[int, int]],
    normalized_radius: float,
    angle_origin: float = 0.0,
    angular_offset: float = 0.0,
    state: int = 4,
) -> CartesianSeedCell | None:
    angle = angle_origin + angular_offset
    target_x = center[0] + math.cos(angle) * max_radius * normalized_radius
    target_y = center[1] + math.sin(angle) * max_radius * normalized_radius
    nearest = _nearest_untaken(width, height, taken, target_x, target_y)
    if nearest is None:
        return None
    taken.add(nearest)
    return CartesianSeedCell(nearest[0], nearest[1], state)


def _build_vortex_seed(
    width: int,
    height: int,
    *,
    arms: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    arcs: list[dict[str, Any]],
) -> list[CartesianSeedCell]:
    center = _square_grid_center(width, height)
    max_radius = _square_max_radius(width, height)
    cells: list[CartesianSeedCell] = []
    taken: set[tuple[int, int]] = set()

    for arm in arms:
        radial_samples = arm["normalized_radii"]
        angular_offsets = [
            value
            for value in arm["angular_offsets"]
            if not _inside_any_range(value, arm.get("gap_ranges", []))
        ]
        angle_origin = float(arm.get("angle_origin", -0.58))
        twist = float(arm.get("twist", 1.6))
        for normalized_radius in radial_samples:
            for angular_offset in angular_offsets:
                angle = angle_origin + angular_offset
                target_x = center[0] + math.cos(angle) * max_radius * normalized_radius
                target_y = center[1] + math.sin(angle) * max_radius * normalized_radius
                nearest = _nearest_untaken(width, height, taken, target_x, target_y)
                if nearest is None:
                    continue
                taken.add(nearest)
                dx = nearest[0] - center[0]
                dy = nearest[1] - center[1]
                phase = _wrap_angle(math.atan2(dy, dx) - angle_origin) + twist * (
                    math.hypot(dx, dy) / max_radius
                )
                state = 1
                if phase < -0.32:
                    state = 3
                elif phase < 0.0:
                    state = 2
                cells.append(CartesianSeedCell(nearest[0], nearest[1], state))

    for arc in arcs:
        for normalized_radius in arc["normalized_radii"]:
            for angular_offset in arc["angular_offsets"]:
                cell = _place_polar_sample(
                    width=width,
                    height=height,
                    center=center,
                    max_radius=max_radius,
                    taken=taken,
                    normalized_radius=normalized_radius,
                    angle_origin=float(arc.get("angle_origin", 0.0)),
                    angular_offset=angular_offset,
                    state=int(arc.get("state", 3)),
                )
                if cell is not None:
                    cells.append(cell)

    for source in sources:
        cell = _place_polar_sample(
            width=width,
            height=height,
            center=center,
            max_radius=max_radius,
            taken=taken,
            normalized_radius=float(source["normalized_radius"]),
            angle_origin=float(source.get("angle_origin", 0.0)),
            angular_offset=float(source.get("angular_offset", 0.0)),
            state=int(source.get("state", 4)),
        )
        if cell is not None:
            cells.append(cell)
    return cells


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_review(args)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"summary: {result['summary_path']}")
    print(f"montage: {result['montage_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
