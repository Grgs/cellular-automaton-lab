import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

try:
    from tools.check_doc_links import (
        LinkViolation,
        _strip_code_blocks,
        check_file,
        discover_markdown_files,
        github_slug,
        main,
        parse_markdown,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.check_doc_links import (
        LinkViolation,
        _strip_code_blocks,
        check_file,
        discover_markdown_files,
        github_slug,
        main,
        parse_markdown,
    )


class GithubSlugTests(unittest.TestCase):
    def test_lowercases_and_hyphenates_words(self) -> None:
        self.assertEqual(github_slug("Hello World"), "hello-world")

    def test_strips_punctuation(self) -> None:
        self.assertEqual(github_slug("Hello, World!"), "hello-world")

    def test_collapses_internal_whitespace(self) -> None:
        self.assertEqual(github_slug("Hello   World"), "hello-world")

    def test_keeps_hyphens_and_underscores(self) -> None:
        self.assertEqual(github_slug("My_section-name"), "my_section-name")

    def test_drops_backticks_around_code(self) -> None:
        self.assertEqual(github_slug("`tools/foo.py`"), "toolsfoopy")

    def test_handles_trailing_hash_markers(self) -> None:
        self.assertEqual(github_slug("Title ####"), "title")


class StripCodeBlocksTests(unittest.TestCase):
    def test_fenced_block_links_are_ignored(self) -> None:
        text = "Outside [foo](#bar)\n```\n[inside](#nope)\n```\nAfter [baz](#qux)"
        scrubbed = _strip_code_blocks(text)
        self.assertNotIn("inside", scrubbed)
        self.assertIn("foo", scrubbed)
        self.assertIn("baz", scrubbed)

    def test_indented_lines_are_preserved(self) -> None:
        # Indented blocks are not stripped (see docstring); list-continuation
        # text under bullet points still needs its links checked. Fenced blocks
        # remain the standard way to opt out of link checking.
        text = "    [kept](#x)\nVisible [shown](#y)"
        scrubbed = _strip_code_blocks(text)
        self.assertIn("kept", scrubbed)
        self.assertIn("shown", scrubbed)

    def test_line_count_is_preserved(self) -> None:
        text = "a\n```\nb\n```\nc"
        self.assertEqual(text.count("\n"), _strip_code_blocks(text).count("\n"))


class ParseMarkdownTests(unittest.TestCase):
    def test_collects_headings_as_slugs(self) -> None:
        parsed = parse_markdown("# Hello\n## World\n### Code Section")
        self.assertEqual(parsed.headings, ["hello", "world", "code-section"])

    def test_collects_explicit_html_anchors(self) -> None:
        parsed = parse_markdown('Some text\n<a id="explicit-anchor"></a>\nMore text')
        self.assertIn("explicit-anchor", parsed.explicit_anchors)

    def test_collects_reference_definitions(self) -> None:
        parsed = parse_markdown("Refer to [target][ref]\n\n[ref]: ./somewhere.md")
        self.assertEqual(parsed.reference_definitions["ref"], "./somewhere.md")

    def test_skips_headings_inside_fenced_blocks(self) -> None:
        parsed = parse_markdown("# Real heading\n```\n# Not a heading\n```\n")
        self.assertEqual(parsed.headings, ["real-heading"])


class CheckFileTests(unittest.TestCase):
    def _write(self, root: Path, files: dict[str, str]) -> None:
        for relative, content in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def test_external_links_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, {"a.md": "[gh](https://github.com)\n[mail](mailto:foo@bar)"})
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(violations, [])

    def test_missing_target_path_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, {"a.md": "[broken](./does-not-exist.md)"})
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(len(violations), 1)
        self.assertIn("does-not-exist.md", violations[0].reason)

    def test_missing_anchor_in_other_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                {
                    "a.md": "[broken](./b.md#nope)",
                    "b.md": "# Real heading",
                },
            )
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(len(violations), 1)
        self.assertIn("anchor '#nope'", violations[0].reason)

    def test_present_anchor_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                {
                    "a.md": "[ok](./b.md#real-heading)",
                    "b.md": "# Real heading",
                },
            )
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(violations, [])

    def test_self_anchor_is_validated_against_local_headings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                {"a.md": "Jump to [there](#real)\n## Real"},
            )
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(violations, [])

    def test_reference_link_without_definition_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, {"a.md": "Look at [the spec][missing]"})
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(len(violations), 1)
        self.assertIn("reference-style link", violations[0].reason)

    def test_reference_link_with_definition_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                {
                    "a.md": "Look at [the spec][spec]\n\n[spec]: ./b.md",
                    "b.md": "# Other",
                },
            )
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(violations, [])

    def test_links_inside_code_blocks_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                {
                    "a.md": "Outside [ok](./b.md)\n```\nshell snippet [bogus](./missing.md)\n```",
                    "b.md": "# B",
                },
            )
            violations = check_file(root / "a.md", parsed_cache={}, root_dir=root)
        self.assertEqual(violations, [])


class DiscoverMarkdownFilesTests(unittest.TestCase):
    def test_skipped_directories_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "real.md").write_text("# r", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored.md").write_text("# i", encoding="utf-8")
            (root / ".claude").mkdir()
            (root / ".claude" / "stale.md").write_text("# s", encoding="utf-8")
            files = discover_markdown_files(root, [])
        names = {p.name for p in files}
        self.assertEqual(names, {"real.md"})

    def test_explicit_paths_override_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "specific.md"
            target.write_text("# x", encoding="utf-8")
            (root / "other.md").write_text("# y", encoding="utf-8")
            files = discover_markdown_files(root, [target])
        self.assertEqual(files, [target])


class MainEntrypointTests(unittest.TestCase):
    def _silence(self) -> io.StringIO:
        return io.StringIO()

    def test_main_returns_zero_when_no_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "doc.md"
            target.write_text("# Real\n[self](#real)\n", encoding="utf-8")
            buffer = self._silence()
            with redirect_stdout(buffer):
                rc = main([str(target)])
        self.assertEqual(rc, 0)
        self.assertIn("No broken", buffer.getvalue())

    def test_main_returns_one_when_violation_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "doc.md"
            target.write_text("[bad](./missing.md)\n", encoding="utf-8")
            buffer = self._silence()
            with redirect_stdout(buffer):
                rc = main([str(target)])
        self.assertEqual(rc, 1)
        self.assertIn("missing.md", buffer.getvalue())

    def test_main_no_fail_returns_zero_with_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "doc.md"
            target.write_text("[bad](./missing.md)\n", encoding="utf-8")
            buffer = self._silence()
            with redirect_stdout(buffer):
                rc = main([str(target), "--no-fail"])
        self.assertEqual(rc, 0)

    def test_main_emits_machine_readable_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "doc.md"
            target.write_text("[bad](./missing.md)\n", encoding="utf-8")
            buffer = self._silence()
            with redirect_stdout(buffer):
                rc = main(["--format", "json", str(target)])
        self.assertEqual(rc, 1)
        decoded = json.loads(buffer.getvalue())
        self.assertEqual(decoded["files_checked"], 1)
        self.assertEqual(len(decoded["violations"]), 1)


class ViolationDataclassTests(unittest.TestCase):
    def test_violation_is_a_value_type(self) -> None:
        a = LinkViolation(file="a.md", line=1, target="x", reason="r")
        b = LinkViolation(file="a.md", line=1, target="x", reason="r")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
