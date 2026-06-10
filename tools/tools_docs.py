from __future__ import annotations

import argparse
from pathlib import Path

from tools._common import ROOT_DIR
from tools.command_docs import COMMANDS, GROUPS

TOOLS_DOC_PATH = ROOT_DIR / "docs" / "TOOLS.md"


def render_tools_reference() -> str:
    lines: list[str] = []
    lines.append("# Tools Reference")
    lines.append("")
    lines.append(
        "Generated from the `python -m tools ...` command registry. Edit the CLI metadata, not this file by hand."
    )
    lines.append("")
    lines.append(
        "For npm convenience aliases, see the `scripts` block in [package.json](../package.json)."
    )
    lines.append("")
    for group in GROUPS:
        lines.append(f"## {group.title}")
        lines.append("")
        lines.append(group.intro)
        lines.append("")
        group_commands = [command for command in COMMANDS if command.group == group.key]
        for command in group_commands:
            lines.append(f"### `{command.label}`")
            lines.append("")
            lines.append(command.summary)
            lines.append("")
            lines.append(command.details)
            lines.append("")
            lines.append("```powershell")
            for example in command.examples:
                lines.append(example)
            lines.append("```")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools repo tools-docs",
        description="Generate or check docs/TOOLS.md from the tools CLI registry.",
    )
    parser.add_argument(
        "--check", action="store_true", help="Fail if docs/TOOLS.md is out of date."
    )
    parser.add_argument(
        "--write", action="store_true", help="Write the generated reference back to docs/TOOLS.md."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to stdout unless --write is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    rendered = render_tools_reference()
    target_path = args.output
    if args.write:
        target_path = TOOLS_DOC_PATH
    if args.check:
        current = TOOLS_DOC_PATH.read_text(encoding="utf-8")
        if current != rendered:
            print("docs/TOOLS.md is out of date.")
            return 1
        print("docs/TOOLS.md is up to date.")
        return 0
    if target_path is not None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(rendered, encoding="utf-8")
        return 0
    print(rendered, end="")
    return 0
