from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RepoGuardConfigTests(unittest.TestCase):
    def test_fresh_bundle_guard_builds_before_measuring(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package["scripts"]

        self.assertEqual(
            scripts["check:bundle-size:fresh"],
            "npm run build:frontend:standalone && npm run check:bundle-size",
        )
        self.assertIn("npm run check:bundle-size:fresh", scripts["check:ci-local"])

    def test_pre_push_runs_the_fresh_bundle_guard(self) -> None:
        config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        _, hook = config.split("      - id: standalone-bundle-budget", maxsplit=1)
        hook = hook.split("\n      - id:", maxsplit=1)[0]

        self.assertIn("entry: npm run check:bundle-size:fresh", hook)
        self.assertIn("pass_filenames: false", hook)
        self.assertIn("stages: [pre-push, manual]", hook)

    def test_repository_managed_pre_push_dispatcher_is_tracked(self) -> None:
        dispatcher = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")

        self.assertIn("PRE_COMMIT_HOOK_TYPE=pre-push", dispatcher)
        self.assertIn('exec "$HOOK_DIR/pre-commit" "$@"', dispatcher)


if __name__ == "__main__":
    unittest.main()
