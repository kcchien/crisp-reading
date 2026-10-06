#!/usr/bin/env python3
"""Validate CRISP report JSON and render a self-contained reading report."""

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from report_contract import validate_report


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "reading-report-template.html"

MODE_LABELS = {
    "full": "完整深讀",
    "preliminary": "初步評估",
    "quick": "快速評估",
    "notes": "筆記深化",
}

TIP_LABELS = {"T": "工具性", "I": "啟發性", "P": "實用性", "S": "科學性"}
TIP_STATUS_LABELS = {"unknown": "未知", "not_applicable": "不適用"}
SOURCE_BASIS_LABELS = {
    "full_text": "全文",
    "partial_text": "部分文本",
    "reader_notes": "讀者筆記",
    "public_metadata": "已查閱的公開資料",
    "none": "未取得可查閱材料",
}

ALLOWED_TAGS = {
    "p",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "br",
    "code",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "a",
}

VOID_TAGS = {"br"}


class ReportValidationError(ValueError):
    def __init__(self, errors):
        super().__init__("報告資料不符合契約")
        self.errors = errors


def escape(value):
    return html.escape("" if value is None else str(value), quote=True)


def safe_anchor(value):
    raw = str(value)
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", raw).strip("-")
    if normalized and normalized == raw:
        return normalized
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"{normalized or 'source'}-{digest}"


def safe_url(value):
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() in {"http", "https", "mailto"}:
        return value.strip()
    if value.startswith("#"):
        return value
    return None


class SafeHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            return
        safe_attrs = []
        attrs = dict(attrs)
        if tag == "a":
            href = safe_url(attrs.get("href"))
            if href:
                safe_attrs.append(("href", href))
            if attrs.get("title"):
                safe_attrs.append(("title", attrs["title"]))
        elif tag in {"th", "td"}:
            for name in ("scope", "colspan", "rowspan"):
                value = attrs.get(name)
                if value and re.fullmatch(r"[A-Za-z0-9_-]+", value):
                    safe_attrs.append((name, value))
        rendered_attrs = "".join(f' {name}="{escape(value)}"' for name, value in safe_attrs)
        self.parts.append(f"<{tag}{rendered_attrs}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ALLOWED_TAGS and tag not in VOID_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(escape(data))


class PlainTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def sanitize_html_fragment(value):
    parser = SafeHTMLParser()
    parser.feed(str(value))
    parser.close()
    rendered = "".join(parser.parts)
    rendered = rendered.replace(
        "<table>",
        '<div class="table-scroll" role="region" aria-label="可橫向捲動的資料表" tabindex="0"><table>',
    ).replace("</table>", "</table></div>")
    return rendered


def plain_text(value):
    parser = PlainTextParser()
    parser.feed(str(value or ""))
    parser.close()
    return " ".join("".join(parser.parts).split())


def render_rich_text(value):
    if not value:
        return ""
    text = str(value)
    if re.search(r"<[A-Za-z][^>]*>", text):
        return sanitize_html_fragment(text)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    return "".join(f"<p>{escape(part)}</p>" for part in paragraphs)


def render_author(data):
    author = data.get("book_author")
    author_zh = data.get("book_author_zh")
    if author and author_zh:
        return escape(f"{author_zh}（{author}）")
    if author:
        return escape(author)
    return "作者未確認"


def render_coverage(data):
    coverage = data["coverage"]
    rows = [
        ("要求範圍", coverage["requested_scope"]),
        ("已讀位置", "、".join(coverage["read_locations"]) or "未取得可讀內容"),
        ("未讀位置", "、".join(coverage["unread_locations"]) or "無"),
        ("失敗位置", "、".join(coverage["failed_locations"]) or "無"),
        (
            "依據類型",
            "、".join(SOURCE_BASIS_LABELS.get(item, item) for item in coverage["source_basis"]),
        ),
    ]
    row_html = "".join(
        f'<div class="scope-row"><dt>{escape(label)}</dt><dd class="breakable">{escape(value)}</dd></div>'
        for label, value in rows
    )
    limits = coverage["limitations"]
    limit_html = ""
    if limits:
        limit_html = (
            '<div class="scope-limit"><h3>限制與未確認事項</h3><ul>'
            + "".join(f"<li class=\"breakable\">{escape(item)}</li>" for item in limits)
            + "</ul></div>"
        )
    return (
        '<section class="coverage page" id="coverage" aria-labelledby="coverage-title">'
        '<h2 id="coverage-title">閱讀範圍</h2>'
        f'<p class="book-intro">{escape(data["book_introduction"])}</p>'
        f'<dl class="scope-list">{row_html}</dl>{limit_html}</section>'
    )


def render_source_refs(item):
    source_ids = item.get("source_ids") or []
    links = "、".join(
        f'<a href="#source-{safe_anchor(source_id)}">[{escape(source_id)}]</a>' for source_id in source_ids
    )
    attribution = "分析者推論" if item.get("analysis_type") == "analyst_inference" else "來源主張"
    if links:
        return f'<p class="source-ref">{attribution} · 依據 {links}</p>'
    return f'<p class="source-ref">{attribution}</p>'


def render_arguments(arguments):
    parts = []
    for argument in arguments:
        parts.append(
            '<article class="argument">'
            f'<h3>{escape(argument.get("title"))}</h3>'
            f'<div class="prose">{render_rich_text(argument.get("body"))}</div>'
            f'{render_source_refs(argument)}'
            "</article>"
        )
    return "".join(parts)


def render_concepts(concepts, relations):
    parts = []
    for concept in concepts:
        boundary = concept.get("boundary")
        boundary_html = f'<p class="concept-boundary">適用邊界：{escape(boundary)}</p>' if boundary else ""
        parts.append(
            '<article class="concept">'
            f'<h3>{escape(concept.get("name"))}</h3>'
            f'<p>{escape(concept.get("definition"))}</p>{boundary_html}'
            "</article>"
        )
    relation_html = ""
    valid_relations = [item for item in relations if isinstance(item, dict)]
    if valid_relations:
        relation_html = (
            '<div class="relations" aria-labelledby="relations-title"><h3 id="relations-title">概念關係</h3><ul>'
            + "".join(
                f'<li><strong>{escape(item.get("from"))}</strong> '
                f'{escape(item.get("relation"))} <strong>{escape(item.get("to"))}</strong></li>'
                for item in valid_relations
            )
            + "</ul></div>"
        )
    return relation_html + '<div class="concept-list">' + "".join(parts) + "</div>"


def render_critical(items):
    return "".join(
        '<article class="critical-item">'
        f'<h3>{escape(item.get("title"))}</h3>'
        f'<div class="prose">{render_rich_text(item.get("content"))}</div>'
        f'{render_source_refs(item)}'
        "</article>"
        for item in items
    )


def render_tips(tips):
    parts = []
    for key in ("T", "I", "P", "S"):
        item = tips[key]
        status = item["status"]
        value = f'{item["score"]} / 3' if status == "assessed" else TIP_STATUS_LABELS[status]
        parts.append(
            '<article class="tip-item">'
            f'<div class="tip-item__heading"><h3>{TIP_LABELS[key]}</h3><p>{escape(value)}</p></div>'
            f'<p>{escape(item["reason"])}</p>'
            "</article>"
        )
    return '<div class="tips-list">' + "".join(parts) + "</div>"


def render_quotes(quotes):
    parts = []
    for quote in quotes:
        source_link = (
            f'<a href="#source-{safe_anchor(quote["source_id"])}">[{escape(quote["source_id"])}]</a>'
        )
        location = escape(quote["location"])
        if quote["quote_type"] == "direct":
            translation = quote.get("translation")
            translation_html = (
                f'<p class="quote-translation"><span>翻譯</span>{escape(translation)}</p>'
                if translation
                else ""
            )
            parts.append(
                '<blockquote class="quote">'
                '<p class="quote-kind">原文引句</p>'
                f'<p class="quote-original">{escape(quote["original_text"])}</p>'
                f'{translation_html}<footer>{source_link} · <span class="breakable">{location}</span></footer>'
                "</blockquote>"
            )
        else:
            parts.append(
                '<div class="paraphrase">'
                '<p class="quote-kind">轉述</p>'
                f'<p>{escape(quote["paraphrase"])}</p>'
                f'<p class="source-ref">{source_link} · <span class="breakable">{location}</span></p>'
                "</div>"
            )
    return "".join(parts)


def render_actions(actions):
    parts = []
    for action in actions:
        metadata = [action.get("when"), action.get("context"), action.get("action")]
        metadata_html = "".join(f"<li>{escape(item)}</li>" for item in metadata if item)
        parts.append(
            '<article class="action-item">'
            f'<h3>{escape(action.get("title"))}</h3>'
            f'<p>{escape(action.get("description"))}</p>'
            f'<ul>{metadata_html}</ul>'
            "</article>"
        )
    return '<div class="action-list">' + "".join(parts) + "</div>"


def render_meta(items):
    return "".join(
        '<article class="meta-item">'
        f'<h3>{escape(item.get("lens"))}</h3>'
        f'<p>{escape(item.get("description"))}</p>'
        f'<p class="meta-delta">可能改變的理解：{escape(item.get("delta"))}</p>'
        "</article>"
        for item in items
    )


def render_zettels(items):
    labels = {"fleeting": "暫記", "literature": "文獻筆記", "permanent": "概念筆記"}
    return "<ul class=\"knowledge-list\">" + "".join(
        '<li>'
        f'<span class="knowledge-type">{escape(labels.get(item.get("type"), item.get("type")))}</span> '
        f'<strong>{escape(item.get("concept"))}</strong>：{escape(item.get("reason"))}'
        + (f' <span class="knowledge-link">連到 {escape(item.get("links_to"))}</span>' if item.get("links_to") else "")
        + "</li>"
        for item in items
    ) + "</ul>"


def render_sources(sources):
    parts = []
    for source in sources:
        url = safe_url(source.get("url"))
        title = escape(source["title"])
        title_html = f'<a class="breakable" href="{escape(url)}">{title}</a>' if url else title
        edition = f' · {escape(source.get("edition"))}' if source.get("edition") else ""
        locations = "、".join(source["locations"])
        parts.append(
            f'<li id="source-{safe_anchor(source["id"])}">'
            f'<span class="source-id">[{escape(source["id"])}]</span> '
            f'<strong>{title_html}</strong>{edition}'
            f'<p class="breakable">位置：{escape(locations)}</p></li>'
        )
    return '<ol class="source-list">' + "".join(parts) + "</ol>"


def render_further_reading(items):
    return "".join(
        '<article class="further-item">'
        f'<h3>{escape(item.get("title"))}</h3><p>{escape(item.get("reason"))}</p>'
        "</article>"
        for item in items
    )


def make_section(section_id, title, content):
    if not content:
        return None
    return {
        "id": section_id,
        "title": title,
        "html": (
            f'<section class="section" id="{section_id}" aria-labelledby="{section_id}-title">'
            f'<h2 id="{section_id}-title">{escape(title)}</h2>{content}'
            '<p class="back-link"><a href="#report-toc">回到目錄</a></p></section>'
        ),
    }


def build_sections(data):
    sections = []
    if data["core_arguments"]:
        sections.append(make_section("core-analysis", "核心分析", render_arguments(data["core_arguments"])))
    if data["key_concepts"] or data["concept_relations"]:
        sections.append(
            make_section(
                "concepts",
                "概念與關係",
                render_concepts(data["key_concepts"], data["concept_relations"]),
            )
        )
    if data["critical_perspectives"]:
        title = "詮釋與其他讀法" if data["reading_lens"] == "literature" else "批判與替代解釋"
        sections.append(make_section("critical", title, render_critical(data["critical_perspectives"])))
    sections.append(make_section("tips", "TIPS 分項評估", render_tips(data["tips_scores"])))
    if data["quotes"]:
        sections.append(make_section("quotes", "引述與轉述", render_quotes(data["quotes"])))
    if data["actions"]:
        sections.append(make_section("applications", "候選應用", render_actions(data["actions"])))
    if data["meta_knowledge"]:
        sections.append(make_section("mental-models", "可遷移的理解", render_meta(data["meta_knowledge"])))
    if data["zettelkasten"]:
        sections.append(make_section("knowledge-links", "知識連結", render_zettels(data["zettelkasten"])))
    if data["sources"]:
        sections.append(make_section("sources", "來源", render_sources(data["sources"])))
    if data["further_reading"]:
        sections.append(make_section("further-reading", "延伸閱讀", render_further_reading(data["further_reading"])))
    return [section for section in sections if section]


def build_toc(sections):
    return (
        '<nav class="toc page" id="report-toc" aria-labelledby="toc-title">'
        '<h2 id="toc-title">本頁目錄</h2><ol>'
        + "".join(f'<li><a href="#{section["id"]}">{escape(section["title"])}</a></li>' for section in sections)
        + "</ol></nav>"
    )


def build_markdown(data):
    coverage = data["coverage"]
    lines = [
        f'# {data["book_title"]}',
        f'**報告模式：{MODE_LABELS[data["report_mode"]]} · {data["book_type_tag"]}**',
        f'作者：{data.get("book_author") or "未確認"}',
        "",
        data["one_line_review"],
        "",
        "## 閱讀範圍",
        data["book_introduction"],
        f'- 要求範圍：{coverage["requested_scope"]}',
        f'- 已讀位置：{"、".join(coverage["read_locations"]) or "未取得可讀內容"}',
        f'- 未讀位置：{"、".join(coverage["unread_locations"]) or "無"}',
        f'- 失敗位置：{"、".join(coverage["failed_locations"]) or "無"}',
        f'- 依據類型：{"、".join(SOURCE_BASIS_LABELS.get(item, item) for item in coverage["source_basis"])}',
    ]
    if coverage["limitations"]:
        lines.extend(["- 限制：" + "；".join(coverage["limitations"]), ""])

    if data["core_arguments"]:
        lines.extend(["## 核心分析", ""])
        for item in data["core_arguments"]:
            lines.extend(
                [
                    f'### {item["title"]}',
                    plain_text(item["body"]),
                    "歸屬：" + ("分析者推論" if item.get("analysis_type") == "analyst_inference" else "來源主張"),
                    "依據：" + ("、".join(item.get("source_ids") or []) or "無外部來源"),
                    "",
                ]
            )

    if data["key_concepts"] or data["concept_relations"]:
        lines.extend(["## 概念與關係", ""])
        for item in data["key_concepts"]:
            lines.extend([f'### {item["name"]}', item["definition"]])
            if item.get("boundary"):
                lines.append(f'適用邊界：{item["boundary"]}')
            lines.append("")
        for item in data["concept_relations"]:
            lines.append(f'- **{item["from"]}** {item["relation"]} **{item["to"]}**')
        if data["concept_relations"]:
            lines.append("")

    if data["critical_perspectives"]:
        heading = "詮釋與其他讀法" if data["reading_lens"] == "literature" else "批判與替代解釋"
        lines.extend([f"## {heading}", ""])
        for item in data["critical_perspectives"]:
            lines.extend(
                [
                    f'### {item["title"]}',
                    plain_text(item["content"]),
                    "歸屬：" + (
                        "分析者推論" if item.get("analysis_type") == "analyst_inference" else "來源主張"
                    ),
                    "依據：" + ("、".join(item.get("source_ids") or []) or "無外部來源"),
                    "",
                ]
            )

    lines.extend(["## TIPS 分項評估", ""])
    for key in ("T", "I", "P", "S"):
        item = data["tips_scores"][key]
        value = f'{item["score"]}/3' if item["status"] == "assessed" else TIP_STATUS_LABELS[item["status"]]
        lines.append(f'- **{TIP_LABELS[key]}：{value}** — {item["reason"]}')
    lines.append("")

    if data["quotes"]:
        lines.extend(["## 引述與轉述", ""])
        for quote in data["quotes"]:
            if quote["quote_type"] == "direct":
                lines.append(f'> {quote["original_text"]}')
                if quote.get("translation"):
                    lines.append(f'> 翻譯：{quote["translation"]}')
            else:
                lines.append(f'- 轉述：{quote["paraphrase"]}')
            lines.append(f'  來源：{quote["source_id"]} · {quote["location"]}')
        lines.append("")

    if data["actions"]:
        lines.extend(["## 候選應用", ""])
        for item in data["actions"]:
            lines.append(f'- **{item.get("title", "")}**：{item.get("description", "")}')
            for label, field in (("時機", "when"), ("情境", "context"), ("行動", "action")):
                if item.get(field):
                    lines.append(f'  - {label}：{item[field]}')
        lines.append("")

    if data["meta_knowledge"]:
        lines.extend(["## 可遷移的理解", ""])
        for item in data["meta_knowledge"]:
            lines.extend(
                [
                    f'### {item["lens"]}',
                    item["description"],
                    f'可能改變的理解：{item["delta"]}',
                    "",
                ]
            )

    if data["zettelkasten"]:
        zettel_labels = {"fleeting": "暫記", "literature": "文獻筆記", "permanent": "概念筆記"}
        lines.extend(["## 知識連結", ""])
        for item in data["zettelkasten"]:
            link = f' · 連到 {item["links_to"]}' if item.get("links_to") else ""
            lines.append(
                f'- **{zettel_labels.get(item["type"], item["type"])} · {item["concept"]}**：'
                f'{item["reason"]}{link}'
            )
        lines.append("")

    if data["sources"]:
        lines.extend(["## 來源", ""])
        for source in data["sources"]:
            locations = "、".join(source["locations"])
            edition = f' · {source.get("edition")}' if source.get("edition") else ""
            url = f' · {source.get("url")}' if safe_url(source.get("url")) else ""
            lines.append(f'- [{source["id"]}] {source["title"]}{edition} · 位置：{locations}{url}')
        lines.append("")

    if data["further_reading"]:
        lines.extend(["## 延伸閱讀", ""])
        for item in data["further_reading"]:
            lines.append(f'- **{item["title"]}**：{item["reason"]}')
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render(data, template_text):
    errors = validate_report(data)
    if errors:
        raise ReportValidationError(errors)

    sections = build_sections(data)
    markdown = build_markdown(data)
    replacements = {
        "{{BOOK_TITLE}}": escape(data["book_title"]),
        "{{BOOK_AUTHOR}}": render_author(data),
        "{{ONE_LINE_REVIEW}}": escape(data["one_line_review"]),
        "{{BOOK_TYPE_TAG}}": escape(data["book_type_tag"]),
        "{{REPORT_MODE}}": escape(MODE_LABELS[data["report_mode"]]),
        "{{COVERAGE_HTML}}": render_coverage(data),
        "{{TOC_HTML}}": build_toc(sections),
        "{{REPORT_SECTIONS_HTML}}": "".join(section["html"] for section in sections),
        "{{REPORT_MARKDOWN}}": escape(markdown),
        "{{DOWNLOAD_FILENAME}}": escape(f'reading-report-{data["slug"]}.md'),
        "{{GENERATION_DATE}}": escape(data.get("generation_date", date.today().isoformat())),
    }
    result = template_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def load_data(input_name):
    if input_name == "-":
        return json.loads(sys.stdin.read())
    input_path = Path(input_name)
    if not input_path.is_file():
        raise FileNotFoundError(f"找不到：{input_name}")
    return json.loads(input_path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="CRISP Reading：HTML 報告渲染")
    parser.add_argument("input", help="分析結果 JSON 檔案路徑，或 - 從 stdin 讀取")
    parser.add_argument("--output", "-o", help="輸出 HTML 路徑")
    parser.add_argument("--template", "-t", help="自訂模板路徑（預設使用內建模板）")
    parser.add_argument("--validate", action="store_true", help="只驗證 JSON，不產生 HTML")
    args = parser.parse_args()

    try:
        data = load_data(args.input)
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    errors = validate_report(data)
    if args.validate:
        print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
        sys.exit(0 if not errors else 2)
    if errors:
        print(json.dumps({"success": False, "errors": errors}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)

    template_path = Path(args.template) if args.template else TEMPLATE_PATH
    if not template_path.is_file():
        print(
            json.dumps({"success": False, "error": f"找不到模板：{template_path}"}, ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(1)

    html_output = render(data, template_path.read_text(encoding="utf-8"))
    output_path = Path(args.output) if args.output else Path.cwd() / f'reading-report-{data["slug"]}.html'
    output_path.write_text(html_output, encoding="utf-8")
    print(json.dumps({"success": True, "output_path": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
