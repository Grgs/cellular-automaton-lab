from __future__ import annotations

import unittest

from tools.dead_code_audit import (
    Finding,
    SourceFacts,
    classify_findings,
    parse_vulture_output,
    suppression_reason,
)


def _finding(
    *,
    path: str = "backend/example.py",
    line: int = 10,
    kind: str = "function",
    name: str = "unused_helper",
) -> Finding:
    raw = f"{path}:{line}: unused {kind} '{name}' (60% confidence)"
    return Finding(path=path, line=line, kind=kind, name=name, raw=raw)


class DeadCodeAuditTests(unittest.TestCase):
    def test_parse_vulture_output_preserves_actionable_location(self) -> None:
        finding = parse_vulture_output(
            "backend/example.py:17: unused function 'unused_helper' (60% confidence)\n"
        )
        self.assertEqual(
            finding,
            [_finding(line=17)],
        )

    def test_typed_dict_members_are_suppressed_by_source_location(self) -> None:
        finding = _finding(line=12, kind="variable", name="payload_key")
        facts = SourceFacts(
            typed_dict_members=frozenset({("backend/example.py", 12)}),
            protocol_parameters=frozenset(),
            string_literals=frozenset(),
        )
        self.assertIn("TypedDict", suppression_reason(finding, facts) or "")

    def test_protocol_parameters_are_suppressed_by_source_location(self) -> None:
        finding = _finding(line=15, kind="variable", name="message")
        facts = SourceFacts(
            typed_dict_members=frozenset(),
            protocol_parameters=frozenset({("backend/example.py", 15)}),
            string_literals=frozenset(),
        )
        self.assertIn("Protocol", suppression_reason(finding, facts) or "")

    def test_string_resolved_class_is_suppressed(self) -> None:
        finding = _finding(kind="class", name="GeneratedPayload")
        facts = SourceFacts(
            typed_dict_members=frozenset(),
            protocol_parameters=frozenset(),
            string_literals=frozenset({"GeneratedPayload"}),
        )
        self.assertIn("string-based", suppression_reason(finding, facts) or "")

    def test_ordinary_definition_remains_actionable(self) -> None:
        finding = _finding()
        facts = SourceFacts(
            typed_dict_members=frozenset(),
            protocol_parameters=frozenset(),
            string_literals=frozenset(),
        )
        actionable, suppressed = classify_findings([finding], facts)
        self.assertEqual(actionable, [finding])
        self.assertEqual(suppressed, [])


if __name__ == "__main__":
    unittest.main()
