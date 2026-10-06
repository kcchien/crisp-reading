# CRISP 報告資料契約

`scripts/report_contract.py` 的 `validate_report(data)` 是可執行的契約權威；本文件說明模型應產出的資料，不另建立一套可能漂移的規則。產出後先執行：

```bash
python scripts/render-report.py analysis.json --validate
python scripts/render-report.py analysis.json -o reading-report.html
```

驗證錯誤包含 `path`、`code`、`message`。只有 `errors: []` 才能渲染；舊 JSON 缺欄位時補齊真實資料，不推測閱讀範圍或來源。

## 根層欄位

```json
{
  "slug": "book-slug",
  "book_title": "書名",
  "book_author": null,
  "book_type_tag": "使用者可讀的類型文字",
  "report_mode": "full",
  "reading_lens": "nonfiction",
  "one_line_review": "一句結論",
  "book_introduction": "依據與限制清楚的簡介",
  "coverage": {},
  "sources": [],
  "tips_scores": {},
  "core_arguments": [],
  "key_concepts": [],
  "concept_relations": [],
  "critical_perspectives": [],
  "quotes": [],
  "actions": [],
  "zettelkasten": [],
  "meta_knowledge": [],
  "further_reading": []
}
```

- `report_mode`：`full`、`preliminary`、`quick`、`notes`。部分閱讀以 `coverage` 表達，不冒充 full。
- `reading_lens`：`nonfiction`、`literature`、`mixed`。
- `book_author`：可為 `null`；未知就保留未知，不填猜測值。
- `sources` 及各內容陣列即使為空也要明列，讓「無資料」與「忘了產出」可區分。
- `full` 必須有已讀位置、可回查來源及主要分析；其他模式仍需說明實際依據。

## 閱讀範圍

```json
{
  "coverage": {
    "requested_scope": "使用者要求的範圍",
    "read_locations": ["第一章", "第二章"],
    "unread_locations": ["第三章"],
    "failed_locations": [],
    "source_basis": ["partial_text"],
    "limitations": ["未提供第三章"]
  }
}
```

`source_basis` 可用值：`full_text`、`partial_text`、`reader_notes`、`public_metadata`、`none`。模型既有知識不是已查閱的公開資料；若只有書名且未查到資料，使用 `none`。`none` 必須單獨使用，且此時 `read_locations` 必須為空。`report_mode: full` 必須包含 `full_text`，且 `unread_locations`、`failed_locations` 都必須為空；否則應改用 `preliminary`，不可交付為完整深讀。

## 來源與論點歸屬

```json
{
  "sources": [
    {
      "id": "src-book",
      "type": "provided_text",
      "title": "書名或文件標題",
      "edition": "版本；未知可省略",
      "locations": ["第一章", "第二章"],
      "url": "https://example.org/source；沒有可省略"
    }
  ],
  "core_arguments": [
    {
      "title": "論點標題",
      "body": "論點說明",
      "analysis_type": "source_claim",
      "source_ids": ["src-book"]
    }
  ],
  "critical_perspectives": [
    {
      "title": "另一種解釋",
      "content": "這是分析者根據文本提出的詮釋。",
      "analysis_type": "analyst_inference",
      "source_ids": ["src-book"]
    }
  ]
}
```

來源 `id` 必須唯一。`source_claim` 至少指向一個有效 `source_id`；`analyst_inference` 明示為分析者推論，可列支撐來源，但不能寫成作者原意。來源位置要能讓讀者回查，不把章節索引當成 PDF 頁碼。

## TIPS

```json
{
  "tips_scores": {
    "T": {"score": 2, "status": "assessed", "reason": "有方法，但需自行轉化。"},
    "I": {"score": 2, "status": "assessed", "reason": "提供可辨識的新觀點。"},
    "P": {"score": null, "status": "unknown", "reason": "未提供讀者情境。"},
    "S": {"score": null, "status": "not_applicable", "reason": "小說不以實證論證為目的。"}
  }
}
```

- `assessed`：`score` 必須為 1–3，並說明理由。
- `unknown`、`not_applicable`：`score` 必須為 `null`，理由分別說明資訊不足或不適用。
- 不產出 `total`、`verdict`，也不把未知或不適用換算成低分。

## 引述

直接引述把原文、翻譯與位置分開：

```json
{
  "quote_type": "direct",
  "original_text": "Original wording",
  "translation": "繁體中文翻譯；不需要時為 null",
  "source_id": "src-book",
  "location": "第二章／PDF 實際第 31 頁"
}
```

轉述不能放進引號冒充原文：

```json
{
  "quote_type": "paraphrase",
  "paraphrase": "作者在此區分可逆與難以逆轉的決策。",
  "source_id": "src-book",
  "location": "第一章第一段"
}
```

`quotes` 可以是空陣列，不為湊數生成引句。無法定位的文字不要當引述交付。

## 選填內容與文學分支

`actions`、`quotes`、`zettelkasten`、`meta_knowledge`、`further_reading` 可以為空。沒有讀者情境時，`actions` 只能是明確標示的候選應用；文學作品不強制產出工具、科學性分數或行動。

`concept_relations` 使用結構化關係資料；renderer 負責產生安全 HTML，不接受任意模型生成的 SVG 或 script。

renderer 會顯示的物件都要提供對應欄位；不要用相似但未定義的鍵名：

```json
{
  "key_concepts": [
    {"name": "概念", "definition": "白話定義", "boundary": "可省略的適用邊界"}
  ],
  "concept_relations": [
    {"from": "概念 A", "relation": "限制", "to": "概念 B"}
  ],
  "actions": [
    {
      "title": "候選應用標題",
      "description": "為何值得嘗試",
      "when": "可省略的時間",
      "context": "可省略的情境",
      "action": "可省略的具體行為"
    }
  ],
  "meta_knowledge": [
    {"lens": "可遷移理解", "description": "連結機制", "delta": "可能改變的理解"}
  ],
  "zettelkasten": [
    {
      "type": "literature",
      "concept": "一則一概念",
      "reason": "為什麼重要",
      "links_to": "可省略；要含連結機制與關鍵差異"
    }
  ],
  "further_reading": [
    {"title": "下一份材料", "reason": "與本報告的具體關係"}
  ]
}
```

`zettelkasten[].type` 可用 `fleeting`、`literature`、`permanent`。選填文字欄位可以省略，但若存在就必須是文字；必要顯示欄位不可用空字串。

## 可執行範例

以下 fixture 都必須通過 `--validate`，並與契約測試一起維護：

- 非虛構完整報告：[`../tests/fixtures/nonfiction.json`](../tests/fixtures/nonfiction.json)
- 只有書名的 preliminary：[`../tests/fixtures/preliminary.json`](../tests/fixtures/preliminary.json)
- 文學完整報告：[`../tests/fixtures/literature.json`](../tests/fixtures/literature.json)
