# CRISP Reading

以可回查來源完成書籍分析，並交付可離線閱讀的繁體中文 HTML 報告。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-compatible-blueviolet.svg?style=flat-square)](#安裝)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab.svg?style=flat-square)](#需求)

CRISP = Comprehend · Review · Internalize · Synthesize · Practice。

它不是把所有輸入都包裝成「完整深讀」。技能先判斷使用者意圖與實際材料，再分成完整閱讀、指定範圍、快速評估、既有筆記或初步評估；報告頁首會說明已讀範圍、未讀／失敗位置、來源與限制。

## 安裝

```bash
npx skills add kcchien/crisp-reading
```

任何能讀取 `SKILL.md` 的相容 agent 都可使用。這個 repository 版本需要 Python 3.9+；PDF fallback 需要 `pymupdf4llm`，PDF 結構資訊需要 PyMuPDF。若環境已有可用的文件轉 Markdown gateway，提取器會優先使用它。

## 使用方式

| 你說 | 技能如何處理 |
|---|---|
| 「幫我讀這本書」並附 PDF / EPUB | 提取要求範圍、完整分析、驗證資料、輸出 HTML |
| 「先讀前五章」 | 只把前五章當要求範圍，其他內容不猜測 |
| 「這本書值不值得讀？」 | 產出 `quick` 精簡評估 |
| 「我有筆記，幫我深化」 | 保留既有判斷，以筆記與可回查原文補強 |
| 只有書名 | 先尋找合法可用全文；找不到就交付 `preliminary`，不冒充完整閱讀 |
| 「只摘要這份文件」 | 不啟動完整 CRISP，照摘要需求處理 |

使用者明確不要 HTML 時會遵守；其他書籍閱讀模式預設交付 HTML。

## 報告會呈現什麼

- 報告模式與一句話結論。
- 閱讀範圍：要求、已讀、未讀、失敗位置、依據類型與限制。
- 連續章節的核心分析、概念關係、批判或其他詮釋。
- TIPS 四維度的個別分數／狀態與理由；沒有總分或固定「好書」等級。
- 有根據才顯示的引句、候選應用、知識連結與延伸閱讀。
- 可回查來源；來源主張與分析者推論分開標示。

文學作品使用敘事、人物、語言、意象與主題的分支，不強制科學性分數或行動計畫。沒有讀者情境時，應用只會標成候選，不會假裝讀者已內化或承諾。

## HTML 閱讀體驗

報告是自包含的單一 HTML 檔案，不需要伺服器或外部框架：

- 核心內容以連續章節呈現，頁內目錄只列出存在的區塊。
- 顯示來源位置、引句類型、TIPS 理由與未知／不適用狀態。
- 提供淺色／深色模式、複製 Markdown、下載 Markdown 與列印樣式。
- JavaScript 關閉時，正文與來源仍完整可讀。
- 長 URL 與寬表格不會讓整頁水平溢位；表格需要時局部捲動。
- Copy 失敗會顯示可手動選取的 Markdown，不會假報成功。

## 證據原則

1. 只有實際讀到的材料才算已讀；模型既有知識不是已查閱來源。
2. 直接引句需要原文與位置；轉述明確標示。
3. 部分或失敗提取不得被渲染成宣稱完整的報告。
4. 事實查核與公眾評價分開；讀者聲量不能取代真偽判斷。
5. 接受作者前提不代表論證必然成立；分析者補強也不冒充作者原意。

## 資料與渲染流程

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

## TIPS

| 維度 | 問題 |
|---|---|
| T — 工具性 | 是否提供可執行、可檢驗的方法 |
| I — 啟發性 | 相對已知背景，是否帶來新的理解角度 |
| P — 實用性 | 對已知讀者情境是否有幫助 |
| S — 科學性 | 可驗證主張的證據與推論品質如何 |

每一維都是 `assessed`、`unknown` 或 `not_applicable`。只有 `assessed` 使用 1–3 分；資訊不足不會被換算成低分。

## 專案結構

```text
crisp-reading/
├── SKILL.md
├── agents/openai.yaml
├── assets/reading-report-template.html
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

## 測試

```bash
python3 -m unittest discover -s tests -v
```

fixtures 使用合成材料，只驗證資料契約、提取狀態與渲染行為；它們不是任何真實書籍的閱讀品質證據。

## 需求

- 支援 Agent Skills 的 AI agent。
- Python 3.9+。
- PDF fallback：`pymupdf4llm`。
- PDF `--info` / `--toc`：PyMuPDF (`pymupdf` / `fitz`)。
- EPUB：可用的文件轉 Markdown gateway；沒有可行後端時會明確回報。

## License

[MIT](LICENSE)

---

## English

CRISP Reading turns verifiable book material into a self-contained Traditional Chinese HTML reading report. It routes full-text reading, scoped chapters, quick evaluation, existing notes, and title-only requests separately instead of presenting every result as a complete deep read.

The report exposes coverage and limitations, links claims to sources, keeps direct quotations distinct from paraphrases, and shows each TIPS dimension with its own reason. Missing reader context remains unknown; literary works use a dedicated interpretive branch. Core content remains readable without JavaScript, while theme switching, truthful Markdown copy/download, responsive layout, and print styling are progressive enhancements.
