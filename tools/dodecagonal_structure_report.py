from __future__ import annotations

from typing import Any


def render_text_report(summary: Any) -> str:
    lines = [
        "Dodecagonal Square-Triangle Structure Mining",
        (
            f"source_cells={summary.source_cell_count} seed_index={summary.seed_index} "
            f"max_available_depth={summary.max_available_depth} analyzed_roots={summary.analyzed_root_count}"
        ),
        (
            f"neighborhood_radius={summary.neighborhood_radius} region_radius={summary.region_radius} "
            f"max_candidate_size={summary.max_candidate_size} min_candidate_size={summary.min_candidate_size} "
            f"beam_width={summary.beam_width}"
        ),
        "",
        "Top Local Neighborhood Classes",
    ]
    if not summary.local_neighborhood_classes:
        lines.append("  none")
    for neighborhood_class in summary.local_neighborhood_classes:
        lines.extend([
            (
                f"  signature={neighborhood_class.signature} count={neighborhood_class.count} "
                f"kinds={dict(neighborhood_class.kind_counts)} depths={dict(neighborhood_class.depth_histogram)}"
            ),
            f"    example_cells={list(neighborhood_class.example_cells)}",
        ])

    lines.extend(["", "Macro Candidate Groups"])
    if not summary.macro_candidate_groups:
        lines.append("  none")
    for macro_group in summary.macro_candidate_groups:
        lines.extend([
            (
                f"  macro_kind={macro_group.macro_kind} occurrence_count={macro_group.occurrence_count} "
                f"cell_count={macro_group.cell_count} side_count={macro_group.side_count} "
                f"area_ratio≈{macro_group.quantized_area_ratio}"
            ),
            (
                f"    edge_signature={list(macro_group.edge_length_signature)} "
                f"angle_signature={list(macro_group.angle_signature)}"
            ),
            f"    root_signatures={dict(macro_group.root_signature_counts)}",
            f"    example_roots={list(macro_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in macro_group.example_subsets]}",
        ])

    lines.extend(["", "Seeded Supertile Groups"])
    if not summary.seeded_supertile_groups:
        lines.append("  none")
    for supertile_group in summary.seeded_supertile_groups:
        lines.extend([
            (
                f"  seed_macro_kind={supertile_group.seed_macro_kind} seed_cell_count={supertile_group.seed_cell_count} "
                f"grown_macro_kind={supertile_group.grown_macro_kind} grown_cell_count={supertile_group.grown_cell_count} "
                f"occurrence_count={supertile_group.occurrence_count} side_count={supertile_group.side_count} "
                f"area_ratio≈{supertile_group.quantized_area_ratio}"
            ),
            (
                f"    selected_slots={list(supertile_group.selected_slots)} "
                f"line_families={dict(supertile_group.boundary_direction_histogram)} "
                f"marked_cells={dict(supertile_group.marked_cell_signature)}"
            ),
            (
                f"    edge_signature={list(supertile_group.edge_length_signature)} "
                f"angle_signature={list(supertile_group.angle_signature)}"
            ),
            f"    example_roots={list(supertile_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in supertile_group.example_subsets]}",
        ])

    lines.extend(["", "Inflation Candidate Groups"])
    if not summary.inflation_candidate_groups:
        lines.append("  none")
    for inflation_group in summary.inflation_candidate_groups:
        lines.extend([
            (
                f"  seed_macro_kind={inflation_group.seed_macro_kind} base_cell_count={inflation_group.base_cell_count} "
                f"grown_macro_kind={inflation_group.grown_macro_kind} grown_cell_count={inflation_group.grown_cell_count} "
                f"occurrence_count={inflation_group.occurrence_count} combo_size={inflation_group.combo_size} "
                f"side_count={inflation_group.side_count} area_ratio≈{inflation_group.quantized_area_ratio} "
                f"inflation≈{inflation_group.inflation_estimate}"
            ),
            (
                f"    selected_slots={list(inflation_group.selected_slots)} "
                f"line_families={dict(inflation_group.boundary_direction_histogram)} "
                f"marked_cells={dict(inflation_group.marked_cell_signature)}"
            ),
            (
                f"    edge_signature={list(inflation_group.edge_length_signature)} "
                f"angle_signature={list(inflation_group.angle_signature)}"
            ),
            f"    example_roots={list(inflation_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in inflation_group.example_subsets]}",
        ])

    lines.extend(["", "Boundary Template Groups"])
    if not summary.boundary_template_groups:
        lines.append("  none")
    for template_group in summary.boundary_template_groups:
        lines.extend([
            (
                f"  seed_macro_kind={template_group.seed_macro_kind} base_cell_count={template_group.base_cell_count} "
                f"candidate_cell_count={template_group.candidate_cell_count} occurrence_count={template_group.occurrence_count} "
                f"template_match_count={template_group.template_match_count} template_variants={template_group.template_variant_count} "
                f"side_count={template_group.side_count} area_ratio≈{template_group.quantized_area_ratio} "
                f"inflation≈{template_group.inflation_estimate}"
            ),
            (
                f"    selected_slots={list(template_group.selected_slots)} "
                f"line_families="
                f"{ {family.axis_angle: list(family.offsets) for family in template_group.line_families} } "
                f"marked_cells={dict(template_group.marked_cell_signature)}"
            ),
            f"    canonical_vertices={list(template_group.canonical_vertices)}",
            f"    example_roots={list(template_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in template_group.example_subsets]}",
        ])

    lines.extend(["", "Supertile Decomposition Groups"])
    if not summary.supertile_decomposition_groups:
        lines.append("  none")
    for decomposition_group in summary.supertile_decomposition_groups:
        lines.extend([
            (
                f"  seed_macro_kind={decomposition_group.seed_macro_kind} "
                f"base_cell_count={decomposition_group.base_cell_count} "
                f"candidate_cell_count={decomposition_group.candidate_cell_count} "
                f"template_match_count={decomposition_group.template_match_count}"
            ),
            f"    line_equations={[equation.equation for equation in decomposition_group.line_equations]}",
            f"    canonical_vertices={list(decomposition_group.canonical_vertices)}",
        ])
        for component_group in decomposition_group.component_groups:
            lines.extend([
                (
                    f"    region_signature={list(component_group.region_signature)} "
                    f"macro_kind={component_group.component_macro_kind} "
                    f"cell_count={component_group.cell_count} "
                    f"occurrence_count={component_group.occurrence_count} "
                    f"side_count={component_group.side_count} "
                    f"area_ratio≈{component_group.quantized_area_ratio}"
                ),
                f"      marked_cells={dict(component_group.marked_cell_signature)}",
                f"      example_roots={list(component_group.example_roots)}",
                f"      example_subsets={[list(subset) for subset in component_group.example_subsets]}",
            ])

    lines.extend(["", "Macro Composition Groups"])
    if not summary.macro_composition_groups:
        lines.append("  none")
    for composition_group in summary.macro_composition_groups:
        lines.extend([
            (
                f"  seed_macro_kind={composition_group.seed_macro_kind} "
                f"base_cell_count={composition_group.base_cell_count} "
                f"candidate_cell_count={composition_group.candidate_cell_count} "
                f"template_match_count={composition_group.template_match_count} "
                f"composition_macro_kind={composition_group.composition_macro_kind} "
                f"composed_cell_count={composition_group.composed_cell_count} "
                f"occurrence_count={composition_group.occurrence_count} "
                f"side_count={composition_group.side_count} "
                f"area_ratio≈{composition_group.quantized_area_ratio}"
            ),
            f"    component_region_signatures={[list(signature) for signature in composition_group.component_region_signatures]}",
            f"    marked_cells={dict(composition_group.marked_cell_signature)}",
            f"    example_roots={list(composition_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in composition_group.example_subsets]}",
        ])

    lines.extend(["", "Recovered Substitution Rules"])
    if not summary.recovered_substitution_rules:
        lines.append("  none")
    for rule in summary.recovered_substitution_rules:
        lines.extend([
            (
                f"  seed_macro_kind={rule.seed_macro_kind} "
                f"base_cell_count={rule.base_cell_count} "
                f"candidate_cell_count={rule.candidate_cell_count} "
                f"template_match_count={rule.template_match_count} "
                f"verified_template_match_count={rule.verified_template_match_count} "
                f"verified_child_rule_count={rule.verified_child_rule_count} "
                f"verified_rule_ratio={rule.verified_rule_ratio}"
            ),
            f"    line_equations={[equation.equation for equation in rule.line_equations]}",
            f"    residual_region_signatures={[list(signature) for signature in rule.residual_region_signatures]}",
            f"    verification_max_source_depth={rule.verification_max_source_depth}",
            f"    example_roots={list(rule.example_roots)}",
            f"    example_subsets={[list(subset) for subset in rule.example_subsets]}",
        ])
        for child_rule in rule.child_rules:
            lines.extend([
                (
                    f"    child_macro_kind={child_rule.macro_kind} "
                    f"cell_count={child_rule.cell_count} "
                    f"occurrence_count={child_rule.occurrence_count} "
                    f"verified_occurrence_count={child_rule.verified_occurrence_count}"
                ),
                f"      component_region_signatures={[list(signature) for signature in child_rule.component_region_signatures]}",
                f"      marked_cells={dict(child_rule.marked_cell_signature)}",
            ])

    lines.extend(["", "Recovered Parent Decompositions"])
    if not summary.recovered_parent_decompositions:
        lines.append("  none")
    for decomposition in summary.recovered_parent_decompositions:
        lines.extend([
            (
                f"  seed_macro_kind={decomposition.seed_macro_kind} "
                f"base_cell_count={decomposition.base_cell_count} "
                f"candidate_cell_count={decomposition.candidate_cell_count} "
                f"template_match_count={decomposition.template_match_count} "
                f"verified_template_match_count={decomposition.verified_template_match_count} "
                f"coverage_ratio={decomposition.coverage_ratio} "
                f"verified_piece_count={decomposition.verified_piece_count} "
                f"verified_piece_ratio={decomposition.verified_piece_ratio}"
            ),
            f"    covered_region_signatures={[list(signature) for signature in decomposition.covered_region_signatures]}",
            f"    uncovered_region_signatures={[list(signature) for signature in decomposition.uncovered_region_signatures]}",
            f"    verification_max_source_depth={decomposition.verification_max_source_depth}",
            f"    example_roots={list(decomposition.example_roots)}",
            f"    example_subsets={[list(subset) for subset in decomposition.example_subsets]}",
        ])
        for piece in decomposition.child_pieces:
            lines.extend([
                (
                    f"    piece_kind={piece.piece_kind} "
                    f"macro_kind={piece.macro_kind} "
                    f"cell_count={piece.cell_count} "
                    f"occurrence_count={piece.occurrence_count} "
                    f"verified_occurrence_count={piece.verified_occurrence_count}"
                ),
                f"      component_region_signatures={[list(signature) for signature in piece.component_region_signatures]}",
                f"      marked_cells={dict(piece.marked_cell_signature)}",
            ])

    lines.extend(["", "Canonical Parent Rules"])
    if not summary.canonical_parent_rules:
        lines.append("  none")
    for canonical_rule in summary.canonical_parent_rules:
        lines.extend([
            (
                f"  seed_macro_kind={canonical_rule.seed_macro_kind} "
                f"base_cell_count={canonical_rule.base_cell_count} "
                f"candidate_cell_count={canonical_rule.candidate_cell_count} "
                f"template_match_count={canonical_rule.template_match_count} "
                f"verified_template_match_count={canonical_rule.verified_template_match_count} "
                f"coverage_ratio={canonical_rule.coverage_ratio} "
                f"piece_count={canonical_rule.piece_count} "
                f"composition_piece_count={canonical_rule.composition_piece_count} "
                f"verified_piece_count={canonical_rule.verified_piece_count} "
                f"weak_piece_count={canonical_rule.weak_piece_count} "
                f"verified_piece_ratio={canonical_rule.verified_piece_ratio}"
            ),
            f"    line_equations={[equation.equation for equation in canonical_rule.line_equations]}",
            f"    covered_region_signatures={[list(signature) for signature in canonical_rule.covered_region_signatures]}",
            f"    uncovered_region_signatures={[list(signature) for signature in canonical_rule.uncovered_region_signatures]}",
            f"    verification_max_source_depth={canonical_rule.verification_max_source_depth}",
            f"    example_roots={list(canonical_rule.example_roots)}",
            f"    example_subsets={[list(subset) for subset in canonical_rule.example_subsets]}",
        ])
        for piece in canonical_rule.child_pieces:
            lines.extend([
                (
                    f"    piece_kind={piece.piece_kind} "
                    f"macro_kind={piece.macro_kind} "
                    f"cell_count={piece.cell_count} "
                    f"occurrence_count={piece.occurrence_count} "
                    f"verified_occurrence_count={piece.verified_occurrence_count}"
                ),
                f"      component_region_signatures={[list(signature) for signature in piece.component_region_signatures]}",
                f"      marked_cells={dict(piece.marked_cell_signature)}",
            ])

    lines.extend(["", "Evidence Parent Rules"])
    if not summary.evidence_parent_rules:
        lines.append("  none")
    for evidence_rule in summary.evidence_parent_rules:
        lines.extend([
            (
                f"  seed_macro_kind={evidence_rule.seed_macro_kind} "
                f"base_cell_count={evidence_rule.base_cell_count} "
                f"candidate_cell_count={evidence_rule.candidate_cell_count} "
                f"template_match_count={evidence_rule.template_match_count} "
                f"verified_template_match_count={evidence_rule.verified_template_match_count} "
                f"coverage_ratio={evidence_rule.coverage_ratio} "
                f"piece_count={evidence_rule.piece_count} "
                f"composition_piece_count={evidence_rule.composition_piece_count} "
                f"verified_piece_count={evidence_rule.verified_piece_count} "
                f"weak_piece_count={evidence_rule.weak_piece_count} "
                f"verified_piece_ratio={evidence_rule.verified_piece_ratio}"
            ),
            f"    line_equations={[equation.equation for equation in evidence_rule.line_equations]}",
            f"    covered_region_signatures={[list(signature) for signature in evidence_rule.covered_region_signatures]}",
            f"    uncovered_region_signatures={[list(signature) for signature in evidence_rule.uncovered_region_signatures]}",
            f"    verification_max_source_depth={evidence_rule.verification_max_source_depth}",
            f"    example_roots={list(evidence_rule.example_roots)}",
            f"    example_subsets={[list(subset) for subset in evidence_rule.example_subsets]}",
        ])
        for piece in evidence_rule.child_pieces:
            lines.extend([
                (
                    f"    piece_kind={piece.piece_kind} "
                    f"macro_kind={piece.macro_kind} "
                    f"cell_count={piece.cell_count} "
                    f"occurrence_count={piece.occurrence_count} "
                    f"verified_occurrence_count={piece.verified_occurrence_count}"
                ),
                f"      component_region_signatures={[list(signature) for signature in piece.component_region_signatures]}",
                f"      marked_cells={dict(piece.marked_cell_signature)}",
            ])
    return "\n".join(lines)


