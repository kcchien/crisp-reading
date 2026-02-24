# 分析 JSON Schema

> Claude 分析完成後，依此結構產出 JSON，交由 render-report.py 渲染為 HTML。

```json
{
  "slug": "almanack-of-naval",           // 用於檔名
  "book_title": "納瓦爾寶典（The Almanack of Naval Ravikant）",
  "book_author": "Eric Jorgenson",
  "book_author_zh": "艾瑞克·乔根森",    // 作者中文譯名（選填，有公認譯名時填寫）
  "book_type_tag": "自我成長",            // 書型標籤（見 analysis.md 書型分類）
  "one_line_review": "一句話評價（15-25 字）",
  "book_introduction": "書籍簡介（3-5 句），涵蓋主題、作者背景、書的定位",

  "tips_scores": {
    "T": 2,
    "I": 3,
    "P": 2,
    "S": 1,
    "total": 8,
    "verdict": "好書"
  },

  "core_arguments": [
    {
      "title": "論點標題",
      "body": "論點說明文字，純文字或含 inline HTML（如 <strong>、<em>）。render-report.py 會自動偵測 HTML 標籤"
    }
  ],

  "key_concepts": [
    {
      "name": "概念名稱",
      "definition": "白話解釋",
      "boundary": "適用條件與失效邊界（選填，僅在概念有明確邊界時填寫）"
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
      "reason": "為什麼連結",
      "links_to": "連結到哪本書或哪個知識體系（選填）"
    }
  ],

  "meta_knowledge": [
    {
      "lens": "思維模型名稱",
      "description": "這個模型怎麼用、能看到什麼",
      "delta": "讀完前後，你對這件事的理解有什麼不同"
    }
  ],

  "further_reading": [
    {
      "title": "《窮查理的普通常識》（Poor Charlie's Almanack）— Charlie Munger",
      "reason": "為什麼推薦"
    }
  ]
}
```

## 欄位說明

| 欄位 | 必填 | 說明 |
|------|------|------|
| slug | ✅ | 英文 kebab-case，用於輸出檔名 |
| book_title | ✅ | 書名。英文書有中文譯名時用「中文書名（原文）」格式，如「納瓦爾寶典（The Almanack of Naval Ravikant）」；無譯名則用原文；中文書直接用中文書名 |
| book_author | ✅ | 作者原文名 |
| book_author_zh | 選填 | 作者中文譯名。有公認中文譯名時填寫；render-report.py 會自動組合為「中文譯名（原文名）」格式顯示 |
| book_type_tag | ✅ | 書型標籤（如「理論思想」「工具技術」） |
| one_line_review | ✅ | 一句話評價，15-25 字 |
| book_introduction | ✅ | 書籍簡介（3-5 句），涵蓋主題、作者背景、書的定位。顯示在 HTML 報告 header 下方 |
| tips_scores | ✅ | TIPS 四維度評分（T/I/P/S 各 1-3 分）、total、verdict（總分解讀） |
| core_arguments | ✅ | 全書 3-7 個核心論點 |
| key_concepts | ✅ | 關鍵概念列表 |
| concept_relations_svg | 選填 | 內嵌 SVG（見 design-spec.md 配色規範） |
| critical_perspectives | ✅ | 批判視角，可為陣列或純字串 |
| quotes | ✅ | 精選引句（3-5 則） |
| actions | ✅ | 行動承諾（3-5 個），需含 when/context/action |
| zettelkasten | ✅ | 知識連結筆記 |
| zettelkasten[].links_to | 選填 | 跨書或跨領域的連結點（僅 permanent 類型建議填寫） |
| meta_knowledge | ✅ | 可跨域遷移的思維模型，2-4 筆。每筆含 lens（模型名稱）、description（怎麼用）、delta（認知變化） |
| key_concepts[].boundary | 選填 | 概念的適用條件與失效邊界（僅在概念有明確邊界時填寫） |
| further_reading | ✅ | 延伸閱讀推薦。title 格式：「《中文書名》（原文）— 作者」，如「《窮查理的普通常識》（Poor Charlie's Almanack）— Charlie Munger」；無中文譯名則用原文 |

「選填」欄位在資訊不足時可省略；render-report.py 會自動處理空值。
