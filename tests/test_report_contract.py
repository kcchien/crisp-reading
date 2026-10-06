import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PACKAGE_DIR / "scripts"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

from report_contract import validate_report  # noqa: E402


def load_renderer_module():
    spec = importlib.util.spec_from_file_location("crisp_renderer", SCRIPTS_DIR / "render-report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture(name):
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))


class ReportContractTests(unittest.TestCase):
    def assert_error(self, data, path_prefix, code=None):
        errors = validate_report(data)
        self.assertTrue(errors)
        self.assertTrue(all({"path", "code", "message"} <= set(error) for error in errors))
        matches = [error for error in errors if error["path"].startswith(path_prefix)]
        self.assertTrue(matches, errors)
        if code:
            self.assertTrue(any(error["code"] == code for error in matches), errors)

    def test_empty_object_reports_structured_missing_fields(self):
        self.assert_error({}, "report_mode", "required")

    def test_non_object_root_is_rejected(self):
        self.assert_error([], "$", "type")

    def test_valid_nonfiction_preliminary_and_literature_fixtures_pass(self):
        for name in ("nonfiction", "preliminary", "literature"):
            with self.subTest(name=name):
                self.assertEqual(validate_report(load_fixture(name)), [])

    def test_legacy_total_and_verdict_are_rejected(self):
        data = load_fixture("nonfiction")
        data["tips_scores"]["total"] = 7
        data["tips_scores"]["verdict"] = "好書"
        self.assert_error(data, "tips_scores.total", "forbidden")
        self.assert_error(data, "tips_scores.verdict", "forbidden")

    def test_missing_sources_field_is_not_treated_as_empty(self):
        data = load_fixture("nonfiction")
        del data["sources"]
        self.assert_error(data, "sources", "required")

    def test_duplicate_and_unresolved_source_ids_are_rejected(self):
        duplicate = load_fixture("nonfiction")
        duplicate["sources"].append(copy.deepcopy(duplicate["sources"][0]))
        self.assert_error(duplicate, "sources.1.id", "duplicate")

        unresolved = load_fixture("nonfiction")
        unresolved["core_arguments"][0]["source_ids"] = ["src-missing"]
        self.assert_error(unresolved, "core_arguments.0.source_ids.0", "unresolved_source")

    def test_unknown_or_not_applicable_dimension_cannot_have_score(self):
        data = load_fixture("preliminary")
        data["tips_scores"]["P"] = {
            "score": 1,
            "status": "unknown",
            "reason": "未提供讀者情境",
        }
        self.assert_error(data, "tips_scores.P.score", "status_score_mismatch")

    def test_assessed_dimension_requires_score_and_reason(self):
        data = load_fixture("nonfiction")
        data["tips_scores"]["T"] = {"score": None, "status": "assessed", "reason": ""}
        self.assert_error(data, "tips_scores.T.score", "status_score_mismatch")
        self.assert_error(data, "tips_scores.T.reason", "required")

    def test_quote_requires_resolvable_source_and_location(self):
        data = load_fixture("literature")
        data["quotes"][0]["source_id"] = "src-missing"
        data["quotes"][0]["location"] = ""
        self.assert_error(data, "quotes.0.source_id", "unresolved_source")
        self.assert_error(data, "quotes.0.location", "required")

    def test_rendered_items_require_the_fields_the_renderer_displays(self):
        data = load_fixture("edge")
        data["core_arguments"][0]["body"] = ""
        data["key_concepts"][0]["definition"] = ""
        data["concept_relations"][0]["relation"] = ""
        data["actions"][0]["description"] = ""
        self.assert_error(data, "core_arguments.0.body", "required")
        self.assert_error(data, "key_concepts.0.definition", "required")
        self.assert_error(data, "concept_relations.0.relation", "required")
        self.assert_error(data, "actions.0.description", "required")

    def test_optional_item_lists_reject_non_object_entries(self):
        data = load_fixture("nonfiction")
        data["actions"] = ["do something"]
        self.assert_error(data, "actions.0", "type")

    def test_full_report_requires_read_scope_and_sources(self):
        data = load_fixture("nonfiction")
        data["coverage"]["read_locations"] = []
        data["sources"] = []
        self.assert_error(data, "coverage.read_locations", "full_requires_coverage")
        self.assert_error(data, "sources", "full_requires_sources")

    def test_none_source_basis_cannot_mix_with_read_material(self):
        mixed = load_fixture("preliminary")
        mixed["coverage"]["source_basis"] = ["none", "public_metadata"]
        self.assert_error(mixed, "coverage.source_basis", "inconsistent_coverage")

        claimed_reading = load_fixture("preliminary")
        claimed_reading["coverage"]["read_locations"] = ["第一章"]
        self.assert_error(claimed_reading, "coverage.read_locations", "inconsistent_coverage")

    def test_full_report_rejects_partial_or_failed_coverage(self):
        for field in ("unread_locations", "failed_locations"):
            with self.subTest(field=field):
                data = load_fixture("nonfiction")
                data["coverage"][field] = ["第三章"]
                self.assert_error(data, f"coverage.{field}", "full_requires_complete_coverage")

        partial_basis = load_fixture("nonfiction")
        partial_basis["coverage"]["source_basis"] = ["partial_text"]
        self.assert_error(partial_basis, "coverage.source_basis", "full_requires_complete_coverage")

    def test_cli_validate_accepts_file_and_stdin_without_writing_html(self):
        script = SCRIPTS_DIR / "render-report.py"
        fixture = FIXTURES_DIR / "preliminary.json"
        with tempfile.TemporaryDirectory() as tmp:
            file_result = subprocess.run(
                [sys.executable, str(script), str(fixture), "--validate"],
                cwd=tmp,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(file_result.returncode, 0, file_result.stderr)
            self.assertEqual(json.loads(file_result.stdout)["valid"], True)
            self.assertEqual(list(Path(tmp).glob("*.html")), [])

            stdin_result = subprocess.run(
                [sys.executable, str(script), "-", "--validate"],
                cwd=tmp,
                input=fixture.read_text(encoding="utf-8"),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(stdin_result.returncode, 0, stdin_result.stderr)
            self.assertEqual(json.loads(stdin_result.stdout)["valid"], True)

    def test_cli_invalid_data_exits_nonzero_and_writes_no_html(self):
        script = SCRIPTS_DIR / "render-report.py"
        with tempfile.TemporaryDirectory() as tmp:
            invalid_path = Path(tmp) / "invalid.json"
            invalid_path.write_text("{}", encoding="utf-8")
            output_path = Path(tmp) / "must-not-exist.html"
            result = subprocess.run(
                [sys.executable, str(script), str(invalid_path), "-o", str(output_path)],
                cwd=tmp,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stderr)
            self.assertEqual(payload["success"], False)
            self.assertTrue(payload["errors"])
            self.assertFalse(output_path.exists())

    def test_render_entrypoint_rejects_invalid_report(self):
        renderer = load_renderer_module()
        with self.assertRaises(ValueError) as raised:
            renderer.render({}, "{{BOOK_TITLE}}")
        self.assertTrue(raised.exception.errors)


if __name__ == "__main__":
    unittest.main()
