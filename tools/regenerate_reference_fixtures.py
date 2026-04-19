from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias, cast


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.reference_verification.fixtures import (
    _CANONICAL_REFERENCE_FIXTURE_PATH,
    _LOCAL_REFERENCE_FIXTURE_PATH,
    _canonical_patch_payload,
    _cell_local_reference_payload,
)
from backend.simulation.reference_verification.observation import _build_reference_topology
from backend.simulation.reference_verification.types import (
    _CanonicalPatchFixturePayload,
    _LocalReferenceAnchorPayload,
)


FixtureMode = Literal["local", "canonical", "both"]
LocalFixturePayload: TypeAlias = dict[str, dict[str, dict[str, _LocalReferenceAnchorPayload]]]
CanonicalFixturePayload: TypeAlias = dict[str, dict[str, _CanonicalPatchFixturePayload]]


@dataclass(frozen=True)
class LocalFixtureTarget:
    geometry: str
    depth: int
    anchor_ids: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalFixtureTarget:
    geometry: str
    depth: int
    fixture_key: str
    include_id: bool


class FixtureRegenerationError(ValueError):
    pass


def _read_local_fixtures(path: Path = _LOCAL_REFERENCE_FIXTURE_PATH) -> LocalFixturePayload:
    return cast(LocalFixturePayload, json.loads(path.read_text(encoding="utf-8")))


def _read_canonical_fixtures(
    path: Path = _CANONICAL_REFERENCE_FIXTURE_PATH,
) -> CanonicalFixturePayload:
    return cast(CanonicalFixturePayload, json.loads(path.read_text(encoding="utf-8")))


def _format_fixture_json(payload: LocalFixturePayload | CanonicalFixturePayload) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _write_fixture_json(
    path: Path,
    payload: LocalFixturePayload | CanonicalFixturePayload,
) -> None:
    path.write_text(_format_fixture_json(payload), encoding="utf-8")


def discover_local_fixture_targets(
    fixtures: LocalFixturePayload,
    *,
    geometry: str | None = None,
    depth: int | None = None,
) -> tuple[LocalFixtureTarget, ...]:
    targets: list[LocalFixtureTarget] = []
    for candidate_geometry, depths in sorted(fixtures.items()):
        if geometry is not None and candidate_geometry != geometry:
            continue
        for depth_key, anchors in sorted(depths.items(), key=lambda item: int(item[0])):
            candidate_depth = int(depth_key)
            if depth is not None and candidate_depth != depth:
                continue
            targets.append(
                LocalFixtureTarget(
                    geometry=candidate_geometry,
                    depth=candidate_depth,
                    anchor_ids=tuple(sorted(anchors)),
                )
            )
    return tuple(targets)


def discover_canonical_fixture_targets(
    fixtures: CanonicalFixturePayload,
    *,
    geometry: str | None = None,
    depth: int | None = None,
) -> tuple[CanonicalFixtureTarget, ...]:
    targets: list[CanonicalFixtureTarget] = []
    for candidate_geometry, spec in sorted(REFERENCE_FAMILY_SPECS.items()):
        if geometry is not None and candidate_geometry != geometry:
            continue
        for candidate_depth, expectation in sorted(spec.depth_expectations.items()):
            if depth is not None and candidate_depth != depth:
                continue
            fixture_key = expectation.canonical_patch_fixture_key
            if fixture_key is None:
                continue
            targets.append(
                CanonicalFixtureTarget(
                    geometry=candidate_geometry,
                    depth=candidate_depth,
                    fixture_key=fixture_key,
                    include_id=expectation.canonical_patch_include_id,
                )
            )
    return tuple(targets)


def regenerate_local_fixtures(
    fixtures: LocalFixturePayload,
    targets: tuple[LocalFixtureTarget, ...],
) -> LocalFixturePayload:
    regenerated = copy.deepcopy(fixtures)
    for target in targets:
        try:
            spec = REFERENCE_FAMILY_SPECS[target.geometry]
        except KeyError as error:
            raise FixtureRegenerationError(
                f"Unsupported reference fixture geometry {target.geometry!r}."
            ) from error
        topology = _build_reference_topology(spec, target.depth)
        depth_payload: dict[str, _LocalReferenceAnchorPayload] = {}
        for anchor_id in target.anchor_ids:
            anchor_payload = _cell_local_reference_payload(topology, anchor_id)
            if anchor_payload is None:
                raise FixtureRegenerationError(
                    f"Missing local fixture anchor {target.geometry} depth {target.depth}: {anchor_id}."
                )
            depth_payload[anchor_id] = anchor_payload
        regenerated.setdefault(target.geometry, {})[str(target.depth)] = depth_payload
    return regenerated


def regenerate_canonical_fixtures(
    fixtures: CanonicalFixturePayload,
    targets: tuple[CanonicalFixtureTarget, ...],
) -> CanonicalFixturePayload:
    regenerated = copy.deepcopy(fixtures)
    for target in targets:
        try:
            spec = REFERENCE_FAMILY_SPECS[target.geometry]
        except KeyError as error:
            raise FixtureRegenerationError(
                f"Unsupported reference fixture geometry {target.geometry!r}."
            ) from error
        topology = _build_reference_topology(spec, target.depth)
        regenerated.setdefault(target.geometry, {})[target.fixture_key] = {
            "depth": target.depth,
            "include_id": target.include_id,
            "cells": _canonical_patch_payload(topology, include_id=target.include_id),
        }
    return regenerated


def _local_drift_lines(
    current: LocalFixturePayload,
    regenerated: LocalFixturePayload,
    targets: tuple[LocalFixtureTarget, ...],
) -> list[str]:
    drift: list[str] = []
    for target in targets:
        current_depth = current.get(target.geometry, {}).get(str(target.depth), {})
        regenerated_depth = regenerated.get(target.geometry, {}).get(str(target.depth), {})
        for anchor_id in target.anchor_ids:
            if current_depth.get(anchor_id) != regenerated_depth.get(anchor_id):
                drift.append(f"local {target.geometry} depth {target.depth} anchor {anchor_id}")
    return drift


def _canonical_drift_lines(
    current: CanonicalFixturePayload,
    regenerated: CanonicalFixturePayload,
    targets: tuple[CanonicalFixtureTarget, ...],
) -> list[str]:
    drift: list[str] = []
    for target in targets:
        current_fixture = current.get(target.geometry, {}).get(target.fixture_key)
        regenerated_fixture = regenerated.get(target.geometry, {}).get(target.fixture_key)
        if current_fixture != regenerated_fixture:
            drift.append(
                f"canonical {target.geometry} depth {target.depth} fixture {target.fixture_key}"
            )
    return drift


def selected_modes(mode: FixtureMode) -> tuple[Literal["local", "canonical"], ...]:
    if mode == "both":
        return ("local", "canonical")
    return (mode,)


def build_regenerated_fixture_payloads(
    *,
    mode: FixtureMode,
    all_targets: bool,
    geometry: str | None,
    depth: int | None,
) -> tuple[
    LocalFixturePayload | None,
    CanonicalFixturePayload | None,
    tuple[LocalFixtureTarget, ...],
    tuple[CanonicalFixtureTarget, ...],
]:
    if all_targets and (geometry is not None or depth is not None):
        raise FixtureRegenerationError("--all cannot be combined with --geometry or --depth.")
    if not all_targets and (geometry is None or depth is None):
        raise FixtureRegenerationError("Pass --all or pass both --geometry and --depth.")

    local_fixtures = _read_local_fixtures()
    canonical_fixtures = _read_canonical_fixtures()
    local_targets: tuple[LocalFixtureTarget, ...] = ()
    canonical_targets: tuple[CanonicalFixtureTarget, ...] = ()
    regenerated_local: LocalFixturePayload | None = None
    regenerated_canonical: CanonicalFixturePayload | None = None

    if "local" in selected_modes(mode):
        local_targets = discover_local_fixture_targets(
            local_fixtures,
            geometry=None if all_targets else geometry,
            depth=None if all_targets else depth,
        )
        if not local_targets:
            raise FixtureRegenerationError("No local fixture targets matched the request.")
        regenerated_local = regenerate_local_fixtures(local_fixtures, local_targets)

    if "canonical" in selected_modes(mode):
        canonical_targets = discover_canonical_fixture_targets(
            canonical_fixtures,
            geometry=None if all_targets else geometry,
            depth=None if all_targets else depth,
        )
        if not canonical_targets:
            raise FixtureRegenerationError("No canonical fixture targets matched the request.")
        regenerated_canonical = regenerate_canonical_fixtures(
            canonical_fixtures,
            canonical_targets,
        )

    return regenerated_local, regenerated_canonical, local_targets, canonical_targets


def check_fixture_drift(
    *,
    mode: FixtureMode,
    all_targets: bool,
    geometry: str | None,
    depth: int | None,
) -> list[str]:
    local_fixtures = _read_local_fixtures()
    canonical_fixtures = _read_canonical_fixtures()
    regenerated_local, regenerated_canonical, local_targets, canonical_targets = (
        build_regenerated_fixture_payloads(
            mode=mode,
            all_targets=all_targets,
            geometry=geometry,
            depth=depth,
        )
    )
    drift: list[str] = []
    if regenerated_local is not None:
        drift.extend(_local_drift_lines(local_fixtures, regenerated_local, local_targets))
    if regenerated_canonical is not None:
        drift.extend(
            _canonical_drift_lines(canonical_fixtures, regenerated_canonical, canonical_targets)
        )
    return drift


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate checked-in literature reference fixture JSON.",
    )
    parser.add_argument("--mode", choices=("local", "canonical", "both"), required=True)
    parser.add_argument("--all", action="store_true", dest="all_targets")
    parser.add_argument("--geometry")
    parser.add_argument("--depth", type=int)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    mode = cast(FixtureMode, args.mode)
    try:
        if args.check:
            drift = check_fixture_drift(
                mode=mode,
                all_targets=bool(args.all_targets),
                geometry=cast(str | None, args.geometry),
                depth=cast(int | None, args.depth),
            )
            if drift:
                print("Reference fixture drift detected:")
                for line in drift:
                    print(f"  {line}")
                return 1
            print("Reference fixtures are up to date.")
            return 0

        regenerated_local, regenerated_canonical, local_targets, canonical_targets = (
            build_regenerated_fixture_payloads(
                mode=mode,
                all_targets=bool(args.all_targets),
                geometry=cast(str | None, args.geometry),
                depth=cast(int | None, args.depth),
            )
        )
        if regenerated_local is not None:
            _write_fixture_json(_LOCAL_REFERENCE_FIXTURE_PATH, regenerated_local)
            print(f"Regenerated {len(local_targets)} local fixture target(s).")
        if regenerated_canonical is not None:
            _write_fixture_json(_CANONICAL_REFERENCE_FIXTURE_PATH, regenerated_canonical)
            print(f"Regenerated {len(canonical_targets)} canonical fixture target(s).")
        return 0
    except FixtureRegenerationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
