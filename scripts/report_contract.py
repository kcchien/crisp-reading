"""Executable data contract for CRISP Reading reports."""

from typing import Any, Dict, List, Set


REPORT_MODES = {"full", "preliminary", "quick", "notes"}
READING_LENSES = {"nonfiction", "literature", "mixed"}
TIP_STATUSES = {"assessed", "unknown", "not_applicable"}
SOURCE_BASIS = {"full_text", "partial_text", "reader_notes", "public_metadata", "none"}
ANALYSIS_TYPES = {"source_claim", "analyst_inference"}
QUOTE_TYPES = {"direct", "paraphrase"}
ZETTEL_TYPES = {"fleeting", "literature", "permanent"}

REQUIRED_ROOT_FIELDS = (
    "slug",
    "book_title",
    "book_author",
    "book_type_tag",
    "report_mode",
    "reading_lens",
    "one_line_review",
    "book_introduction",
    "coverage",
    "sources",
    "tips_scores",
    "core_arguments",
    "key_concepts",
    "concept_relations",
    "critical_perspectives",
    "quotes",
    "actions",
    "zettelkasten",
    "meta_knowledge",
    "further_reading",
)

LIST_FIELDS = (
    "sources",
    "core_arguments",
    "key_concepts",
    "concept_relations",
    "critical_perspectives",
    "quotes",
    "actions",
    "zettelkasten",
    "meta_knowledge",
    "further_reading",
)


def _error(errors: List[Dict[str, str]], path: str, code: str, message: str) -> None:
    errors.append({"path": path, "code": code, "message": message})


def _require_text(
    errors: List[Dict[str, str]], data: Dict[str, Any], key: str, path: str = ""
) -> None:
    value = data.get(key)
    field_path = f"{path}.{key}" if path else key
    if not isinstance(value, str) or not value.strip():
        _error(errors, field_path, "required", "必須提供非空白文字")


def _validate_string_list(
    errors: List[Dict[str, str]], value: Any, path: str, allow_empty: bool = True
) -> None:
    if not isinstance(value, list):
        _error(errors, path, "type", "必須是陣列")
        return
    if not allow_empty and not value:
        _error(errors, path, "required", "至少需要一項")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            _error(errors, f"{path}.{index}", "type", "必須是非空白文字")


def _validate_coverage(errors: List[Dict[str, str]], coverage: Any) -> None:
    if not isinstance(coverage, dict):
        _error(errors, "coverage", "type", "必須是物件")
        return
    _require_text(errors, coverage, "requested_scope", "coverage")
    for key in ("read_locations", "unread_locations", "failed_locations", "limitations"):
        _validate_string_list(errors, coverage.get(key), f"coverage.{key}")
    basis = coverage.get("source_basis")
    _validate_string_list(errors, basis, "coverage.source_basis", allow_empty=False)
    if isinstance(basis, list):
        for index, item in enumerate(basis):
            if isinstance(item, str) and item not in SOURCE_BASIS:
                _error(
                    errors,
                    f"coverage.source_basis.{index}",
                    "enum",
                    f"必須是 {sorted(SOURCE_BASIS)} 之一",
                )
        if "none" in basis and len(basis) != 1:
            _error(
                errors,
                "coverage.source_basis",
                "inconsistent_coverage",
                "none 必須單獨使用，不能與已取得的來源類型並列",
            )
        if "none" in basis and coverage.get("read_locations"):
            _error(
                errors,
                "coverage.read_locations",
                "inconsistent_coverage",
                "未取得可查閱材料時不可宣稱已讀位置",
            )


def _validate_sources(errors: List[Dict[str, str]], sources: Any) -> Set[str]:
    if not isinstance(sources, list):
        return set()
    seen: Set[str] = set()
    for index, source in enumerate(sources):
        path = f"sources.{index}"
        if not isinstance(source, dict):
            _error(errors, path, "type", "來源必須是物件")
            continue
        for key in ("id", "type", "title"):
            _require_text(errors, source, key, path)
        source_id = source.get("id")
        if isinstance(source_id, str) and source_id.strip():
            if source_id in seen:
                _error(errors, f"{path}.id", "duplicate", "來源 id 不可重複")
            seen.add(source_id)
        _validate_string_list(errors, source.get("locations"), f"{path}.locations", allow_empty=False)
    return seen


def _validate_tips(errors: List[Dict[str, str]], tips: Any) -> None:
    if not isinstance(tips, dict):
        _error(errors, "tips_scores", "type", "必須是物件")
        return
    for forbidden in ("total", "verdict"):
        if forbidden in tips:
            _error(errors, f"tips_scores.{forbidden}", "forbidden", "新版契約不允許總分或固定等級")
    for dimension in ("T", "I", "P", "S"):
        path = f"tips_scores.{dimension}"
        item = tips.get(dimension)
        if not isinstance(item, dict):
            _error(errors, path, "required", "每個 TIPS 維度都必須提供物件")
            continue
        status = item.get("status")
        score = item.get("score")
        reason = item.get("reason")
        if status not in TIP_STATUSES:
            _error(errors, f"{path}.status", "enum", f"必須是 {sorted(TIP_STATUSES)} 之一")
        if not isinstance(reason, str) or not reason.strip():
            _error(errors, f"{path}.reason", "required", "必須說明評估或無法評估的理由")
        if status == "assessed":
            if not isinstance(score, int) or isinstance(score, bool) or score not in (1, 2, 3):
                _error(errors, f"{path}.score", "status_score_mismatch", "assessed 必須有 1–3 分")
        elif status in {"unknown", "not_applicable"} and score is not None:
            _error(errors, f"{path}.score", "status_score_mismatch", f"{status} 的 score 必須是 null")


def _validate_claims(
    errors: List[Dict[str, str]], claims: Any, path: str, source_ids: Set[str]
) -> None:
    if not isinstance(claims, list):
        return
    for index, claim in enumerate(claims):
        item_path = f"{path}.{index}"
        if not isinstance(claim, dict):
            _error(errors, item_path, "type", "內容項目必須是物件")
            continue
        _require_text(errors, claim, "title", item_path)
        _require_text(
            errors,
            claim,
            "body" if path == "core_arguments" else "content",
            item_path,
        )
        analysis_type = claim.get("analysis_type")
        if analysis_type not in ANALYSIS_TYPES:
            _error(errors, f"{item_path}.analysis_type", "enum", f"必須是 {sorted(ANALYSIS_TYPES)} 之一")
        refs = claim.get("source_ids")
        if analysis_type == "source_claim" and (not isinstance(refs, list) or not refs):
            _error(errors, f"{item_path}.source_ids", "required", "來源主張至少需要一個 source id")
        if refs is not None:
            _validate_string_list(errors, refs, f"{item_path}.source_ids")
            if isinstance(refs, list):
                for ref_index, source_id in enumerate(refs):
                    if isinstance(source_id, str) and source_id not in source_ids:
                        _error(
                            errors,
                            f"{item_path}.source_ids.{ref_index}",
                            "unresolved_source",
                            "找不到對應來源 id",
                        )


def _validate_quotes(errors: List[Dict[str, str]], quotes: Any, source_ids: Set[str]) -> None:
    if not isinstance(quotes, list):
        return
    for index, quote in enumerate(quotes):
        path = f"quotes.{index}"
        if not isinstance(quote, dict):
            _error(errors, path, "type", "引述必須是物件")
            continue
        quote_type = quote.get("quote_type")
        if quote_type not in QUOTE_TYPES:
            _error(errors, f"{path}.quote_type", "enum", f"必須是 {sorted(QUOTE_TYPES)} 之一")
        if quote_type == "direct":
            _require_text(errors, quote, "original_text", path)
            translation = quote.get("translation")
            if translation is not None and not isinstance(translation, str):
                _error(errors, f"{path}.translation", "type", "翻譯必須是文字或 null")
        if quote_type == "paraphrase":
            _require_text(errors, quote, "paraphrase", path)
        _require_text(errors, quote, "location", path)
        source_id = quote.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            _error(errors, f"{path}.source_id", "required", "引述必須指向來源")
        elif source_id not in source_ids:
            _error(errors, f"{path}.source_id", "unresolved_source", "找不到對應來源 id")


def _validate_object_items(
    errors: List[Dict[str, str]],
    items: Any,
    path: str,
    required_fields: tuple,
    optional_text_fields: tuple = (),
) -> None:
    if not isinstance(items, list):
        return
    for index, item in enumerate(items):
        item_path = f"{path}.{index}"
        if not isinstance(item, dict):
            _error(errors, item_path, "type", "內容項目必須是物件")
            continue
        for field in required_fields:
            _require_text(errors, item, field, item_path)
        for field in optional_text_fields:
            value = item.get(field)
            if value is not None and not isinstance(value, str):
                _error(errors, f"{item_path}.{field}", "type", "必須是文字或省略")


def _validate_zettels(errors: List[Dict[str, str]], items: Any) -> None:
    _validate_object_items(errors, items, "zettelkasten", ("type", "concept", "reason"), ("links_to",))
    if not isinstance(items, list):
        return
    for index, item in enumerate(items):
        if isinstance(item, dict) and item.get("type") not in ZETTEL_TYPES:
            _error(
                errors,
                f"zettelkasten.{index}.type",
                "enum",
                f"必須是 {sorted(ZETTEL_TYPES)} 之一",
            )


def validate_report(data: dict) -> list:
    """Return structured validation errors; an empty list means valid."""
    errors: List[Dict[str, str]] = []
    if not isinstance(data, dict):
        _error(errors, "$", "type", "報告根節點必須是物件")
        return errors

    for field in REQUIRED_ROOT_FIELDS:
        if field not in data:
            _error(errors, field, "required", "缺少必要欄位")

    for field in ("slug", "book_title", "book_type_tag", "one_line_review", "book_introduction"):
        if field in data:
            _require_text(errors, data, field)
    if "book_author" in data and data["book_author"] is not None and not isinstance(data["book_author"], str):
        _error(errors, "book_author", "type", "作者必須是文字或 null")

    if data.get("report_mode") not in REPORT_MODES:
        _error(errors, "report_mode", "enum", f"必須是 {sorted(REPORT_MODES)} 之一")
    if data.get("reading_lens") not in READING_LENSES:
        _error(errors, "reading_lens", "enum", f"必須是 {sorted(READING_LENSES)} 之一")

    for field in LIST_FIELDS:
        if field in data and not isinstance(data[field], list):
            _error(errors, field, "type", "必須是陣列")

    _validate_coverage(errors, data.get("coverage"))
    known_source_ids = _validate_sources(errors, data.get("sources"))
    _validate_tips(errors, data.get("tips_scores"))
    _validate_claims(errors, data.get("core_arguments"), "core_arguments", known_source_ids)
    _validate_claims(errors, data.get("critical_perspectives"), "critical_perspectives", known_source_ids)
    _validate_quotes(errors, data.get("quotes"), known_source_ids)
    _validate_object_items(errors, data.get("key_concepts"), "key_concepts", ("name", "definition"), ("boundary",))
    _validate_object_items(errors, data.get("concept_relations"), "concept_relations", ("from", "relation", "to"))
    _validate_object_items(
        errors,
        data.get("actions"),
        "actions",
        ("title", "description"),
        ("when", "context", "action"),
    )
    _validate_object_items(
        errors,
        data.get("meta_knowledge"),
        "meta_knowledge",
        ("lens", "description", "delta"),
    )
    _validate_zettels(errors, data.get("zettelkasten"))
    _validate_object_items(errors, data.get("further_reading"), "further_reading", ("title", "reason"))

    if data.get("report_mode") == "full":
        coverage = data.get("coverage")
        if isinstance(coverage, dict) and not coverage.get("read_locations"):
            _error(errors, "coverage.read_locations", "full_requires_coverage", "完整報告必須列出已讀位置")
        if isinstance(coverage, dict):
            for field in ("unread_locations", "failed_locations"):
                if coverage.get(field):
                    _error(
                        errors,
                        f"coverage.{field}",
                        "full_requires_complete_coverage",
                        "完整深讀不可包含要求範圍內的未讀或提取失敗位置；請改用 preliminary",
                    )
            basis = coverage.get("source_basis")
            if isinstance(basis, list) and "full_text" not in basis:
                _error(
                    errors,
                    "coverage.source_basis",
                    "full_requires_complete_coverage",
                    "完整深讀的依據類型必須包含 full_text",
                )
        if isinstance(data.get("sources"), list) and not data["sources"]:
            _error(errors, "sources", "full_requires_sources", "完整報告必須有可回查來源")
        if isinstance(data.get("core_arguments"), list) and not data["core_arguments"]:
            _error(errors, "core_arguments", "full_requires_analysis", "完整報告必須交代主要內容")

    return errors
