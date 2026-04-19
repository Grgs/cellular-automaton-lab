from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.topology import build_topology


DEFAULT_FIXTURE_MANIFEST_PATH = ROOT / "frontend" / "test-fixtures" / "topologies" / "fixture-manifest.json"


@dataclass(frozen=True)
class FrontendTopologyFixtureTarget:
    name: str
    path: Path
    family: str
    width: int
    height: int
    patch_depth: int | None
    cell_size: int
    topology_revision: str


class FrontendFixtureRegenerationError(ValueError):
    pass


def _format_fixture_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _read_manifest(manifest_path: Path = DEFAULT_FIXTURE_MANIFEST_PATH) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def _resolve_fixture_path(manifest_path: Path, relative_path: str) -> Path:
    candidate_path = Path(relative_path)
    if candidate_path.is_absolute():
        return candidate_path
    return (manifest_path.parent / candidate_path).resolve()


def _require_int(value: object, *, field_name: str, fixture_name: str) -> int:
    if not isinstance(value, int):
        raise FrontendFixtureRegenerationError(
            f"Fixture {fixture_name!r} is missing integer field {field_name!r}."
        )
    return int(value)


def load_fixture_targets(
    manifest_path: Path = DEFAULT_FIXTURE_MANIFEST_PATH,
) -> tuple[FrontendTopologyFixtureTarget, ...]:
    payload = _read_manifest(manifest_path)
    fixture_entries = payload.get("fixtures")
    if not isinstance(fixture_entries, list):
        raise FrontendFixtureRegenerationError("Fixture manifest is missing a 'fixtures' array.")

    targets: list[FrontendTopologyFixtureTarget] = []
    for fixture_entry in fixture_entries:
        if not isinstance(fixture_entry, dict):
            raise FrontendFixtureRegenerationError("Fixture manifest entries must be objects.")
        name = fixture_entry.get("name")
        relative_path = fixture_entry.get("path")
        family = fixture_entry.get("family")
        topology_revision = fixture_entry.get("topologyRevision")
        if not isinstance(name, str) or not name:
            raise FrontendFixtureRegenerationError("Fixture manifest entries must declare a non-empty name.")
        if not isinstance(relative_path, str) or not relative_path:
            raise FrontendFixtureRegenerationError(f"Fixture {name!r} is missing a non-empty path.")
        if not isinstance(family, str) or not family:
            raise FrontendFixtureRegenerationError(f"Fixture {name!r} is missing a non-empty family.")
        if not isinstance(topology_revision, str) or not topology_revision:
            raise FrontendFixtureRegenerationError(
                f"Fixture {name!r} is missing a non-empty topologyRevision."
            )
        patch_depth_value = fixture_entry.get("patchDepth")
        if patch_depth_value is not None and not isinstance(patch_depth_value, int):
            raise FrontendFixtureRegenerationError(
                f"Fixture {name!r} has a non-integer patchDepth."
            )
        targets.append(
            FrontendTopologyFixtureTarget(
                name=name,
                path=_resolve_fixture_path(manifest_path, relative_path),
                family=family,
                width=_require_int(fixture_entry.get("width"), field_name="width", fixture_name=name),
                height=_require_int(fixture_entry.get("height"), field_name="height", fixture_name=name),
                patch_depth=None if patch_depth_value is None else int(patch_depth_value),
                cell_size=_require_int(fixture_entry.get("cellSize"), field_name="cellSize", fixture_name=name),
                topology_revision=topology_revision,
            )
        )
    return tuple(targets)


def discover_fixture_targets(
    *,
    manifest_path: Path = DEFAULT_FIXTURE_MANIFEST_PATH,
    all_targets: bool,
    names: tuple[str, ...],
) -> tuple[FrontendTopologyFixtureTarget, ...]:
    if all_targets and names:
        raise FrontendFixtureRegenerationError("--all cannot be combined with --fixture.")
    if not all_targets and not names:
        raise FrontendFixtureRegenerationError("Pass --all or at least one --fixture name.")

    known_targets = load_fixture_targets(manifest_path)
    if all_targets:
        return known_targets

    target_by_name = {target.name: target for target in known_targets}
    selected_targets: list[FrontendTopologyFixtureTarget] = []
    for name in names:
        try:
            selected_targets.append(target_by_name[name])
        except KeyError as exc:
            available = ", ".join(sorted(target_by_name))
            raise FrontendFixtureRegenerationError(
                f"Unknown frontend topology fixture {name!r}. Available fixtures: {available}"
            ) from exc
    return tuple(selected_targets)


def regenerate_fixture_payload(
    target: FrontendTopologyFixtureTarget,
) -> dict[str, Any]:
    topology = build_topology(
        target.family,
        target.width,
        target.height,
        target.patch_depth,
    )
    topology_payload = json.loads(json.dumps(topology.to_dict()))
    topology_payload["topology_revision"] = target.topology_revision
    return {
        "geometry": target.family,
        "width": target.width,
        "height": target.height,
        "patchDepth": target.patch_depth,
        "cellSize": target.cell_size,
        "topology": topology_payload,
    }


def _read_existing_fixture(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def fixture_drift_lines(
    targets: tuple[FrontendTopologyFixtureTarget, ...],
) -> list[str]:
    drift: list[str] = []
    for target in targets:
        regenerated = regenerate_fixture_payload(target)
        current = _read_existing_fixture(target.path)
        if current != regenerated:
            drift.append(target.name)
    return drift


def write_regenerated_fixtures(
    targets: tuple[FrontendTopologyFixtureTarget, ...],
) -> None:
    for target in targets:
        target.path.parent.mkdir(parents=True, exist_ok=True)
        target.path.write_text(
            _format_fixture_json(regenerate_fixture_payload(target)),
            encoding="utf-8",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate checked-in frontend representative topology fixture JSON.",
    )
    parser.add_argument("--all", action="store_true", dest="all_targets")
    parser.add_argument(
        "--fixture",
        action="append",
        default=[],
        help="Fixture name from the frontend fixture manifest. May be repeated.",
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_FIXTURE_MANIFEST_PATH,
        help="Fixture manifest path. Defaults to the checked-in frontend fixture manifest.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        targets = discover_fixture_targets(
            manifest_path=Path(args.manifest),
            all_targets=bool(args.all_targets),
            names=tuple(str(name) for name in args.fixture),
        )
        if bool(args.check):
            drift = fixture_drift_lines(targets)
            if drift:
                print("Frontend topology fixture drift detected:")
                for name in drift:
                    print(f"  {name}")
                return 1
            print("Frontend topology fixtures are up to date.")
            return 0

        write_regenerated_fixtures(targets)
        print(f"Regenerated {len(targets)} frontend topology fixture(s).")
        for target in targets:
            print(f"  {target.name} -> {target.path}")
        return 0
    except FrontendFixtureRegenerationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
