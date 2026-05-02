"""Validate internal Markdown links and anchors across the repo.

The repo has ~17 Markdown files cross-referencing each other (and
``docs/TOOLS.md`` alone has ~50 link targets), so broken paths and
broken heading anchors accumulate quickly without a gate. This tool
walks every tracked Markdown file, extracts internal links (skipping
``http(s)://`` and ``mailto:`` schemes), and asserts:

1. Every linked path resolves to an existing file or directory.
2. Every ``#anchor`` resolves to a heading the target file actually
   declares (using the GitHub heading-slug rules).
3. Every reference-style ``[text][ref]`` link has a matching
   ``[ref]: ...`` definition somewhere in the file.

Exits non-zero on any violation. External URLs are intentionally not
checked (network-flaky and out of scope for this gate).

Examples:

    py -3 tools/check_doc_links.py
    py -3 tools/check_doc_links.py --format json
    py -3 tools/check_doc_links.py docs/TOOLS.md README.md
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]

# Directories whose contents are never scanned, even when they contain .md files.
# `.claude/worktrees/` holds independent git worktrees with their own (often
# diverged) docs; scanning them would surface noise from sibling branches.
_SKIP_DIR_PARTS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".venv",
        ".claude",
        ".codex",
        "node_modules",
        "output",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
    }
)

# URL schemes that are skipped: external link liveness is out of scope.
_EXTERNAL_SCHEME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

# Inline link: [text](target) or [text](target "title"). Matches the *first*
# closing paren that does not appear inside balanced parentheses or quotes.
_INLINE_LINK_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    (?<!\\)               # not escaped
    \[(?P<text>(?:[^\[\]\\]|\\.)*)\]   # link text
    \(
      (?P<target>
        (?:
            <[^>]*>           # angle-bracket form: <https://...>
          | [^()\s]+(?:\([^()]*\))?  # plain target, allow one nested paren pair
        )
      )
      (?:\s+"[^"]*")?         # optional title
    \)
    """,
    re.VERBOSE,
)

# Reference-style link: [text][ref] or [text][] (collapsed). The collapsed form
# uses the link text as the reference.
_REFERENCE_LINK_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<!\\)\[(?P<text>(?:[^\[\]\\]|\\.)+)\]\[(?P<ref>(?:[^\[\]\\]|\\.)*)\]"
)

# Reference-link definition: [ref]: target "title"
_REFERENCE_DEF_RE: Final[re.Pattern[str]] = re.compile(
    r"""^\s*\[(?P<ref>[^\]]+)\]:\s*
        (?P<target>\S+)
        (?:\s+"[^"]*")?\s*$
    """,
    re.VERBOSE,
)

# Markdown headings: # text, ## text, ... up to ###### text.
_HEADING_RE: Final[re.Pattern[str]] = re.compile(r"^(#{1,6})\s+(?P<title>.+?)\s*#*\s*$")

# Explicit anchors: <a id="..."> or <a name="...">.
_HTML_ANCHOR_RE: Final[re.Pattern[str]] = re.compile(
    r"""<a\s+(?:id|name)\s*=\s*["'](?P<anchor>[^"']+)["']""", re.IGNORECASE
)


@dataclass(frozen=True)
class LinkViolation:
    file: str
    line: int
    target: str
    reason: str


@dataclass
class _ParsedFile:
    headings: list[str] = field(default_factory=list)
    """GitHub-slug forms of every heading in the file."""

    explicit_anchors: list[str] = field(default_factory=list)
    """Anchors declared via inline HTML."""

    reference_definitions: dict[str, str] = field(default_factory=dict)
    """Lowercased reference name -> target string."""

    @property
    def all_anchors(self) -> set[str]:
        return set(self.headings) | set(self.explicit_anchors)


def _strip_code_blocks(text: str) -> str:
    """Replace fenced code blocks with blank lines so link regexes don't match them.

    Preserves line numbering so we can still report line numbers for any violations
    found in the surviving prose. Indented code blocks (4+ space prefix) are not
    stripped because they are visually indistinguishable from list continuations
    in GitHub-flavored Markdown without a full parser, and most of the repo uses
    fenced blocks anyway.
    """
    lines = text.splitlines()
    out: list[str] = []
    fence: str | None = None
    for line in lines:
        stripped = line.lstrip()
        if fence is None:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = stripped[:3]
                out.append("")
                continue
            out.append(line)
            continue
        # Inside a fenced block: look for the matching closing fence.
        if stripped.startswith(fence):
            fence = None
        out.append("")
    return "\n".join(out)


_SLUG_PUNCT_RE: Final[re.Pattern[str]] = re.compile(r"[^\w\- ]+", re.UNICODE)


def github_slug(heading: str) -> str:
    """Approximate GitHub's heading-to-anchor slug rules.

    The rules in practice:
    1. Strip leading/trailing whitespace and trailing closing-hash markers.
    2. Lowercase.
    3. Drop emoji and most punctuation; keep word characters, hyphens, underscores.
    4. Replace runs of whitespace with single hyphens.
    """
    cleaned = heading.strip()
    cleaned = re.sub(r"#+\s*$", "", cleaned)
    cleaned = cleaned.lower()
    # Strip backticks first so `code` headings normalise to ``code``.
    cleaned = cleaned.replace("`", "")
    cleaned = _SLUG_PUNCT_RE.sub("", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned.strip("-")


def parse_markdown(text: str) -> _ParsedFile:
    """Extract headings, explicit anchors, and reference-link definitions."""
    parsed = _ParsedFile()
    in_fence = False
    fence: str | None = None
    for raw_line in text.splitlines():
        stripped = raw_line.lstrip()
        if in_fence:
            if fence is not None and stripped.startswith(fence):
                in_fence = False
                fence = None
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = True
            fence = stripped[:3]
            continue
        heading_match = _HEADING_RE.match(raw_line.strip())
        if heading_match is not None:
            parsed.headings.append(github_slug(heading_match.group("title")))
            continue
        for anchor_match in _HTML_ANCHOR_RE.finditer(raw_line):
            parsed.explicit_anchors.append(anchor_match.group("anchor"))
        ref_match = _REFERENCE_DEF_RE.match(raw_line)
        if ref_match is not None:
            parsed.reference_definitions[ref_match.group("ref").strip().lower()] = ref_match.group(
                "target"
            )
    return parsed


def _normalise_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target


def _split_target(target: str) -> tuple[str, str | None]:
    if target.startswith("#"):
        return "", target[1:]
    if "#" in target:
        path, _, anchor = target.partition("#")
        return path, anchor
    return target, None


def _is_external(target: str) -> bool:
    return bool(_EXTERNAL_SCHEME_RE.match(target))


def _resolve_target_path(file_path: Path, target_path: str) -> Path:
    if target_path.startswith("/"):
        # Treat absolute paths as repo-rooted, following the convention used in
        # the repo's docs.
        return ROOT_DIR / target_path.lstrip("/")
    return (file_path.parent / target_path).resolve()


def _line_index_to_line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _display_path(file_path: Path, root_dir: Path) -> str:
    try:
        return file_path.relative_to(root_dir).as_posix()
    except ValueError:
        # Path is outside the repo root (e.g. an ad-hoc absolute argument);
        # fall back to the absolute path so the report is still actionable.
        return file_path.as_posix()


def check_file(
    file_path: Path,
    *,
    parsed_cache: dict[Path, _ParsedFile],
    root_dir: Path,
) -> list[LinkViolation]:
    """Validate every internal link in `file_path`."""
    relative_path = _display_path(file_path, root_dir)
    # Tolerate UTF-8 BOMs that Windows editors sometimes prepend.
    text = file_path.read_text(encoding="utf-8-sig")
    parsed = parsed_cache.setdefault(file_path, parse_markdown(text))
    scrubbed = _strip_code_blocks(text)
    violations: list[LinkViolation] = []

    used_references: set[str] = set()

    for match in _INLINE_LINK_RE.finditer(scrubbed):
        target = _normalise_target(match.group("target"))
        line_number = _line_index_to_line_number(scrubbed, match.start())
        violations.extend(
            _validate_target(
                relative_path,
                line_number,
                target,
                file_path=file_path,
                parsed_cache=parsed_cache,
                root_dir=root_dir,
                local_parsed=parsed,
            )
        )

    for match in _REFERENCE_LINK_RE.finditer(scrubbed):
        ref_name = (match.group("ref") or match.group("text")).strip().lower()
        if not ref_name:
            continue
        used_references.add(ref_name)
        line_number = _line_index_to_line_number(scrubbed, match.start())
        resolved_target = parsed.reference_definitions.get(ref_name)
        if resolved_target is None:
            violations.append(
                LinkViolation(
                    file=relative_path,
                    line=line_number,
                    target=f"[{ref_name}]",
                    reason="reference-style link with no matching [label]: definition",
                )
            )
            continue
        violations.extend(
            _validate_target(
                relative_path,
                line_number,
                _normalise_target(resolved_target),
                file_path=file_path,
                parsed_cache=parsed_cache,
                root_dir=root_dir,
                local_parsed=parsed,
            )
        )

    return violations


def _validate_target(
    relative_path: str,
    line_number: int,
    target: str,
    *,
    file_path: Path,
    parsed_cache: dict[Path, _ParsedFile],
    root_dir: Path,
    local_parsed: _ParsedFile,
) -> list[LinkViolation]:
    if not target:
        return [
            LinkViolation(
                file=relative_path,
                line=line_number,
                target="(empty)",
                reason="empty link target",
            )
        ]
    if _is_external(target):
        return []

    path_part, anchor = _split_target(target)
    if path_part:
        target_path = _resolve_target_path(file_path, path_part)
        if not target_path.exists():
            return [
                LinkViolation(
                    file=relative_path,
                    line=line_number,
                    target=target,
                    reason=f"target path does not exist: {path_part}",
                )
            ]
        if anchor is None:
            return []
        if not target_path.is_file():
            return [
                LinkViolation(
                    file=relative_path,
                    line=line_number,
                    target=target,
                    reason="anchor specified on a directory link",
                )
            ]
        if target_path.suffix.lower() != ".md":
            # Anchors in non-Markdown files (e.g. inside a Python or HTML source
            # browsed on GitHub) are not checked here; we trust the URL.
            return []
        target_parsed = parsed_cache.get(target_path)
        if target_parsed is None:
            target_parsed = parse_markdown(target_path.read_text(encoding="utf-8-sig"))
            parsed_cache[target_path] = target_parsed
        if anchor not in target_parsed.all_anchors:
            return [
                LinkViolation(
                    file=relative_path,
                    line=line_number,
                    target=target,
                    reason=(
                        f"anchor '#{anchor}' not found in {_display_path(target_path, root_dir)}"
                    ),
                )
            ]
        return []

    # Pure anchor: same-file reference.
    if anchor is None or anchor not in local_parsed.all_anchors:
        return [
            LinkViolation(
                file=relative_path,
                line=line_number,
                target=target,
                reason=f"anchor '#{anchor or ''}' not found in current file",
            )
        ]
    return []


def discover_markdown_files(root_dir: Path, explicit: Iterable[Path]) -> list[Path]:
    explicit_paths = [path.resolve() for path in explicit]
    if explicit_paths:
        return sorted({p for p in explicit_paths if p.exists() and p.suffix.lower() == ".md"})
    discovered: list[Path] = []
    for path in root_dir.rglob("*.md"):
        if any(part in _SKIP_DIR_PARTS for part in path.relative_to(root_dir).parts):
            continue
        discovered.append(path)
    return sorted(discovered)


def _format_summary(files: list[Path], violations: list[LinkViolation], root_dir: Path) -> str:
    lines: list[str] = []
    lines.append(f"Checked {len(files)} Markdown files.")
    if not violations:
        lines.append("No broken internal links or anchors.")
        return "\n".join(lines)
    by_file: dict[str, list[LinkViolation]] = {}
    for violation in violations:
        by_file.setdefault(violation.file, []).append(violation)
    lines.append(f"{len(violations)} broken link(s) across {len(by_file)} file(s):")
    for file in sorted(by_file):
        lines.append(f"\n  {file}")
        for violation in by_file[file]:
            lines.append(f"    line {violation.line}: {violation.target} -> {violation.reason}")
    _ = root_dir
    return "\n".join(lines)


def _to_serializable(violations: list[LinkViolation]) -> list[dict[str, object]]:
    return [
        {
            "file": v.file,
            "line": v.line,
            "target": v.target,
            "reason": v.reason,
        }
        for v in violations
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="optional explicit Markdown paths; defaults to a repo-wide scan",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="output format (default: summary)",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="exit 0 even when broken links are present",
    )
    args = parser.parse_args(argv)

    files = discover_markdown_files(ROOT_DIR, args.paths)
    parsed_cache: dict[Path, _ParsedFile] = {}
    violations: list[LinkViolation] = []
    for file_path in files:
        violations.extend(check_file(file_path, parsed_cache=parsed_cache, root_dir=ROOT_DIR))

    if args.format == "json":
        rendered = json.dumps(
            {
                "files_checked": len(files),
                "violations": _to_serializable(violations),
            },
            indent=2,
            sort_keys=True,
        )
    else:
        rendered = _format_summary(files, violations, ROOT_DIR)

    print(rendered)
    if args.no_fail:
        return 0
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
