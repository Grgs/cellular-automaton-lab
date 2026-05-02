import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

try:
    from tools.run_supply_chain_audit import (
        EcosystemResult,
        Finding,
        _format_summary,
        _run_npm_audit,
        _run_pip_audit,
        _severity_at_or_above,
        _to_serializable,
        main,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.run_supply_chain_audit import (
        EcosystemResult,
        Finding,
        _format_summary,
        _run_npm_audit,
        _run_pip_audit,
        _severity_at_or_above,
        _to_serializable,
        main,
    )


class SeverityRankingTests(unittest.TestCase):
    def test_known_severities_are_compared_by_index(self) -> None:
        self.assertTrue(_severity_at_or_above("critical", "high"))
        self.assertTrue(_severity_at_or_above("high", "high"))
        self.assertFalse(_severity_at_or_above("moderate", "high"))
        self.assertFalse(_severity_at_or_above("low", "moderate"))

    def test_unknown_severities_escalate_to_high(self) -> None:
        # Unrated pip-audit findings must not be silently dropped: they should
        # block at the default "high" threshold.
        self.assertTrue(_severity_at_or_above("unrated", "high"))
        self.assertFalse(_severity_at_or_above("unrated", "critical"))


class PipAuditParsingTests(unittest.TestCase):
    def _stub_completed(self, stdout: str, returncode: int = 1) -> mock.MagicMock:
        completed = mock.MagicMock()
        completed.stdout = stdout
        completed.stderr = ""
        completed.returncode = returncode
        return completed

    def test_pip_audit_parses_object_shape(self) -> None:
        payload = (
            '{"dependencies": [{"name": "flask", "version": "3.1.0", '
            '"vulns": [{"id": "PYSEC-1", "fix_versions": ["3.1.1"], '
            '"aliases": ["CVE-2025-1"], "description": "demo"}]}]}'
        )
        with (
            mock.patch("tools.run_supply_chain_audit.subprocess.run") as run,
            mock.patch.dict(sys.modules, {"pip_audit": mock.MagicMock()}),
        ):
            run.return_value = self._stub_completed(payload, returncode=1)
            result = _run_pip_audit(frozenset())
        self.assertEqual(result.error, None)
        self.assertEqual(len(result.findings), 1)
        finding = result.findings[0]
        self.assertEqual(finding.package, "flask")
        self.assertEqual(finding.installed_version, "3.1.0")
        self.assertEqual(finding.vuln_id, "PYSEC-1")
        self.assertEqual(finding.fix_versions, ("3.1.1",))

    def test_pip_audit_parses_top_level_list_shape(self) -> None:
        payload = (
            '[{"name": "pillow", "version": "11.2.1", '
            '"vulns": [{"id": "PYSEC-99", "fix_versions": [], "aliases": [], '
            '"description": ""}]}]'
        )
        with (
            mock.patch("tools.run_supply_chain_audit.subprocess.run") as run,
            mock.patch.dict(sys.modules, {"pip_audit": mock.MagicMock()}),
        ):
            run.return_value = self._stub_completed(payload, returncode=1)
            result = _run_pip_audit(frozenset())
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].fix_versions, ())

    def test_pip_audit_skipped_when_module_missing(self) -> None:
        with mock.patch.dict(sys.modules, {"pip_audit": None}):
            result = _run_pip_audit(frozenset())
        self.assertIsNotNone(result.skipped_reason)
        self.assertEqual(result.findings, [])

    def test_pip_audit_unexpected_exit_code_records_error(self) -> None:
        with (
            mock.patch("tools.run_supply_chain_audit.subprocess.run") as run,
            mock.patch.dict(sys.modules, {"pip_audit": mock.MagicMock()}),
        ):
            run.return_value = self._stub_completed("", returncode=2)
            result = _run_pip_audit(frozenset())
        self.assertIsNotNone(result.error)
        self.assertEqual(result.findings, [])

    def test_pip_audit_ignore_filter_drops_matching_id(self) -> None:
        payload = (
            '{"dependencies": [{"name": "flask", "version": "3.1.0", '
            '"vulns": [{"id": "PYSEC-1", "fix_versions": ["3.1.1"], '
            '"aliases": [], "description": "demo"}]}]}'
        )
        with (
            mock.patch("tools.run_supply_chain_audit.subprocess.run") as run,
            mock.patch.dict(sys.modules, {"pip_audit": mock.MagicMock()}),
        ):
            run.return_value = self._stub_completed(payload, returncode=1)
            result = _run_pip_audit(frozenset({"PYSEC-1"}))
        self.assertEqual(result.findings, [])


class NpmAuditParsingTests(unittest.TestCase):
    def _stub_completed(self, stdout: str, returncode: int = 1) -> mock.MagicMock:
        completed = mock.MagicMock()
        completed.stdout = stdout
        completed.stderr = ""
        completed.returncode = returncode
        return completed

    def test_npm_audit_parses_vulnerabilities_block(self) -> None:
        payload = (
            '{"vulnerabilities": {"vite": {"severity": "high", '
            '"via": [{"title": "Path traversal", '
            '"url": "https://github.com/advisories/GHSA-4w7w-66w2-5vf9", '
            '"range": ">=8.0.0 <=8.0.4"}], '
            '"fixAvailable": {"version": "8.1.0"}}}}'
        )
        with (
            mock.patch("tools.run_supply_chain_audit.shutil.which") as which,
            mock.patch("tools.run_supply_chain_audit.subprocess.run") as run,
            mock.patch.object(Path, "exists", return_value=True),
        ):
            which.return_value = "/usr/bin/npm"
            run.return_value = self._stub_completed(payload)
            result = _run_npm_audit()
        self.assertEqual(result.error, None)
        self.assertEqual(len(result.findings), 1)
        finding = result.findings[0]
        self.assertEqual(finding.package, "vite")
        self.assertEqual(finding.severity, "high")
        self.assertEqual(finding.fix_versions, ("8.1.0",))
        self.assertIn("Path traversal", finding.description)

    def test_npm_audit_handles_empty_vulnerabilities(self) -> None:
        with (
            mock.patch("tools.run_supply_chain_audit.shutil.which") as which,
            mock.patch("tools.run_supply_chain_audit.subprocess.run") as run,
            mock.patch.object(Path, "exists", return_value=True),
        ):
            which.return_value = "/usr/bin/npm"
            run.return_value = self._stub_completed('{"vulnerabilities": {}}', returncode=0)
            result = _run_npm_audit()
        self.assertEqual(result.findings, [])

    def test_npm_audit_skipped_when_npm_missing(self) -> None:
        with mock.patch("tools.run_supply_chain_audit.shutil.which", return_value=None):
            result = _run_npm_audit()
        self.assertIsNotNone(result.skipped_reason)


class FormattingTests(unittest.TestCase):
    def _result(self, *findings: Finding) -> EcosystemResult:
        result = EcosystemResult(ecosystem=findings[0].ecosystem if findings else "python")
        result.findings.extend(findings)
        return result

    def test_summary_separates_blocking_from_informational(self) -> None:
        results = [
            self._result(
                Finding("python", "demo", "1.0", "X-1", "high", ("1.1",), (), "blocker"),
                Finding("python", "demo", "1.0", "X-2", "low", (), (), "info only"),
            )
        ]
        rendered = _format_summary(results, "high")
        self.assertIn("1 blocking, 1 informational", rendered)
        self.assertIn("BLOCK", rendered)
        self.assertIn("info ", rendered)
        self.assertIn("Totals: 1 blocking", rendered)

    def test_summary_reports_skipped_ecosystems(self) -> None:
        result = EcosystemResult(ecosystem="npm")
        result.skipped_reason = "no package-lock.json"
        rendered = _format_summary([result], "high")
        self.assertIn("[npm] skipped", rendered)

    def test_serializable_marks_blocking_per_finding(self) -> None:
        results = [
            self._result(
                Finding("python", "demo", "1.0", "X-1", "high", (), (), ""),
                Finding("python", "demo", "1.0", "X-2", "low", (), (), ""),
            )
        ]
        payload = _to_serializable(results, "high")
        eco = payload["ecosystems"]
        assert isinstance(eco, list) and isinstance(eco[0], dict)
        findings = eco[0]["findings"]
        assert isinstance(findings, list)
        self.assertTrue(findings[0]["blocking"])
        self.assertFalse(findings[1]["blocking"])


class MainEntrypointTests(unittest.TestCase):
    def _run(
        self, argv: list[str], pip_result: EcosystemResult, npm_result: EcosystemResult
    ) -> int:
        buffer = io.StringIO()
        with (
            mock.patch("tools.run_supply_chain_audit._run_pip_audit", return_value=pip_result),
            mock.patch("tools.run_supply_chain_audit._run_npm_audit", return_value=npm_result),
            redirect_stdout(buffer),
        ):
            return main(argv)

    def test_main_returns_zero_when_no_findings(self) -> None:
        self.assertEqual(
            self._run([], EcosystemResult("python"), EcosystemResult("npm")),
            0,
        )

    def test_main_returns_one_when_blocking(self) -> None:
        blocking = EcosystemResult(ecosystem="python")
        blocking.findings.append(
            Finding("python", "demo", "1.0", "X-1", "high", (), (), ""),
        )
        self.assertEqual(self._run([], blocking, EcosystemResult("npm")), 1)

    def test_main_no_fail_overrides_blocking(self) -> None:
        blocking = EcosystemResult(ecosystem="python")
        blocking.findings.append(
            Finding("python", "demo", "1.0", "X-1", "critical", (), (), ""),
        )
        self.assertEqual(self._run(["--no-fail"], blocking, EcosystemResult("npm")), 0)

    def test_main_returns_two_on_tool_error(self) -> None:
        errored = EcosystemResult(ecosystem="python")
        errored.error = "boom"
        self.assertEqual(self._run([], errored, EcosystemResult("npm")), 2)


if __name__ == "__main__":
    unittest.main()
