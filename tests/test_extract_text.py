import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from contextlib import redirect_stdout


PACKAGE_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PACKAGE_DIR / "scripts" / "extract-text.py"


def load_extractor():
    spec = importlib.util.spec_from_file_location("crisp_extract_text", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExtractTextTests(unittest.TestCase):
    def setUp(self):
        self.extractor = load_extractor()

    def test_all_failed_chunks_report_failed_and_keep_ranges(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            self.extractor, "get_pdf_info", return_value={"success": True, "page_count": 4}
        ), mock.patch.object(
            self.extractor,
            "extract_document",
            create=True,
            side_effect=[
                {"success": False, "error": "OCR failed"},
                {"success": False, "error": "timeout"},
            ],
        ):
            result = self.extractor.chunk_extract("book.pdf", 2, tmp, "gateway.py")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["failed_ranges"], ["1-2", "3-4"])
        self.assertEqual(result["chunks"][0]["error"], "OCR failed")

    def test_partial_chunks_report_partial_and_do_not_claim_success(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            self.extractor, "get_pdf_info", return_value={"success": True, "page_count": 4}
        ), mock.patch.object(
            self.extractor,
            "extract_document",
            create=True,
            side_effect=[
                {"success": True, "content": "first", "output_path": str(Path(tmp) / "one.md")},
                {"success": False, "error": "page image unreadable"},
            ],
        ):
            result = self.extractor.chunk_extract("book.pdf", 2, tmp, "gateway.py")

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["failed_ranges"], ["3-4"])

    def test_non_positive_chunk_size_is_rejected(self):
        for chunk_size in (0, -2):
            with self.subTest(chunk_size=chunk_size), tempfile.TemporaryDirectory() as tmp:
                result = self.extractor.chunk_extract("book.pdf", chunk_size, tmp, "gateway.py")
            self.assertEqual(result["success"], False)
            self.assertEqual(result["status"], "failed")
            self.assertIn("正整數", result["error"])

    def test_pdf_page_audit_marks_missing_pages_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "book.pdf"
            input_path.write_bytes(b"placeholder")
            with mock.patch.object(
                self.extractor,
                "extract_via_pymupdf",
                return_value={"success": True, "status": "complete", "content": "pages 1 and 3"},
            ), mock.patch.object(
                self.extractor,
                "audit_pdf_page_coverage",
                return_value={"verified": True, "failed_ranges": ["2"]},
            ):
                result = self.extractor.extract_document(input_path)

        self.assertEqual(result["success"], False)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["failed_ranges"], ["2"])

    def test_chunk_extract_preserves_inner_failed_page_ranges(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            self.extractor, "get_pdf_info", return_value={"success": True, "page_count": 4}
        ), mock.patch.object(
            self.extractor,
            "extract_document",
            side_effect=[
                {"success": False, "status": "partial", "failed_ranges": ["2"], "content": "page 1"},
                {"success": True, "status": "complete", "failed_ranges": [], "content": "pages 3-4"},
            ],
        ):
            result = self.extractor.chunk_extract("book.pdf", 2, tmp, "gateway.py")

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["failed_ranges"], ["2"])
        self.assertEqual(result["chunks"][0]["status"], "partial")

    def test_gateway_rejects_unexpected_empty_output(self):
        completed = subprocess.CompletedProcess(["gateway"], 0, stdout=" \n", stderr="")
        with mock.patch.object(self.extractor.subprocess, "run", return_value=completed):
            result = self.extractor.extract_via_gateway("gateway.py", "book.pdf")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["success"], False)
        self.assertIn("空白", result["error"])

    def test_gateway_timeout_returns_structured_failure(self):
        with mock.patch.object(
            self.extractor.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["gateway"], timeout=300),
        ):
            result = self.extractor.extract_via_gateway("gateway.py", "book.pdf")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["success"], False)
        self.assertIn("逾時", result["error"])

    def test_pdf_gateway_failure_uses_pymupdf_only_when_it_succeeds(self):
        with mock.patch.object(
            self.extractor, "extract_via_gateway", return_value={"success": False, "error": "gateway failed"}
        ), mock.patch.object(
            self.extractor,
            "extract_via_pymupdf",
            return_value={"success": True, "status": "complete", "content": "fallback text"},
        ), mock.patch.object(
            self.extractor,
            "audit_pdf_page_coverage",
            return_value={"verified": True, "failed_ranges": []},
        ):
            result = self.extractor.extract_document(Path("book.pdf"), gateway_path="gateway.py")
        self.assertEqual(result["success"], True)
        self.assertEqual(result["backend"], "pymupdf4llm")
        self.assertEqual(result["warnings"], ["gateway failed"])

    def test_epub_gateway_failure_has_no_fake_pdf_fallback(self):
        with mock.patch.object(
            self.extractor, "extract_via_gateway", return_value={"success": False, "error": "gateway failed"}
        ), mock.patch.object(self.extractor, "extract_via_pymupdf") as pymupdf:
            result = self.extractor.extract_document(Path("book.epub"), gateway_path="gateway.py")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["status"], "failed")
        pymupdf.assert_not_called()

    def test_chunking_policy_uses_explicit_capacity_or_conservative_default(self):
        unknown = self.extractor.build_chunking_policy(90_000, None)
        self.assertEqual(unknown["capacity_source"], "conservative_default")
        self.assertEqual(unknown["needs_chunking"], True)
        self.assertEqual(unknown["analysis_budget_tokens"], 80_000)

        known = self.extractor.build_chunking_policy(90_000, 200_000)
        self.assertEqual(known["capacity_source"], "explicit")
        self.assertEqual(known["analysis_budget_tokens"], 130_000)
        self.assertEqual(known["needs_chunking"], False)

    def test_whitespace_pymupdf_output_is_failure(self):
        fake_module = mock.Mock()
        fake_module.to_markdown.return_value = "\n\t"
        with mock.patch.dict("sys.modules", {"pymupdf4llm": fake_module}):
            result = self.extractor.extract_via_pymupdf("book.pdf")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["success"], False)

    def test_cli_output_metadata_keeps_status_backend_and_ranges(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "book.pdf"
            input_path.write_bytes(b"placeholder")
            output_path = Path(tmp) / "book.md"
            result = {
                "success": True,
                "status": "complete",
                "backend": "pymupdf4llm",
                "chunks": [],
                "failed_ranges": [],
                "content": "extracted",
            }
            with mock.patch.object(self.extractor, "find_gateway", return_value=None), mock.patch.object(
                self.extractor, "extract_document", return_value=result
            ), mock.patch.object(
                self.extractor.sys,
                "argv",
                [str(SCRIPT_PATH), str(input_path), "-o", str(output_path)],
            ), redirect_stdout(io.StringIO()) as stdout:
                self.extractor.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "complete")
        self.assertEqual(payload["backend"], "pymupdf4llm")
        self.assertEqual(payload["failed_ranges"], [])

    def test_pdf_info_returns_structured_failure_when_document_cannot_open(self):
        fake_module = mock.Mock()
        fake_module.open.side_effect = ValueError("broken pdf")
        with mock.patch.dict("sys.modules", {"pymupdf": fake_module}):
            result = self.extractor.get_pdf_info("broken.pdf")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["status"], "failed")
        self.assertIn("broken pdf", result["error"])

    def test_pdf_toc_returns_structured_failure_when_document_cannot_open(self):
        fake_module = mock.Mock()
        fake_module.open.side_effect = ValueError("broken pdf")
        with mock.patch.dict("sys.modules", {"pymupdf": fake_module}):
            result = self.extractor.get_toc("broken.pdf")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["status"], "failed")
        self.assertIn("broken pdf", result["error"])


if __name__ == "__main__":
    unittest.main()
