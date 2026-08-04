from __future__ import annotations

import argparse
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from backend.application_commands.contracts import (
    COMMAND_SPECS,
    TYPESCRIPT_TYPE_MODULES,
    CommandSpec,
)
from tools._common import ROOT_DIR, write_text_lf

APPLICATION_COMMAND_CONTRACT_PATH = ROOT_DIR / "frontend" / "application-command-contract.ts"
_TYPESCRIPT_TYPE_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9_]*\b")


def _referenced_types(specs: Sequence[CommandSpec]) -> set[str]:
    return {
        match.group(0)
        for spec in specs
        for expression in (spec.frontend_request, spec.frontend_result)
        for match in _TYPESCRIPT_TYPE_PATTERN.finditer(expression)
    }


def _render_imports(
    specs: Sequence[CommandSpec],
    type_modules: Mapping[str, str],
) -> list[str]:
    referenced_types = _referenced_types(specs)
    missing_types = sorted(referenced_types - type_modules.keys())
    if missing_types:
        raise ValueError(
            "Application command TypeScript types have no import module: "
            + ", ".join(missing_types)
        )

    module_order: list[str] = []
    for spec in specs:
        for expression in (spec.frontend_request, spec.frontend_result):
            for match in _TYPESCRIPT_TYPE_PATTERN.finditer(expression):
                module = type_modules[match.group(0)]
                if module not in module_order:
                    module_order.append(module)

    lines: list[str] = []
    for module in module_order:
        names = sorted(name for name in referenced_types if type_modules[name] == module)
        lines.append("import type {")
        lines.extend(f"    {name}," for name in names)
        lines.append(f'}} from "{module}";')
    return lines


def _render_command_entry(spec: CommandSpec) -> list[str]:
    prefix = f'    "{spec.command.value}": CommandContract<'
    compact = f"{prefix}{spec.frontend_request}, {spec.frontend_result}>;"
    if len(compact) <= 100:
        return [compact]
    return [
        f"{prefix}",
        f"        {spec.frontend_request},",
        f"        {spec.frontend_result}",
        "    >;",
    ]


def _request_payload_members(specs: Sequence[CommandSpec]) -> tuple[str, ...]:
    members: list[str] = []
    for spec in specs:
        for member in spec.frontend_request.split("|"):
            normalized = member.strip()
            if normalized != "undefined" and normalized not in members:
                members.append(normalized)
    return tuple(members)


def render_application_command_contract(
    specs: Sequence[CommandSpec] = COMMAND_SPECS,
    type_modules: Mapping[str, str] = TYPESCRIPT_TYPE_MODULES,
) -> str:
    lines = _render_imports(specs, type_modules)
    lines.extend(
        (
            "",
            "/**",
            " * Generated from backend/application_commands/contracts.py.",
            " * Regenerate with `python -m tools repo command-contract --write`.",
            " */",
            "interface CommandContract<TRequest, TResult> {",
            "    request: TRequest;",
            "    result: TResult;",
            "}",
            "",
            "export interface ApplicationCommandMap {",
        )
    )
    for spec in specs:
        lines.extend(_render_command_entry(spec))
    lines.extend(("}", "", "export interface ApplicationCommandPathMap {"))
    lines.extend(
        f'    "{spec.transport_path}": ApplicationCommandMap["{spec.command.value}"];'
        for spec in specs
    )
    lines.extend(("}", "", "export type StandaloneRequestPayload ="))
    request_members = _request_payload_members(specs)
    lines.extend(
        f"    | {member}{';' if index == len(request_members) - 1 else ''}"
        for index, member in enumerate(request_members)
    )
    lines.extend(
        (
            "",
            "export type ApplicationCommandId = keyof ApplicationCommandMap;",
            "export type ApplicationCommandPath = keyof ApplicationCommandPathMap;",
            "export type ApplicationCommandRequest<TCommand extends ApplicationCommandId> =",
            '    ApplicationCommandMap[TCommand]["request"];',
            "export type ApplicationCommandResult<TCommand extends ApplicationCommandId> =",
            '    ApplicationCommandMap[TCommand]["result"];',
            "",
        )
    )
    return "\n".join(lines)


def contract_is_current() -> bool:
    return (
        APPLICATION_COMMAND_CONTRACT_PATH.read_text(encoding="utf-8")
        == render_application_command_contract()
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or check the TypeScript application command contract.",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--check",
        action="store_true",
        help="Fail if frontend/application-command-contract.ts is out of date.",
    )
    action.add_argument(
        "--write",
        action="store_true",
        help="Write frontend/application-command-contract.ts from the Python registry.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to stdout unless --write is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rendered = render_application_command_contract()
    if args.check:
        if not contract_is_current():
            print(
                "frontend/application-command-contract.ts is out of date; run "
                "`python -m tools repo command-contract --write`."
            )
            return 1
        print("frontend/application-command-contract.ts is up to date.")
        return 0

    target_path = APPLICATION_COMMAND_CONTRACT_PATH if args.write else args.output
    if target_path is not None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(target_path, rendered)
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
