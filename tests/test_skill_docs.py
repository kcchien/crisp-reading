import re
import unittest
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]


class SkillDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (PACKAGE_DIR / "SKILL.md").read_text(encoding="utf-8")
        cls.analysis = (PACKAGE_DIR / "references" / "analysis.md").read_text(encoding="utf-8")
        cls.readme = (PACKAGE_DIR / "README.md").read_text(encoding="utf-8")

    def test_entrypoint_routes_modes_without_promising_full_analysis_for_every_input(self):
        self.assertIn("preliminary", self.skill)
        self.assertIn("quick", self.skill)
        self.assertIn("notes", self.skill)
        self.assertIn("純文件摘要", self.skill)
        self.assertNotIn("所有路徑一律走完全流程", self.skill)
        self.assertNotIn("所有書籍一律執行完整深度分析", self.skill)

    def test_skill_uses_capability_names_not_specific_agent_tools(self):
        body = self.skill.split("---", 2)[-1]
        for stale_name in ("Claude", "WebFetch", "WebSearch"):
            self.assertNotIn(stale_name, body)

    def test_tips_has_no_total_or_fixed_book_grade(self):
        self.assertNotRegex(self.skill, r"[49]-12|總分解讀|N / 12")
        self.assertIn("unknown", self.skill)
        self.assertIn("not_applicable", self.skill)

    def test_analysis_guards_known_inference_boundaries(self):
        required_phrases = (
            "必要條件，不是充分條件",
            "分析者補強",
            "證據不足提高不確定性",
            "連結機制",
            "關鍵差異",
            "事實查核",
            "公眾評價",
            "文學分支",
            "逐列重算",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, self.analysis)

    def test_readme_keeps_portfolio_cover_and_matches_continuous_report(self):
        cover_path = PACKAGE_DIR / "assets" / "cover.webp"
        self.assertIn('src="assets/cover.webp"', self.readme)
        self.assertTrue(cover_path.is_file())
        for stale_claim in ("70,000+", "444+", "Claude 知識", "collapsible arguments", "SVG diagram", "精華版 / 完整版切換"):
            self.assertNotIn(stale_claim, self.readme)
        self.assertIn("連續章節", self.readme)
        self.assertIn("閱讀範圍", self.readme)

    def test_readme_links_cloudflare_report_gallery_in_both_languages(self):
        report_urls = (
            "https://books.kcchien.com/reading-report-the-great-gatsby.html",
            "https://books.kcchien.com/lao-can-you-ji.html",
            "https://books.kcchien.com/pride-and-prejudice.html",
            "https://books.kcchien.com/almanack-of-naval.html",
        )
        self.assertIn("公開成果瀏覽", self.readme)
        self.assertIn("Public report gallery", self.readme)
        for url in report_urls:
            self.assertEqual(self.readme.count(url), 2)

    def test_openai_metadata_is_present_and_not_truncated(self):
        metadata = (PACKAGE_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        match = re.search(r'short_description:\s*"([^"]+)"', metadata)
        self.assertIsNotNone(match)
        self.assertFalse(match.group(1).rstrip().endswith("·"))
        self.assertLessEqual(len(match.group(1)), 120)


if __name__ == "__main__":
    unittest.main()
