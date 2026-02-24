# 分析 JSON Schema

> Claude 分析完成後，依此結構產出 JSON，交由 render-report.py 渲染為 HTML。

```json
{
  "slug": "almanack-of-naval",           // 用於檔名
  "book_title": "納瓦爾寶典",
  "book_author": "Eric Jorgenson",
  "book_type_tag": "自我成長",            // 書型標籤（見 analysis.md 書型分類）
  "one_line_review": "一句話評價（15-25 字）",

  "tips_scores": {
    "T": 2,
    "I": 3,
    "P": 2,
    "S": 1,
    "total": 8,
    "verdict": "好書，標準分析流程"
  },

  "core_arguments": [
    {
      "title": "論點標題",
      "body": "論點說明文字，純文字或 HTML（若含 HTML 須以 < 開頭，否則會被 escape）"
    }
  ],

  "key_concepts": [
    {
      "name": "概念名稱",
      "definition": "白話解釋"
    }
  ],

  "concept_relations_svg": "<svg>...</svg>",  // 概念關係圖（可選，見 design-spec.md SVG 配色）

  "critical_perspectives": [
    {
      "title": "批判面向標題",
      "content": "批判內容（純文字或 HTML）"
    }
  ],

  "quotes": [
    {
      "text": "引句內容（英文書附中文翻譯）",
      "source": "來源（章節/頁碼）"
    }
  ],

  "actions": [
    {
      "title": "行動標題",
      "description": "行動說明",
      "when": "時間",
      "context": "場景",
      "action": "具體做法"
    }
  ],

  "zettelkasten": [
    {
      "type": "permanent",           // "fleeting" | "literature" | "permanent"
      "concept": "概念名稱",
      "reason": "為什麼連結"
    }
  ],

  "further_reading": [
    {
      "title": "書名 — 作者",
      "reason": "為什麼推薦"
    }
  ]
}
```

## 欄位說明

| 欄位 | 必填 | 深度 | 說明 |
|------|------|------|------|
| slug | ✅ | — | 英文 kebab-case，用於輸出檔名 |
| book_title | ✅ | 全部 | 書名 |
| book_author | ✅ | 全部 | 作者 |
| book_type_tag | ✅ | 全部 | 書型標籤（如「理論思想」「工具技術」） |
| one_line_review | ✅ | 全部 | 一句話評價，15-25 字 |
| tips_scores | ✅ | 全部 | TIPS 四維度評分（T/I/P/S 各 1-3 分）、total、verdict（總分解讀） |
| core_arguments | ✅ | 精華版 | 全書 3-7 個核心論點 |
| key_concepts | ✅ | 精華版 | 關鍵概念列表 |
| concept_relations_svg | 選填 | 完整版 | 內嵌 SVG（見 design-spec.md 配色規範） |
| critical_perspectives | 選填 | 完整版 | 批判視角，可為陣列或純字串 |
| quotes | ✅ | 精華版 | 精選引句（3-5 則） |
| actions | ✅ | 精華版 | 行動承諾（3-5 個），需含 when/context/action |
| zettelkasten | 選填 | 完整版 | 知識連結筆記 |
| further_reading | 選填 | 完整版 | 延伸閱讀推薦 |

「選填」欄位在快速評估或資訊不足時可省略；render-report.py 會自動處理空值。
