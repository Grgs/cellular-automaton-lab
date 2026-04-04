from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from backend.simulation.topology_catalog_types import TopologyDefinition

if TYPE_CHECKING:
    from backend.simulation.topology_catalog_types import (
        SizingPolicyDefinition,
        TopologyVariantDefinition,
    )


def build_topology_catalog(
    variants: tuple[TopologyVariantDefinition, ...],
    sizing_policies: dict[str, SizingPolicyDefinition],
    picker_group_order: dict[str, int],
    render_kind_for_geometry: Callable[[str], str],
) -> tuple[TopologyDefinition, ...]:
    grouped: dict[str, list[TopologyVariantDefinition]] = {}
    for variant in variants:
        grouped.setdefault(variant.tiling_family, []).append(variant)

    catalog: list[TopologyDefinition] = []
    for tiling_family, family_variants in grouped.items():
        family_variants.sort(key=lambda entry: (entry.adjacency_mode != "edge", entry.adjacency_mode))
        first = family_variants[0]
        catalog.append(
            TopologyDefinition(
                tiling_family=tiling_family,
                label=first.label,
                picker_group=first.picker_group,
                picker_order=first.picker_order,
                sizing_mode=first.sizing_mode,
                family=first.family,
                render_kind=str(render_kind_for_geometry(first.geometry_key)),
                viewport_sync_mode=first.viewport_sync_mode,
                supported_adjacency_modes=tuple(variant.adjacency_mode for variant in family_variants),
                default_adjacency_mode=family_variants[0].adjacency_mode,
                default_rules={
                    variant.adjacency_mode: variant.default_rule
                    for variant in family_variants
                },
                geometry_keys={
                    variant.adjacency_mode: variant.geometry_key
                    for variant in family_variants
                },
                sizing_policy=sizing_policies[tiling_family],
            )
        )
    catalog.sort(
        key=lambda definition: (
            picker_group_order.get(definition.picker_group, 99),
            definition.picker_order,
            definition.label.lower(),
        )
    )
    return tuple(catalog)
