#!/usr/bin/env python3
"""
將 Claude 的分析結果（JSON）套用到 HTML 模板，產出閱讀報告。
此腳本不消耗 token，純粹做模板填充。

用法：
  python render-report.py analysis.json                     # 輸出到同目錄
  python render-report.py analysis.json -o report.html      # 指定輸出路徑
  echo '{"book_title": "..."}' | python render-report.py -  # 從 stdin 讀取

JSON 結構見底部的 SCHEMA 說明。
"""

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "reading-report-template.html"


def escape(text):
    """HTML 轉義"""
    if not text:
        return ""
    return html.escape(str(text))


# Claude 產出中常見的 inline HTML 標籤
_INLINE_HTML_RE = re.compile(r"<(?:strong|em|b|i|u|br|a |span |mark|code|sub|sup)[>\s/]", re.IGNORECASE)


def contains_html(text):
    """偵測文字中是否包含 HTML 標籤（用於判斷是否跳過 escape）。
    安全假設：JSON 來源為 Claude 分析產出，非使用者直接輸入。"""
    return bool(_INLINE_HTML_RE.search(str(text)))


def render_introduction(text):
    """書籍簡介 → 純文字（HTML 轉義）"""
    if not text:
        return ""
    return escape(text)


def render_tips_scores(tips):
    """TIPS 評分 → 評分區塊 HTML（含圓點指示器與等級表）"""
    if not tips:
        return ""
    dim_names = {
        "T": "工具性",
        "I": "啟發性",
        "P": "實用性",
        "S": "科學性",
    }
    items = []
    for key in ("T", "I", "P", "S"):
        score = int(tips.get(key, 0))
        name = dim_names.get(key, key)
        # 圓點：實心 ● = 已得分，空心 ○ = 未得分
        dots = []
        for i in range(1, 4):
            if i <= score:
                dots.append('<span class="tips-scores__dot--filled">&#9679;</span>')
            else:
                dots.append('<span class="tips-scores__dot--empty">&#9675;</span>')
        dots_html = "".join(dots)
        items.append(
            f'<div class="tips-scores__item">'
            f'<span class="tips-scores__dim">{escape(name)}</span>'
            f'<div class="tips-scores__dots">{dots_html}</div>'
            f'</div>'
        )
    total = tips.get("total", 0)
    verdict = escape(tips.get("verdict", ""))
    total_html = f'<p class="tips-scores__total"><strong>{escape(str(total))}</strong> / 12 — {verdict}</p>'
    legend_html = '<p class="tips-scores__legend">4-5 一般 &#x2003; 6-8 好書 &#x2003; 9-12 非常值得深讀</p>'

    return (
        f'<div class="tips-scores page">\n'
        f'  <p class="tips-scores__label">TIPS 評分</p>\n'
        f'  <div class="tips-scores__grid">\n'
        f'    {"".join(items)}\n'
        f'  </div>\n'
        f'  {total_html}\n'
        f'  {legend_html}\n'
        f'</div>'
    )


def render_author(data):
    """處理作者顯示：若有 book_author_zh 則組合為「中文譯名（原文）」"""
    author = data.get("book_author", "未知作者")
    author_zh = data.get("book_author_zh", "")
    if author_zh:
        return escape(f"{author_zh}（{author}）")
    return escape(author)


def render_arguments(arguments):
    """核心論點 → details/summary HTML

    body 可以是純文字或 Claude 產出的 HTML。
    當 body 以 '<' 開頭時視為已格式化的 HTML，直接嵌入（信任 Claude 產出）。
    安全假設：JSON 來源為 Claude 分析產出，非使用者直接輸入。
    """
    if not arguments:
        return ""
    parts = []
    for arg in arguments:
        title = escape(arg.get("title", ""))
        body = arg.get("body", "")
        if body.strip().startswith("<") or contains_html(body):
            # 已含 HTML 標籤（整段 HTML 或混合內容），直接嵌入
            if not body.strip().startswith("<"):
                # 混合內容：用 <p> 包裹每行但不 escape（保留 inline HTML）
                body = "".join(f"<p>{line}</p>" for line in body.split("\n") if line.strip())
        else:
            body = "".join(f"<p>{escape(line)}</p>" for line in body.split("\n") if line.strip())
        parts.append(
            f'<details class="argument">\n'
            f'  <summary>{title}<span class="argument__arrow" aria-hidden="true">&#9654;</span></summary>\n'
            f'  <div class="argument__body">{body}</div>\n'
            f'</details>'
        )
    return "\n".join(parts)


def render_concepts(concepts):
    """關鍵概念 → concept list HTML"""
    if not concepts:
        return ""
    parts = []
    for c in concepts:
        name = escape(c.get("name", ""))
        definition = escape(c.get("definition", ""))
        boundary = escape(c.get("boundary", ""))
        boundary_html = (
            f'\n  <p class="concept__boundary">適用邊界｜{boundary}</p>'
            if boundary else ""
        )
        parts.append(
            f'<div class="concept">\n'
            f'  <p class="concept__name">{name}</p>\n'
            f'  <p class="concept__def">{definition}</p>'
            f'{boundary_html}\n'
            f'</div>'
        )
    return "\n".join(parts)


def render_quotes(quotes):
    """精選引句 → blockquote HTML"""
    if not quotes:
        return ""
    parts = []
    for q in quotes:
        text = escape(q.get("text", ""))
        source = escape(q.get("source", ""))
        parts.append(
            f'<blockquote class="quote">\n'
            f'  <p class="quote__text">{text}</p>\n'
            f'  <p class="quote__source">{source}</p>\n'
            f'</blockquote>'
        )
    return "\n".join(parts)


def render_actions(actions):
    """行動方案 → action cards HTML"""
    if not actions:
        return ""
    parts = []
    for a in actions:
        title = escape(a.get("title", ""))
        description = escape(a.get("description", ""))
        when = escape(a.get("when", ""))
        context = escape(a.get("context", ""))
        action = escape(a.get("action", ""))

        meta = ""
        if when or context or action:
            meta_parts = []
            if when:
                meta_parts.append(f"<span>{when}</span>")
            if context:
                meta_parts.append(f"<span>{context}</span>")
            if action:
                meta_parts.append(f"<span>{action}</span>")
            meta = f'\n      <div class="action-meta">{"".join(meta_parts)}</div>'

        parts.append(
            f'<div class="action-item">\n'
            f'  <div class="action-item__content">\n'
            f"    <h4>{title}</h4>\n"
            f"    <p>{description}</p>{meta}\n"
            f"  </div>\n"
            f"</div>"
        )
    return "\n".join(parts)


def render_critical(critical):
    """批判視角 → prose HTML

    content 可以是純文字或 Claude 產出的 HTML（以 '<' 開頭時直接嵌入）。
    安全假設：JSON 來源為 Claude 分析產出，非使用者直接輸入。
    """
    if not critical:
        return ""
    if isinstance(critical, str):
        if critical.strip().startswith("<") or contains_html(critical):
            return critical
        paragraphs = critical.split("\n\n")
        return "\n".join(f"<p>{escape(p)}</p>" for p in paragraphs if p.strip())

    # 結構化格式：[{title, content}]
    parts = []
    for section in critical:
        title = escape(section.get("title", ""))
        content = section.get("content", "")
        if content.strip().startswith("<") or contains_html(content):
            # 含 HTML 標籤，直接嵌入
            if not content.strip().startswith("<"):
                content = "".join(
                    f"<p>{line}</p>" for line in content.split("\n") if line.strip()
                )
        else:
            content = "".join(
                f"<p>{escape(line)}</p>" for line in content.split("\n") if line.strip()
            )
        parts.append(f"<h3>{title}</h3>\n{content}")
    return "\n".join(parts)


def render_zettelkasten(notes):
    """知識連結 → zettel list HTML"""
    if not notes:
        return ""
    parts = []
    for n in notes:
        note_type = escape(n.get("type", "permanent"))
        link = escape(n.get("concept", ""))
        reason = escape(n.get("reason", ""))
        links_to = escape(n.get("links_to", ""))
        links_to_html = (
            f' → <span class="zettel-list__link-to">{links_to}</span>'
            if links_to else ""
        )
        parts.append(
            f"<li>"
            f'<span class="zettel-list__type">{note_type}</span>'
            f'<span class="zettel-list__link">{link}</span>'
            f' — <span class="zettel-list__reason">{reason}</span>'
            f'{links_to_html}'
            f"</li>"
        )
    return "\n".join(parts)


def render_further_reading(books):
    """延伸閱讀 → further reading HTML"""
    if not books:
        return ""
    parts = []
    for b in books:
        title = escape(b.get("title", ""))
        reason = escape(b.get("reason", ""))
        parts.append(
            f'<div class="further-item">\n'
            f'  <p class="further-item__title">{title}</p>\n'
            f'  <p class="further-item__reason">{reason}</p>\n'
            f"</div>"
        )
    return "\n".join(parts)


def render_meta_knowledge(items):
    """思維模型 → 完整 section HTML（含標題），空時回傳空字串以隱藏整個區塊"""
    if not items:
        return ""
    parts = []
    for m in items:
        lens = escape(m.get("lens", ""))
        desc = escape(m.get("description", ""))
        delta = escape(m.get("delta", ""))
        parts.append(
            f'<div class="meta-item">\n'
            f'  <h3 class="meta-item__lens">{lens}</h3>\n'
            f'  <p class="meta-item__desc">{desc}</p>\n'
            f'  <p class="meta-item__delta">{delta}</p>\n'
            f'</div>'
        )
    inner = "\n".join(parts)
    return (
        f'<section class="section" aria-label="思維模型">\n'
        f'  <p class="section__label">思維模型</p>\n'
        f'  <h2>這本書給你什麼新的「看問題方式」</h2>\n'
        f'  <div class="meta-list">\n'
        f'    {inner}\n'
        f'  </div>\n'
        f'</section>'
    )


def render_svg(svg_data):
    """概念關係圖 SVG — 直接傳入或空字串"""
    if not svg_data:
        return ""
    return svg_data


def render(data, template_text):
    """將分析 JSON 填入模板"""
    replacements = {
        "{{BOOK_TITLE}}": escape(data.get("book_title", "未知書名")),
        "{{BOOK_AUTHOR}}": render_author(data),
        "{{ONE_LINE_REVIEW}}": escape(data.get("one_line_review", "")),
        "{{BOOK_TYPE_TAG}}": escape(data.get("book_type_tag", "閱讀報告")),
        "{{BOOK_INTRODUCTION}}": render_introduction(data.get("book_introduction", "")),
        "{{TIPS_SCORES_HTML}}": render_tips_scores(data.get("tips_scores")),
        "{{CORE_ARGUMENTS_HTML}}": render_arguments(data.get("core_arguments", [])),
        "{{KEY_CONCEPTS_HTML}}": render_concepts(data.get("key_concepts", [])),
        "{{QUOTES_HTML}}": render_quotes(data.get("quotes", [])),
        "{{ACTION_CARDS_HTML}}": render_actions(data.get("actions", [])),
        "{{CONCEPT_RELATIONS_SVG}}": render_svg(data.get("concept_relations_svg", "")),
        "{{CRITICAL_PERSPECTIVES_HTML}}": render_critical(data.get("critical_perspectives")),
        "{{ZETTELKASTEN_HTML}}": render_zettelkasten(data.get("zettelkasten", [])),
        "{{META_KNOWLEDGE_HTML}}": render_meta_knowledge(data.get("meta_knowledge", [])),
        "{{FURTHER_READING_HTML}}": render_further_reading(data.get("further_reading", [])),
        "{{GENERATION_DATE}}": data.get("generation_date", date.today().isoformat()),
    }

    result = template_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def main():
    parser = argparse.ArgumentParser(description="CRISP 閱讀解構師：HTML 報告渲染")
    parser.add_argument("input", help="分析結果 JSON 檔案路徑，或 - 從 stdin 讀取")
    parser.add_argument("--output", "-o", help="輸出 HTML 路徑")
    parser.add_argument("--template", "-t", help="自訂模板路徑（預設使用內建模板）")
    args = parser.parse_args()

    # 讀取 JSON
    if args.input == "-":
        data = json.loads(sys.stdin.read())
    else:
        input_path = Path(args.input)
        if not input_path.is_file():
            print(json.dumps({"success": False, "error": f"找不到：{args.input}"}), file=sys.stderr)
            sys.exit(1)
        data = json.loads(input_path.read_text(encoding="utf-8"))

    # 讀取模板
    template_path = Path(args.template) if args.template else TEMPLATE_PATH
    if not template_path.is_file():
        print(
            json.dumps({"success": False, "error": f"找不到模板：{template_path}"}),
            file=sys.stderr,
        )
        sys.exit(1)
    template_text = template_path.read_text(encoding="utf-8")

    # 渲染
    html_output = render(data, template_text)

    # 輸出
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(html_output, encoding="utf-8")
        print(json.dumps({"success": True, "output_path": str(output_path)}, ensure_ascii=False))
    else:
        # 自動命名
        slug = data.get("slug", "book")
        output_path = Path.cwd() / f"reading-report-{slug}.html"
        output_path.write_text(html_output, encoding="utf-8")
        print(json.dumps({"success": True, "output_path": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
