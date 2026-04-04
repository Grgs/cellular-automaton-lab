from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.defaults import (
    DEFAULT_HEIGHT,
    DEFAULT_ADJACENCY_MODE,
    DEFAULT_GEOMETRY,
    DEFAULT_PATCH_DEPTH,
    DEFAULT_SPEED,
    DEFAULT_TILING_FAMILY,
    DEFAULT_WIDTH,
    MAX_GRID_SIZE,
    MAX_PATCH_DEPTH,
    MAX_SPEED,
    MIN_PATCH_DEPTH,
    MIN_SPEED,
)
from backend.payload_types import (
    CellStatePayload,
    RuleDefinitionPayload,
    SimulationStatePayload,
    TopologySpecInput,
    TopologySpecPayload,
)
from backend.simulation.topology_catalog import (
    minimum_grid_dimension_for_geometry,
    EDGE_ADJACENCY,
    get_topology_definition,
    get_topology_variant_for_geometry,
    maximum_patch_depth_for_tiling_family,
    minimum_patch_depth_for_tiling_family,
    normalize_adjacency_mode,
    resolve_geometry_key,
)
from backend.simulation.topology import (
    LatticeTopology,
    SimulationBoard,
)

if TYPE_CHECKING:
    from backend.rules.base import AutomatonRule

def clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(int(value), maximum))


def clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(float(value), maximum))


def _coerce_optional_int(value: object, fallback: int) -> int:
    if value is None:
        return fallback
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return int(value)
    raise TypeError(f"Expected an int-compatible value, received {type(value).__name__}.")


def _topology_spec_string_value(
    topology_spec: TopologySpecInput,
    key: str,
    fallback: str,
) -> str:
    value = topology_spec.get(key)
    return fallback if value is None else str(value)


def _topology_spec_int_value(
    topology_spec: TopologySpecInput,
    key: str,
    fallback: int,
) -> int:
    return _coerce_optional_int(topology_spec.get(key), fallback)


def _topology_spec_bool_value(
    topology_spec: TopologySpecInput,
    key: str,
    fallback: bool = False,
) -> bool:
    value = topology_spec.get(key)
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    raise TypeError(f"Expected a bool-compatible value, received {type(value).__name__}.")


MAX_UNSAFE_PATCH_DEPTH = 12

@dataclass(frozen=True)
class TopologySpec:
    tiling_family: str = DEFAULT_TILING_FAMILY
    adjacency_mode: str = DEFAULT_ADJACENCY_MODE
    sizing_mode: str = "grid"
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    patch_depth: int = DEFAULT_PATCH_DEPTH
    unsafe_size_override: bool = False

    @classmethod
    def from_values(
        cls,
        tiling_family: str = DEFAULT_TILING_FAMILY,
        adjacency_mode: str | None = DEFAULT_ADJACENCY_MODE,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        patch_depth: int = DEFAULT_PATCH_DEPTH,
        unsafe_size_override: bool = False,
    ) -> "TopologySpec":
        tiling_family_id = str(tiling_family)
        definition = get_topology_definition(tiling_family_id)
        resolved_adjacency_mode = normalize_adjacency_mode(tiling_family_id, adjacency_mode)
        geometry_id = resolve_geometry_key(tiling_family_id, resolved_adjacency_mode)
        minimum_grid_size = minimum_grid_dimension_for_geometry(geometry_id)
        if definition.sizing_mode != "patch_depth":
            normalized_patch_depth = DEFAULT_PATCH_DEPTH
        elif unsafe_size_override:
            normalized_patch_depth = clamp_int(
                patch_depth,
                MIN_PATCH_DEPTH,
                MAX_UNSAFE_PATCH_DEPTH,
            )
        else:
            normalized_patch_depth = clamp_int(
                patch_depth,
                minimum_patch_depth_for_tiling_family(tiling_family_id),
                maximum_patch_depth_for_tiling_family(tiling_family_id),
            )
        return cls(
            tiling_family=tiling_family_id,
            adjacency_mode=resolved_adjacency_mode,
            sizing_mode=definition.sizing_mode,
            width=clamp_int(width, minimum_grid_size, MAX_GRID_SIZE),
            height=clamp_int(height, minimum_grid_size, MAX_GRID_SIZE),
            patch_depth=normalized_patch_depth,
            unsafe_size_override=bool(unsafe_size_override),
        )

    @classmethod
    def from_geometry_key(
        cls,
        geometry: str = DEFAULT_GEOMETRY,
        *,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        patch_depth: int = DEFAULT_PATCH_DEPTH,
    ) -> "TopologySpec":
        variant = get_topology_variant_for_geometry(str(geometry))
        return cls.from_values(
            tiling_family=variant.tiling_family,
            adjacency_mode=variant.adjacency_mode,
            width=width,
            height=height,
            patch_depth=patch_depth,
        )

    def updated(
        self,
        tiling_family: str | None = None,
        adjacency_mode: str | None = None,
        width: int | None = None,
        height: int | None = None,
        patch_depth: int | None = None,
        unsafe_size_override: bool | None = None,
    ) -> "TopologySpec":
        return self.from_values(
            tiling_family=self.tiling_family if tiling_family is None else tiling_family,
            adjacency_mode=self.adjacency_mode if adjacency_mode is None else adjacency_mode,
            width=self.width if width is None else width,
            height=self.height if height is None else height,
            patch_depth=self.patch_depth if patch_depth is None else patch_depth,
            unsafe_size_override=self.unsafe_size_override if unsafe_size_override is None else unsafe_size_override,
        )

    @property
    def geometry_key(self) -> str:
        return resolve_geometry_key(self.tiling_family, self.adjacency_mode)

    def to_dict(self) -> TopologySpecPayload:
        return {
            "tiling_family": self.tiling_family,
            "adjacency_mode": self.adjacency_mode,
            "sizing_mode": self.sizing_mode,
            "width": self.width,
            "height": self.height,
            "patch_depth": self.patch_depth,
        }


@dataclass(frozen=True)
class SimulationConfig:
    topology_spec: TopologySpec = TopologySpec()
    speed: float = DEFAULT_SPEED

    @classmethod
    def from_values(
        cls,
        *,
        topology_spec: TopologySpec | TopologySpecInput | None = None,
        tiling_family: str = DEFAULT_TILING_FAMILY,
        adjacency_mode: str | None = DEFAULT_ADJACENCY_MODE,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        speed: float = DEFAULT_SPEED,
        patch_depth: int = DEFAULT_PATCH_DEPTH,
    ) -> "SimulationConfig":
        resolved_topology_spec: TopologySpec
        if isinstance(topology_spec, TopologySpec):
            resolved_topology_spec = TopologySpec.from_values(
                tiling_family=topology_spec.tiling_family,
                adjacency_mode=topology_spec.adjacency_mode,
                width=topology_spec.width,
                height=topology_spec.height,
                patch_depth=topology_spec.patch_depth,
                unsafe_size_override=topology_spec.unsafe_size_override,
            )
        elif topology_spec is not None:
            resolved_topology_spec = TopologySpec.from_values(
                tiling_family=_topology_spec_string_value(topology_spec, "tiling_family", tiling_family),
                adjacency_mode=_topology_spec_string_value(
                    topology_spec,
                    "adjacency_mode",
                    adjacency_mode or EDGE_ADJACENCY,
                ),
                width=_topology_spec_int_value(topology_spec, "width", width),
                height=_topology_spec_int_value(topology_spec, "height", height),
                patch_depth=_topology_spec_int_value(topology_spec, "patch_depth", patch_depth),
                unsafe_size_override=_topology_spec_bool_value(topology_spec, "unsafe_size_override"),
            )
        else:
            resolved_topology_spec = TopologySpec.from_values(
                tiling_family=tiling_family,
                adjacency_mode=adjacency_mode,
                width=width,
                height=height,
                patch_depth=patch_depth,
            )
        return cls(
            topology_spec=resolved_topology_spec,
            speed=clamp_float(speed, MIN_SPEED, MAX_SPEED),
        )

    @property
    def geometry(self) -> str:
        return self.topology_spec.geometry_key

    @property
    def tiling_family(self) -> str:
        return self.topology_spec.tiling_family

    @property
    def adjacency_mode(self) -> str:
        return self.topology_spec.adjacency_mode

    @property
    def sizing_mode(self) -> str:
        return self.topology_spec.sizing_mode

    @property
    def width(self) -> int:
        return self.topology_spec.width

    @property
    def height(self) -> int:
        return self.topology_spec.height

    @property
    def patch_depth(self) -> int:
        return self.topology_spec.patch_depth

    def updated(
        self,
        topology_spec: TopologySpec | TopologySpecInput | None = None,
        tiling_family: str | None = None,
        adjacency_mode: str | None = None,
        width: int | None = None,
        height: int | None = None,
        speed: float | None = None,
        patch_depth: int | None = None,
    ) -> "SimulationConfig":
        if topology_spec is not None:
            if isinstance(topology_spec, TopologySpec):
                base_topology_spec = self.from_values(
                    topology_spec=topology_spec,
                    width=self.width if width is None else width,
                    height=self.height if height is None else height,
                    patch_depth=self.patch_depth if patch_depth is None else patch_depth,
                ).topology_spec
            else:
                next_width_value = topology_spec.get("width")
                next_height_value = topology_spec.get("height")
                next_patch_depth_value = topology_spec.get("patch_depth")
                base_topology_spec = self.topology_spec.updated(
                    tiling_family=(
                        self.tiling_family
                        if topology_spec.get("tiling_family") is None
                        else str(topology_spec.get("tiling_family"))
                    ),
                    adjacency_mode=(
                        self.adjacency_mode
                        if topology_spec.get("adjacency_mode") is None
                        else str(topology_spec.get("adjacency_mode"))
                    ),
                    width=(
                        self.width
                        if next_width_value is None
                        else _coerce_optional_int(next_width_value, self.width)
                    ),
                    height=(
                        self.height
                        if next_height_value is None
                        else _coerce_optional_int(next_height_value, self.height)
                    ),
                    patch_depth=(
                        self.patch_depth
                        if next_patch_depth_value is None
                        else _coerce_optional_int(next_patch_depth_value, self.patch_depth)
                    ),
                    unsafe_size_override=_topology_spec_bool_value(topology_spec, "unsafe_size_override"),
                )
        else:
            base_topology_spec = self.topology_spec.updated(
                tiling_family=self.tiling_family if tiling_family is None else tiling_family,
                adjacency_mode=self.adjacency_mode if adjacency_mode is None else adjacency_mode,
                width=self.width if width is None else width,
                height=self.height if height is None else height,
                patch_depth=self.patch_depth if patch_depth is None else patch_depth,
            )
        return self.from_values(
            topology_spec=base_topology_spec,
            speed=self.speed if speed is None else speed,
        )


@dataclass(frozen=True)
class RuleSnapshot:
    name: str
    display_name: str
    description: str
    states: list[CellStatePayload]
    default_paint_state: int
    supports_randomize: bool
    rule_protocol: str
    supports_all_topologies: bool

    @classmethod
    def from_rule(cls, rule: AutomatonRule) -> "RuleSnapshot":
        return cls(
            name=rule.name,
            display_name=rule.display_name,
            description=rule.description,
            states=[state.to_dict() for state in rule.state_definitions()],
            default_paint_state=rule.default_paint_state,
            supports_randomize=rule.supports_randomize,
            rule_protocol=rule.rule_protocol,
            supports_all_topologies=rule.supports_all_topologies,
        )

    def to_dict(self) -> RuleDefinitionPayload:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "states": self.states,
            "default_paint_state": self.default_paint_state,
            "supports_randomize": self.supports_randomize,
            "rule_protocol": self.rule_protocol,
            "supports_all_topologies": self.supports_all_topologies,
        }


@dataclass(frozen=True)
class SimulationSnapshot:
    board: SimulationBoard
    config: SimulationConfig
    running: bool
    generation: int
    rule: RuleSnapshot

    @property
    def topology(self) -> LatticeTopology:
        return self.board.topology

    @property
    def cell_states(self) -> list[int]:
        return self.board.cell_states

    @property
    def cells_by_id(self) -> dict[str, int]:
        return self.board.states_by_id(omit_zero=True)

    def to_dict(self) -> SimulationStatePayload:
        return {
            "topology_spec": self.config.topology_spec.to_dict(),
            "speed": self.config.speed,
            "running": self.running,
            "generation": self.generation,
            "rule": self.rule.to_dict(),
            "topology_revision": self.topology.topology_revision,
            "cell_states": self.cell_states,
            "topology": self.topology.to_dict(),
        }


@dataclass
class SimulationStateData:
    config: SimulationConfig
    running: bool
    generation: int
    rule: AutomatonRule
    board: SimulationBoard

    @property
    def topology(self) -> LatticeTopology:
        return self.board.topology
