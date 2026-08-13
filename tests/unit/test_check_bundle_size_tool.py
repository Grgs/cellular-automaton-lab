import gzip
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

try:
    from tools.check_bundle_size import (
        Budget,
        CategoryBudget,
        CategorySizes,
        TotalBudget,
        Violation,
        _classify,
        _format_bytes,
        _format_summary,
        _gzip_size,
        _load_baseline,
        _recalibrated_gzip_budget,
        _recalibrated_raw_budget,
        evaluate,
        load_budget,
        main,
        measure,
        recalibrate_budget,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.check_bundle_size import (
        Budget,
        CategoryBudget,
        CategorySizes,
        TotalBudget,
        Violation,
        _classify,
        _format_bytes,
        _format_summary,
        _gzip_size,
        _load_baseline,
        _recalibrated_gzip_budget,
        _recalibrated_raw_budget,
        evaluate,
        load_budget,
        main,
        measure,
        recalibrate_budget,
    )


def _budget(
    *categories: CategoryBudget, total_raw: int | None = None, total_gzip: int | None = None
) -> Budget:
    return Budget(categories=categories, total=TotalBudget(raw=total_raw, gzip=total_gzip))


class ClassificationTests(unittest.TestCase):
    def test_first_matching_pattern_wins(self) -> None:
        budget = _budget(
            CategoryBudget("html", ("*.html",), raw=None, gzip=None),
            CategoryBudget("everything", ("*",), raw=None, gzip=None),
        )
        self.assertEqual(_classify("standalone.html", budget.categories), "html")
        self.assertEqual(_classify("favicon.svg", budget.categories), "everything")

    def test_uncategorised_returned_when_no_pattern_matches(self) -> None:
        budget = _budget(CategoryBudget("html", ("*.html",), raw=None, gzip=None))
        self.assertEqual(_classify("favicon.svg", budget.categories), "uncategorised")

    def test_glob_supports_directory_prefixes(self) -> None:
        budget = _budget(CategoryBudget("css", ("assets/*.css",), raw=None, gzip=None))
        self.assertEqual(_classify("assets/main.css", budget.categories), "css")
        self.assertEqual(_classify("main.css", budget.categories), "uncategorised")


class GzipSizeTests(unittest.TestCase):
    def test_gzip_size_is_byte_for_byte_deterministic(self) -> None:
        data = b"hello world" * 100
        a = _gzip_size(data)
        b = _gzip_size(data)
        self.assertEqual(a, b)
        # And it is always smaller than the raw bytes for compressible input.
        self.assertLess(a, len(data))

    def test_gzip_size_matches_module_output(self) -> None:
        data = b"abcdef" * 50
        # The shape of output sizes should match the gzip module's defaults
        # for the same level/mtime, so the result is reproducible.
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=9, mtime=0) as handle:
            handle.write(data)
        self.assertEqual(_gzip_size(data), buffer.tell())


class FormatBytesTests(unittest.TestCase):
    def test_under_one_kib_uses_bytes(self) -> None:
        self.assertEqual(_format_bytes(0), "0 B")
        self.assertEqual(_format_bytes(1023), "1023 B")

    def test_kibibytes(self) -> None:
        self.assertEqual(_format_bytes(2048), "2.0 KiB")

    def test_mebibytes(self) -> None:
        self.assertEqual(_format_bytes(2 * 1024 * 1024), "2.00 MiB")

    def test_summary_reports_raw_and_gzip_deltas_for_categories_and_total(self) -> None:
        budget = _budget(CategoryBudget("html", ("*.html",), raw=200, gzip=100))
        sizes = {"html": CategorySizes(name="html", raw_bytes=120, gzip_bytes=60)}
        total = CategorySizes(name="TOTAL", raw_bytes=120, gzip_bytes=60)

        rendered = _format_summary(
            sizes,
            total,
            budget,
            uncategorised=[],
            violations=[],
            baseline={
                "html": {"raw_bytes": 100, "gzip_bytes": 50},
                "TOTAL": {"raw_bytes": 100, "gzip_bytes": 50},
            },
        )

        self.assertIn("delta raw", rendered)
        self.assertIn("delta gzip", rendered)
        self.assertEqual(rendered.count("+20"), 2)
        self.assertEqual(rendered.count("+10"), 2)

    def test_summary_explains_stable_total_chunk_redistribution(self) -> None:
        budget = _budget(
            CategoryBudget("runtime", ("runtime*.js",), raw=10000, gzip=5000),
            CategoryBudget("async", ("async*.js",), raw=10000, gzip=5000),
        )
        sizes = {
            "runtime": CategorySizes("runtime", 7000, 3000),
            "async": CategorySizes("async", 3000, 1000),
        }
        rendered = _format_summary(
            sizes,
            CategorySizes("TOTAL", 10000, 4000),
            budget,
            uncategorised=[],
            violations=[],
            baseline={
                "runtime": {"raw_bytes": 4000, "gzip_bytes": 2000},
                "async": {"raw_bytes": 6000, "gzip_bytes": 2000},
                "TOTAL": {"raw_bytes": 10000, "gzip_bytes": 4000},
            },
        )

        self.assertIn("Likely chunk redistribution", rendered)
        self.assertIn("into runtime", rendered)
        self.assertIn("out of async", rendered)


class MeasureAndEvaluateTests(unittest.TestCase):
    def _write_tree(self, root: Path, files: dict[str, bytes]) -> None:
        for relative, data in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

    def test_measure_groups_files_into_correct_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_tree(
                root,
                {
                    "standalone.html": b"<html>" + b"x" * 100,
                    "assets/main.js": b"console.log(1);" * 20,
                    "assets/style.css": b"body{}" * 30,
                    "favicon.svg": b"<svg/>",
                    "stray.bin": b"\x00\x01",
                },
            )
            budget = _budget(
                CategoryBudget("html", ("*.html",), raw=None, gzip=None),
                CategoryBudget("js", ("assets/*.js",), raw=None, gzip=None),
                CategoryBudget("css", ("assets/*.css",), raw=None, gzip=None),
            )
            sizes, uncategorised = measure(root, budget)
        self.assertEqual(sizes["html"].file_count, 1)
        self.assertEqual(sizes["js"].file_count, 1)
        self.assertEqual(sizes["css"].file_count, 1)
        # Two files (favicon + stray) had no matching pattern.
        self.assertEqual(sorted(uncategorised), ["favicon.svg", "stray.bin"])

    def test_measure_raises_when_directory_missing(self) -> None:
        with self.assertRaises(FileNotFoundError):
            measure(Path("definitely/does/not/exist"), _budget())

    def test_evaluate_flags_raw_and_gzip_violations_independently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "standalone.html").write_bytes(b"x" * 5000)
            budget = _budget(
                CategoryBudget("html", ("*.html",), raw=4000, gzip=10),
            )
            sizes, _ = measure(root, budget)
            violations, total = evaluate(sizes, budget)
        metrics = sorted((v.category, v.metric) for v in violations)
        self.assertIn(("html", "raw"), metrics)
        self.assertIn(("html", "gzip"), metrics)
        # Total roll-up should match the single file.
        self.assertEqual(total.raw_bytes, 5000)

    def test_evaluate_flags_total_budget_overage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.html").write_bytes(b"y" * 2000)
            budget = _budget(
                CategoryBudget("html", ("*.html",), raw=None, gzip=None),
                total_raw=1000,
            )
            sizes, _ = measure(root, budget)
            violations, _ = evaluate(sizes, budget)
        self.assertTrue(any(v.category == "TOTAL" and v.metric == "raw" for v in violations))


class LoadBudgetTests(unittest.TestCase):
    def test_load_budget_filters_invalid_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            path.write_text(
                json.dumps(
                    {
                        "categories": [
                            {"name": "html", "patterns": ["*.html"], "raw": 100, "gzip": 50},
                            {"name": "no-patterns", "patterns": []},
                            {"patterns": ["*.css"]},
                            "garbage",
                        ],
                        "total": {"raw": 999},
                    }
                ),
                encoding="utf-8",
            )
            budget = load_budget(path)
        self.assertEqual(len(budget.categories), 1)
        self.assertEqual(budget.categories[0].name, "html")
        self.assertEqual(budget.total.raw, 999)
        self.assertIsNone(budget.total.gzip)

    def test_load_budget_tolerates_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            payload = json.dumps(
                {"categories": [{"name": "h", "patterns": ["*"], "raw": 10}], "total": {}}
            )
            path.write_bytes(b"\xef\xbb\xbf" + payload.encode("utf-8"))
            budget = load_budget(path)
        self.assertEqual(budget.categories[0].name, "h")


class BaselineManifestTests(unittest.TestCase):
    def test_load_baseline_keeps_only_integer_measurements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(
                json.dumps(
                    {
                        "categories": {
                            "html": {"raw_bytes": 100, "gzip_bytes": 50, "files": []},
                            "invalid": "not a category",
                        },
                        "TOTAL": {"raw_bytes": 100, "gzip_bytes": 50, "file_count": 1},
                    }
                ),
                encoding="utf-8",
            )
            baseline = _load_baseline(path)

        self.assertEqual(
            baseline,
            {
                "html": {"raw_bytes": 100, "gzip_bytes": 50},
                "TOTAL": {"raw_bytes": 100, "gzip_bytes": 50, "file_count": 1},
            },
        )


class RecalibrationTests(unittest.TestCase):
    def _write_budget(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "_comment": "keep me",
                    "categories": [
                        {"name": "runtime", "patterns": ["*.js"], "raw": 100, "gzip": 50},
                        {"name": "data", "patterns": ["*.json"], "raw": 5000},
                    ],
                    "total": {"raw": 20000, "gzip": 10000},
                }
            ),
            encoding="utf-8",
        )

    def test_budget_rounding_matches_repository_policy(self) -> None:
        self.assertEqual(_recalibrated_raw_budget(340523), 344000)
        self.assertEqual(_recalibrated_gzip_budget(92646), 92700)

    def test_recalibration_updates_only_explicit_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            self._write_budget(path)
            updated = recalibrate_budget(
                path,
                {"runtime": CategorySizes("runtime", 340523, 92646, 1)},
                CategorySizes("TOTAL", 10000, 5000, 1),
                {"TOTAL": {"raw_bytes": 10000, "gzip_bytes": 5000}},
                ("runtime",),
            )
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(updated, {"runtime": (344000, 92700)})
        self.assertEqual(payload["categories"][1]["raw"], 5000)
        self.assertEqual(payload["_comment"], "keep me")

    def test_recalibration_requires_a_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            self._write_budget(path)
            with self.assertRaisesRegex(ValueError, "requires an existing --baseline"):
                recalibrate_budget(
                    path,
                    {"runtime": CategorySizes("runtime", 100, 50, 1)},
                    CategorySizes("TOTAL", 100, 50, 1),
                    None,
                    ("runtime",),
                )

    def test_recalibration_rejects_meaningful_total_growth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            self._write_budget(path)
            with self.assertRaisesRegex(ValueError, "total grew"):
                recalibrate_budget(
                    path,
                    {"runtime": CategorySizes("runtime", 13000, 6000, 1)},
                    CategorySizes("TOTAL", 13000, 6000, 1),
                    {"TOTAL": {"raw_bytes": 10000, "gzip_bytes": 4000}},
                    ("runtime",),
                )


class MainEntrypointTests(unittest.TestCase):
    def _silence_stdout(self) -> io.StringIO:
        return io.StringIO()

    def test_main_returns_zero_on_clean_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "build").mkdir()
            (root / "build" / "standalone.html").write_bytes(b"<html/>")
            budget_path = root / "budget.json"
            budget_path.write_text(
                json.dumps(
                    {
                        "categories": [
                            {"name": "html", "patterns": ["*.html"], "raw": 1000, "gzip": 500}
                        ],
                        "total": {"raw": 1000},
                    }
                ),
                encoding="utf-8",
            )
            buffer = self._silence_stdout()
            with redirect_stdout(buffer):
                rc = main(
                    [
                        "--build-dir",
                        str(root / "build"),
                        "--budget",
                        str(budget_path),
                    ]
                )
        self.assertEqual(rc, 0)

    def test_main_returns_one_on_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "build").mkdir()
            (root / "build" / "huge.html").write_bytes(b"x" * 5000)
            budget_path = root / "budget.json"
            budget_path.write_text(
                json.dumps(
                    {
                        "categories": [{"name": "html", "patterns": ["*.html"], "raw": 100}],
                        "total": {"raw": 100},
                    }
                ),
                encoding="utf-8",
            )
            buffer = self._silence_stdout()
            with redirect_stdout(buffer):
                rc = main(
                    [
                        "--build-dir",
                        str(root / "build"),
                        "--budget",
                        str(budget_path),
                    ]
                )
        self.assertEqual(rc, 1)
        self.assertIn("BUDGET VIOLATIONS", buffer.getvalue())

    def test_main_no_fail_returns_zero_even_on_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "build").mkdir()
            (root / "build" / "huge.html").write_bytes(b"x" * 5000)
            budget_path = root / "budget.json"
            budget_path.write_text(
                json.dumps(
                    {
                        "categories": [{"name": "html", "patterns": ["*.html"], "raw": 100}],
                        "total": {},
                    }
                ),
                encoding="utf-8",
            )
            buffer = self._silence_stdout()
            with redirect_stdout(buffer):
                rc = main(
                    [
                        "--build-dir",
                        str(root / "build"),
                        "--budget",
                        str(budget_path),
                        "--no-fail",
                    ]
                )
        self.assertEqual(rc, 0)

    def test_main_emits_json_manifest_alongside_summary_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "build").mkdir()
            (root / "build" / "standalone.html").write_bytes(b"<html/>")
            budget_path = root / "budget.json"
            budget_path.write_text(
                json.dumps(
                    {
                        "categories": [{"name": "html", "patterns": ["*.html"], "raw": 1000}],
                        "total": {"raw": 1000},
                    }
                ),
                encoding="utf-8",
            )
            output_path = root / "out" / "summary.txt"
            buffer = self._silence_stdout()
            with redirect_stdout(buffer):
                rc = main(
                    [
                        "--build-dir",
                        str(root / "build"),
                        "--budget",
                        str(budget_path),
                        "--output",
                        str(output_path),
                    ]
                )
            # Assertions must run inside the temp-dir context manager so the
            # files we wrote are still on disk.
            self.assertEqual(rc, 0)
            self.assertTrue(output_path.exists())
            manifest_path = output_path.with_suffix(output_path.suffix + ".json")
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("categories", manifest)
            self.assertIn("html", manifest["categories"])

    def test_main_reports_raw_and_gzip_deltas_from_baseline_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "build").mkdir()
            contents = b"<html/>"
            (root / "build" / "standalone.html").write_bytes(contents)
            budget_path = root / "budget.json"
            budget_path.write_text(
                json.dumps(
                    {
                        "categories": [{"name": "html", "patterns": ["*.html"]}],
                        "total": {},
                    }
                ),
                encoding="utf-8",
            )
            gzip_bytes = _gzip_size(contents)
            baseline_path = root / "baseline.json"
            baseline_path.write_text(
                json.dumps(
                    {
                        "categories": {"html": {"raw_bytes": 0, "gzip_bytes": 0}},
                        "TOTAL": {"raw_bytes": 0, "gzip_bytes": 0},
                    }
                ),
                encoding="utf-8",
            )
            buffer = self._silence_stdout()
            with redirect_stdout(buffer):
                rc = main(
                    [
                        "--build-dir",
                        str(root / "build"),
                        "--budget",
                        str(budget_path),
                        "--baseline",
                        str(baseline_path),
                    ]
                )

        self.assertEqual(rc, 0)
        self.assertIn(f"+{len(contents)}", buffer.getvalue())
        self.assertIn(f"+{gzip_bytes}", buffer.getvalue())

    def test_main_returns_two_when_build_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            budget_path = root / "budget.json"
            budget_path.write_text(json.dumps({"categories": [], "total": {}}), encoding="utf-8")
            buffer = self._silence_stdout()
            err = io.StringIO()
            from contextlib import redirect_stderr

            with redirect_stdout(buffer), redirect_stderr(err):
                rc = main(
                    [
                        "--build-dir",
                        str(root / "missing"),
                        "--budget",
                        str(budget_path),
                    ]
                )
        self.assertEqual(rc, 2)


class ViolationDataclassTests(unittest.TestCase):
    def test_violation_is_a_value_type(self) -> None:
        a = Violation("html", "raw", 100, 50)
        b = Violation("html", "raw", 100, 50)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
