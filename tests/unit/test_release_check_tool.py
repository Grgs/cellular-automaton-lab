from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from tools.release_check import CheckResult, _check_version_shape, collect_checks


def _completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["mock"], returncode, stdout=stdout, stderr="")


class ReleaseCheckToolTests(unittest.TestCase):
    def test_pre_publish_passes_when_docs_are_ready_and_release_is_absent(self) -> None:
        def git_output(*args: str) -> str | None:
            values = {
                ("status", "--porcelain"): "",
                ("branch", "--show-current"): "main",
                ("rev-parse", "HEAD"): "abc123",
                ("rev-parse", "origin/main"): "abc123",
                ("tag", "--list", "v0.4.0"): "",
            }
            return values.get(args)

        with (
            patch("tools.release_check._git_output", side_effect=git_output),
            patch("tools.release_check._run_command", return_value=_completed()),
            patch("tools.release_check._gh_json", return_value=None),
        ):
            checks = collect_checks("v0.4.0", phase="pre-publish", target_branch="main")

        self.assertTrue(all(check.ok for check in checks), checks)

    def test_post_publish_fails_when_github_release_is_not_latest(self) -> None:
        def git_output(*args: str) -> str | None:
            values = {
                ("status", "--porcelain"): "",
                ("branch", "--show-current"): "main",
                ("rev-parse", "HEAD"): "abc123",
                ("rev-parse", "origin/main"): "abc123",
                ("tag", "--list", "v0.4.0"): "v0.4.0",
                ("rev-list", "-n", "1", "v0.4.0"): "abc123",
            }
            return values.get(args)

        def gh_json(*args: str) -> dict[str, object] | None:
            if args[:3] == ("release", "view", "v0.4.0"):
                return {
                    "tagName": "v0.4.0",
                    "name": "v0.4.0",
                    "isDraft": False,
                    "isPrerelease": False,
                    "url": "https://example.test/releases/v0.4.0",
                    "publishedAt": "2026-05-27T20:07:55Z",
                }
            if args[:2] == ("release", "view"):
                return {
                    "tagName": "v0.3.0",
                    "url": "https://example.test/releases/v0.3.0",
                }
            return None

        with (
            patch("tools.release_check._git_output", side_effect=git_output),
            patch(
                "tools.release_check._run_command", return_value=_completed("abc refs/tags/v0.4.0")
            ),
            patch("tools.release_check._gh_json", side_effect=gh_json),
        ):
            checks = collect_checks("v0.4.0", phase="post-publish", target_branch="main")

        latest_check = next(check for check in checks if check.name == "latest release")
        self.assertFalse(latest_check.ok)
        self.assertIn("v0.3.0", latest_check.detail)

    def test_post_publish_fails_when_tag_does_not_point_at_target_branch(self) -> None:
        def git_output(*args: str) -> str | None:
            values = {
                ("status", "--porcelain"): "",
                ("branch", "--show-current"): "main",
                ("rev-parse", "HEAD"): "def456",
                ("rev-parse", "origin/main"): "def456",
                ("tag", "--list", "v0.4.0"): "v0.4.0",
                ("rev-list", "-n", "1", "v0.4.0"): "abc123",
            }
            return values.get(args)

        def gh_json(*args: str) -> dict[str, object] | None:
            if args[:3] == ("release", "view", "v0.4.0"):
                return {
                    "tagName": "v0.4.0",
                    "name": "v0.4.0",
                    "isDraft": False,
                    "isPrerelease": False,
                    "url": "https://example.test/releases/v0.4.0",
                    "publishedAt": "2026-05-27T20:07:55Z",
                }
            if args[:2] == ("release", "view"):
                return {
                    "tagName": "v0.4.0",
                    "url": "https://example.test/releases/v0.4.0",
                }
            return None

        with (
            patch("tools.release_check._git_output", side_effect=git_output),
            patch(
                "tools.release_check._run_command",
                return_value=_completed("abc refs/tags/v0.4.0"),
            ),
            patch("tools.release_check._gh_json", side_effect=gh_json),
        ):
            checks = collect_checks("v0.4.0", phase="post-publish", target_branch="main")

        tag_target_check = next(check for check in checks if check.name == "tag target")
        self.assertFalse(tag_target_check.ok)
        self.assertIn("does not point at", tag_target_check.detail)

    def test_invalid_version_shape_fails(self) -> None:
        version_check = _check_version_shape("0.4")
        self.assertIsInstance(version_check, CheckResult)
        self.assertFalse(version_check.ok)


if __name__ == "__main__":
    unittest.main()
