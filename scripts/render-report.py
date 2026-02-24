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
import sys
from datetime import date
from pathlib import Path


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "reading-report-template.html"


def escape(text):
    """HTML 轉義"""
    if not text:
        return ""
    return html.escape(str(text))


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
        if not body.strip().startswith("<"):
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
        parts.append(
            f'<div class="concept">\n'
            f'  <p class="concept__name">{name}</p>\n'
            f'  <p class="concept__def">{definition}</p>\n'
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
        # 已經是 HTML 或純文字
        if critical.strip().startswith("<"):
            return critical
        paragraphs = critical.split("\n\n")
        return "\n".join(f"<p>{escape(p)}</p>" for p in paragraphs if p.strip())

    # 結構化格式：[{title, content}]
    parts = []
    for section in critical:
        title = escape(section.get("title", ""))
        content = section.get("content", "")
        if not content.strip().startswith("<"):
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
        parts.append(
            f"<li>"
            f'<span class="zettel-list__type">{note_type}</span>'
            f'<span class="zettel-list__link">{link}</span>'
            f' — <span class="zettel-list__reason">{reason}</span>'
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


def render_svg(svg_data):
    """概念關係圖 SVG — 直接傳入或空字串"""
    if not svg_data:
        return ""
    return svg_data


def render(data, template_text):
    """將分析 JSON 填入模板"""
    replacements = {
        "{{BOOK_TITLE}}": escape(data.get("book_title", "未知書名")),
        "{{BOOK_AUTHOR}}": escape(data.get("book_author", "未知作者")),
        "{{ONE_LINE_REVIEW}}": escape(data.get("one_line_review", "")),
        "{{BOOK_TYPE_TAG}}": escape(data.get("book_type_tag", "閱讀報告")),
        "{{CORE_ARGUMENTS_HTML}}": render_arguments(data.get("core_arguments", [])),
        "{{KEY_CONCEPTS_HTML}}": render_concepts(data.get("key_concepts", [])),
        "{{QUOTES_HTML}}": render_quotes(data.get("quotes", [])),
        "{{ACTION_CARDS_HTML}}": render_actions(data.get("actions", [])),
        "{{CONCEPT_RELATIONS_SVG}}": render_svg(data.get("concept_relations_svg", "")),
        "{{CRITICAL_PERSPECTIVES_HTML}}": render_critical(data.get("critical_perspectives")),
        "{{ZETTELKASTEN_HTML}}": render_zettelkasten(data.get("zettelkasten", [])),
        "{{FURTHER_READING_HTML}}": render_further_reading(data.get("further_reading", [])),
        "{{GENERATION_DATE}}": data.get("generation_date", date.today().isoformat()),
    }

    result = template_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def main():
    parser = argparse.ArgumentParser(description="CRISP 閱讀助手：HTML 報告渲染")
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
