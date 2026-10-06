<a id="top"></a>

<div align="center">

<img src="assets/cover.webp" alt="An open book moves through five analytical layers and becomes connected knowledge" width="100%" />

# CRISP Reading

**從可回查來源到可離線保存的深度閱讀報告。**<br />
*Evidence-aware deep reading, delivered as an offline HTML report.*

[繁體中文](#zh-tw) · [English](#en-us)

[![License: MIT](https://img.shields.io/badge/License-MIT-b08d57.svg?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-compatible-244b3b.svg?style=flat-square)](#安裝)
[![Python](https://img.shields.io/badge/Python-3.9+-315f4b.svg?style=flat-square&logo=python&logoColor=white)](#需求)
[![Output](https://img.shields.io/badge/Output-Offline_HTML-7a2736.svg?style=flat-square)](#html-閱讀體驗)

</div>

<a id="zh-tw"></a>

## 繁體中文（zh-TW）

**CRISP = Comprehend · Review · Internalize · Synthesize · Practice。**

CRISP Reading 是一個重視證據邊界的 AI 深度閱讀 skill。它先判斷使用者意圖與實際取得的材料，再選擇完整閱讀、指定範圍、快速評估、既有筆記深化或初步評估。它不會把每一種輸入都包裝成「完整深讀」。

最後交付的是一份自包含、可離線閱讀的繁體中文 HTML 報告。報告會清楚呈現已讀範圍、未讀或提取失敗的位置、引用來源與分析限制，讓每個重要判斷都能回到材料核對。

### 安裝

```bash
npx skills add kcchien/crisp-reading
```

任何能讀取 `SKILL.md` 的相容 agent 都可使用。這個 repository 版本需要 Python 3.9+。PDF fallback 需要 `pymupdf4llm`；PDF 結構資訊需要 PyMuPDF。若環境已有可用的文件轉 Markdown gateway，提取器會優先使用它。

### 使用方式

| 你說 | 技能如何處理 |
|---|---|
| 「幫我讀這本書」並附 PDF / EPUB | 提取要求範圍、完整分析、驗證資料、輸出 HTML |
| 「先讀前五章」 | 只把前五章當要求範圍，其他內容不猜測 |
| 「這本書值不值得讀？」 | 產出 `quick` 精簡評估 |
| 「我有筆記，幫我深化」 | 保留既有判斷，以筆記與可回查原文補強 |
| 只有書名 | 先尋找合法可用全文；找不到就交付 `preliminary`，不冒充完整閱讀 |
| 「只摘要這份文件」 | 不啟動完整 CRISP，依摘要需求處理 |

使用者明確不要 HTML 時會遵守；其他書籍閱讀模式預設交付 HTML。

### 報告會呈現什麼

- 報告模式與一句話結論。
- 閱讀範圍：要求、已讀、未讀、失敗位置、依據類型與限制。
- 連續章節的核心分析、概念關係、批判或其他詮釋。
- TIPS 四維度的個別分數／狀態與理由；沒有總分或固定「好書」等級。
- 有根據才顯示的引句、候選應用、知識連結與延伸閱讀。
- 可回查來源；來源主張與分析者推論分開標示。

文學作品使用敘事、人物、語言、意象與主題的專用分支，不強制科學性分數或行動計畫。沒有讀者情境時，應用只會標成候選，不會假裝讀者已內化或承諾。

### HTML 閱讀體驗

報告是自包含的單一 HTML 檔案，不需要伺服器或外部框架：

- 核心內容以連續章節呈現，頁內目錄只列出存在的區塊。
- 顯示來源位置、引句類型、TIPS 理由與未知／不適用狀態。
- 提供淺色／深色模式、複製 Markdown、下載 Markdown 與列印樣式。
- JavaScript 關閉時，正文與來源仍完整可讀。
- 長 URL 與寬表格不會讓整頁水平溢位；表格需要時局部捲動。
- Copy 失敗會顯示可手動選取的 Markdown，不會假報成功。

### 證據原則

1. 只有實際讀到的材料才算已讀；模型既有知識不是已查閱來源。
2. 直接引句需要原文與位置；轉述必須明確標示。
3. 部分或失敗提取不得被渲染成宣稱完整的報告。
4. 事實查核與公眾評價分開；讀者聲量不能取代真偽判斷。
5. 接受作者前提不代表論證必然成立；分析者補強也不冒充作者原意。

### 資料與渲染流程

```text
PDF / EPUB / TXT / notes
        │
        ▼
extract-text.py ── status + coverage + failed ranges
        │
        ▼
reading analysis ── structured JSON + sources
        │
        ▼
report_contract.py ── reject missing or inconsistent evidence
        │
        ▼
render-report.py ── self-contained HTML + Markdown export
```

```bash
# 檢查 PDF 大小與分塊需求
python scripts/extract-text.py book.pdf --info

# 提取內容
python scripts/extract-text.py book.pdf -o book.md

# 驗證分析資料
python scripts/render-report.py analysis.json --validate

# 渲染報告
python scripts/render-report.py analysis.json -o reading-report.html
```

`render-report.py` 也接受 stdin。只有資料契約通過時才會輸出 HTML。

### TIPS

| 維度 | 問題 |
|---|---|
| T — 工具性 | 是否提供可執行、可檢驗的方法 |
| I — 啟發性 | 相對已知背景，是否帶來新的理解角度 |
| P — 實用性 | 對已知讀者情境是否有幫助 |
| S — 科學性 | 可驗證主張的證據與推論品質如何 |

每一維都是 `assessed`、`unknown` 或 `not_applicable`。只有 `assessed` 使用 1–3 分；資訊不足不會被換算成低分。

### 專案結構

```text
crisp-reading/
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── cover.webp
│   └── reading-report-template.html
├── references/
│   ├── analysis.md
│   ├── design-spec.md
│   ├── ebook-library.md
│   └── json-schema.md
├── scripts/
│   ├── extract-text.py
│   ├── render-report.py
│   └── report_contract.py
└── tests/
```

### 測試

```bash
python3 -m unittest discover -s tests -v
```

fixtures 使用合成材料，只驗證資料契約、提取狀態與渲染行為；它們不是任何真實書籍的閱讀品質證據。

### 需求

- 支援 Agent Skills 的 AI agent。
- Python 3.9+。
- PDF fallback：`pymupdf4llm`。
- PDF `--info` / `--toc`：PyMuPDF (`pymupdf` / `fitz`)。
- EPUB：可用的文件轉 Markdown gateway；沒有可行後端時會明確回報。

### 授權

[MIT](LICENSE)

<p align="right"><a href="#top">回到頂端</a></p>

---

<a id="en-us"></a>

## English (en-US)

**CRISP = Comprehend · Review · Internalize · Synthesize · Practice.**

CRISP Reading is an evidence-aware deep-reading skill for AI agents. It checks the reader's intent and the material actually available. It then routes the request to full reading, scoped reading, quick evaluation, note expansion, or preliminary evaluation. It does not present every input as a complete deep read.

The final deliverable is a self-contained Traditional Chinese HTML report that works offline. It states what was read, what was not read or failed to extract, which sources support the analysis, and which limits still apply. Readers can trace important conclusions back to the material.

### Install

```bash
npx skills add kcchien/crisp-reading
```

Any compatible agent that can read `SKILL.md` can use the skill. This repository version requires Python 3.9+. The PDF fallback requires `pymupdf4llm`. PDF structure inspection requires PyMuPDF. If the environment provides a document-to-Markdown gateway, the extractor uses it first.

### Ways to use it

| You say | What the skill does |
|---|---|
| “Help me read this book” with a PDF or EPUB | Extracts the requested scope, performs full analysis, validates the data, and renders HTML |
| “Read the first five chapters” | Treats only those chapters as the requested scope and does not guess the rest |
| “Is this book worth reading?” | Produces a concise `quick` evaluation |
| “I have notes. Help me go deeper.” | Preserves the reader's judgments and strengthens them with traceable source material |
| A book title only | Searches for a lawful full-text source first; otherwise delivers a `preliminary` report |
| “Only summarize this document” | Follows the summary request without starting the full CRISP workflow |

If the user explicitly declines HTML, the skill follows that request. Other book-reading modes deliver HTML by default.

### What the report contains

- The report mode and a one-line conclusion.
- Coverage: requested scope, read locations, unread locations, failures, source basis, and limits.
- Continuous chapters for core analysis, concept relationships, critique, or interpretation.
- Separate TIPS scores or states with reasons. There is no total score or fixed “good book” grade.
- Quotations, candidate applications, knowledge links, and further reading only when supported.
- Traceable sources, with source claims separated from analyst inferences.

Literary works use a dedicated path for narrative, character, language, imagery, and theme. They do not receive forced scientificity scores or action plans. Without reader context, applications remain candidates rather than invented commitments.

### HTML reading experience

Each report is one self-contained HTML file. It needs no server or external framework.

- Core content uses continuous chapters. The table of contents lists only present sections.
- Source locations, quotation types, TIPS reasons, and unknown or not-applicable states remain visible.
- Light and dark themes, Markdown copy and download, and print styles are included.
- The body and sources remain readable when JavaScript is disabled.
- Long URLs and wide tables do not create page-wide horizontal overflow.
- If copy fails, the report exposes selectable Markdown instead of reporting false success.

### Evidence contract

1. Only material the skill actually reads counts as read. Model knowledge is not a reviewed source.
2. Direct quotations require the original text and a location. Paraphrases must be labeled.
3. Partial or failed extraction cannot render as a report that claims complete coverage.
4. Fact-checking and public reception remain separate. Popularity cannot establish truth.
5. Accepting an author's premise does not prove the argument. Analyst strengthening cannot impersonate the author.

### Data and rendering pipeline

```text
PDF / EPUB / TXT / notes
        │
        ▼
extract-text.py ── status + coverage + failed ranges
        │
        ▼
reading analysis ── structured JSON + sources
        │
        ▼
report_contract.py ── reject missing or inconsistent evidence
        │
        ▼
render-report.py ── self-contained HTML + Markdown export
```

```bash
# Inspect PDF size and chunking requirements
python scripts/extract-text.py book.pdf --info

# Extract content
python scripts/extract-text.py book.pdf -o book.md

# Validate analysis data
python scripts/render-report.py analysis.json --validate

# Render the report
python scripts/render-report.py analysis.json -o reading-report.html
```

`render-report.py` also accepts stdin. It writes HTML only after the data contract passes.

### TIPS

| Dimension | Question |
|---|---|
| T — Toolability | Does the book provide methods that readers can perform and test? |
| I — Inspirability | Does it add a new perspective relative to the reader's known background? |
| P — Practicality | Does it help in the reader's known context? |
| S — Scientificity | How strong are the evidence and inferences behind verifiable claims? |

Each dimension is `assessed`, `unknown`, or `not_applicable`. Only `assessed` dimensions use a 1–3 score. Missing information never becomes a low score.

### Project structure

```text
crisp-reading/
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── cover.webp
│   └── reading-report-template.html
├── references/
│   ├── analysis.md
│   ├── design-spec.md
│   ├── ebook-library.md
│   └── json-schema.md
├── scripts/
│   ├── extract-text.py
│   ├── render-report.py
│   └── report_contract.py
└── tests/
```

### Tests

```bash
python3 -m unittest discover -s tests -v
```

The fixtures use synthetic material. They verify the data contract, extraction status, and rendering behavior. They are not evidence of reading quality on real books.

### Requirements

- An AI agent that supports Agent Skills.
- Python 3.9+.
- PDF fallback: `pymupdf4llm`.
- PDF `--info` and `--toc`: PyMuPDF (`pymupdf` / `fitz`).
- EPUB: an available document-to-Markdown gateway. The skill reports the limitation when no backend can read the file.

### License

[MIT](LICENSE)

<p align="right"><a href="#top">Back to top</a></p>
