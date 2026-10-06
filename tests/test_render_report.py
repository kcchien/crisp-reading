import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PACKAGE_DIR / "scripts"
TEMPLATE_PATH = PACKAGE_DIR / "assets" / "reading-report-template.html"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))


def load_renderer():
    spec = importlib.util.spec_from_file_location("crisp_renderer_ui", SCRIPTS_DIR / "render-report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture(name):
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))


class RenderReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = load_renderer()
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def render(self, name, mutate=None):
        data = load_fixture(name)
        if mutate:
            mutate(data)
        return self.renderer.render(data, self.template)

    def test_preliminary_shows_mode_and_scope_without_empty_optional_sections(self):
        output = self.render("preliminary")
        self.assertIn("初步評估", output)
        self.assertIn("只有使用者提供的書名", output)
        self.assertIn("全書", output)
        for absent_heading in ("精選引句", "候選應用", "知識連結", "延伸閱讀"):
            self.assertNotIn(f">{absent_heading}<", output)
        self.assertNotIn("{{", output)

    def test_core_analysis_is_continuous_and_toc_only_links_existing_sections(self):
        output = self.render("nonfiction", lambda data: data.__setitem__("quotes", []))
        self.assertNotIn('role="tab"', output)
        self.assertNotIn('role="tabpanel"', output)
        self.assertRegex(output, r'href="#core-analysis"')
        self.assertRegex(output, r'id="core-analysis"')
        self.assertNotIn('href="#quotes"', output)

    def test_header_introduces_the_book_before_report_metadata(self):
        output = self.render("nonfiction")
        title_position = output.index("<h1>")
        author_position = output.index('class="header__author"')
        metadata_position = output.index('class="header__meta"')
        review_position = output.index('class="header__review"')

        self.assertLess(title_position, author_position)
        self.assertLess(author_position, metadata_position)
        self.assertLess(metadata_position, review_position)

    def test_sources_are_linked_from_claims_and_listed_with_locations(self):
        output = self.render("nonfiction")
        self.assertIn('href="#source-src-book"', output)
        self.assertIn('id="source-src-book"', output)
        self.assertIn("第一章", output)
        self.assertIn("合成控制材料 v1", output)

    def test_non_ascii_source_ids_get_distinct_stable_anchors(self):
        data = load_fixture("nonfiction")
        first = data["sources"][0]
        second = dict(first, id="乙")
        first["id"] = "甲"
        data["sources"].append(second)
        data["core_arguments"][0]["source_ids"] = ["甲", "乙"]
        for item in data["critical_perspectives"]:
            item["source_ids"] = ["甲"]
        for quote in data["quotes"]:
            quote["source_id"] = "甲"

        output = self.renderer.render(data, self.template)
        first_anchor = self.renderer.safe_anchor("甲")
        second_anchor = self.renderer.safe_anchor("乙")
        self.assertNotEqual(first_anchor, second_anchor)
        for anchor in (first_anchor, second_anchor):
            self.assertIn(f'href="#source-{anchor}"', output)
            self.assertIn(f'id="source-{anchor}"', output)

    def test_tips_show_reason_and_unknown_without_total_or_verdict(self):
        output = self.render("nonfiction")
        self.assertIn("未提供讀者情境。", output)
        self.assertIn("未知", output)
        self.assertNotIn("/ 12", output)
        self.assertNotIn("非常值得深讀", output)

    def test_literature_uses_interpretive_heading_and_has_no_forced_actions(self):
        output = self.render("literature")
        self.assertIn("詮釋與其他讀法", output)
        self.assertIn("不適用", output)
        self.assertNotIn("讀完之後，具體可以做什麼", output)
        self.assertNotIn(">候選應用<", output)

    def test_malicious_markup_is_sanitized_but_safe_table_remains(self):
        def mutate(data):
            data["core_arguments"][0]["body"] = (
                '<p onclick="steal()">安全段落 <strong>重點</strong></p>'
                '<script>alert("x")</script>'
                '<a href="javascript:alert(1)">危險連結</a>'
                '<table><thead><tr><th>欄</th></tr></thead><tbody><tr><td>值</td></tr></tbody></table>'
            )

        output = self.render("nonfiction", mutate)
        self.assertNotIn("<script>alert", output.lower())
        self.assertNotIn("onclick=", output.lower())
        self.assertNotIn('href="javascript:', output.lower())
        self.assertIn("<strong>重點</strong>", output)
        self.assertIn('class="table-scroll"', output)
        self.assertIn("<table>", output)

    def test_long_source_text_has_breakable_scope_without_global_word_break(self):
        token = "https://example.invalid/" + "a" * 240

        def mutate(data):
            data["sources"][0]["url"] = token
            data["sources"][0]["locations"] = [token]

        output = self.render("nonfiction", mutate)
        self.assertIn("breakable", output)
        self.assertIn("overflow-wrap: anywhere", output)
        body_rule = re.search(r"body\s*\{([^}]+)\}", output)
        self.assertIsNotNone(body_rule)
        self.assertNotIn("word-break: break-all", body_rule.group(1))

    def test_edge_fixture_keeps_action_detail_and_readable_table_columns(self):
        output = self.render("edge")
        self.assertIn("確認頁面本身沒有水平溢位。", output)
        self.assertRegex(output, r"th, td\s*\{[^}]*min-width:\s*7rem")

    def test_quotes_distinguish_direct_text_translation_and_paraphrase(self):
        direct = self.render("literature")
        self.assertIn("原文引句", direct)
        self.assertIn("第二節", direct)

        def mutate(data):
            data["quotes"] = [{
                "quote_type": "paraphrase",
                "paraphrase": "這是轉述，不是逐字引句。",
                "source_id": "src-story",
                "location": "第三節",
            }]

        paraphrase = self.render("literature", mutate)
        self.assertIn("轉述", paraphrase)
        self.assertNotIn("原文引句", paraphrase)

    def test_markdown_export_keeps_scope_tips_reasons_and_sources(self):
        data = load_fixture("nonfiction")
        markdown = self.renderer.build_markdown(data)
        self.assertIn("## 閱讀範圍", markdown)
        self.assertIn("未提供讀者情境。", markdown)
        self.assertIn("## 來源", markdown)
        self.assertIn("src-book", markdown)
        self.assertNotIn("/ 12", markdown)

    def test_markdown_export_keeps_all_structured_sections_and_attribution(self):
        data = load_fixture("edge")
        data["zettelkasten"] = [
            {"type": "permanent", "concept": "可回查性", "reason": "保留依據", "links_to": "來源"}
        ]
        data["meta_knowledge"] = [
            {"lens": "證據邊界", "description": "區分可見與推論", "delta": "降低過度宣稱"}
        ]
        data["further_reading"] = [{"title": "延伸材料", "reason": "補足背景"}]

        markdown = self.renderer.build_markdown(data)
        for heading in (
            "## 概念與關係",
            "## 批判與替代解釋",
            "## 候選應用",
            "## 可遷移的理解",
            "## 知識連結",
            "## 延伸閱讀",
        ):
            self.assertIn(heading, markdown)
        self.assertIn("歸屬：分析者推論", markdown)
        self.assertIn("依據：src-edge", markdown)
        self.assertIn("交付前", markdown)
        self.assertIn("降低過度宣稱", markdown)
        self.assertIn("可回查性", markdown)
        self.assertIn("延伸材料", markdown)

    def test_template_has_truthful_copy_recovery_download_and_no_print_state_mutation(self):
        output = self.render("nonfiction")
        self.assertIn('id="download-md"', output)
        self.assertIn('role="status"', output)
        self.assertIn("document.execCommand", output)
        self.assertIn("copyResult === true", output)
        self.assertIn("複製失敗", output)
        self.assertNotIn('matchMedia("print").addEventListener', output)

    def test_skip_link_target_can_receive_keyboard_focus(self):
        output = self.render("nonfiction")
        self.assertIn('<main class="page" id="main-content" tabindex="-1">', output)

    def test_no_javascript_core_content_is_present_in_html(self):
        output = self.render("nonfiction")
        scriptless = re.sub(r"<script\b[^>]*>.*?</script>", "", output, flags=re.S | re.I)
        self.assertIn("讓求證成本與錯誤成本相稱", scriptless)
        self.assertIn("跨章張力", scriptless)
        self.assertIn("來源", scriptless)


if __name__ == "__main__":
    unittest.main()
