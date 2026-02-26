<div align="center">

<img src="assets/cover.png" alt="CRISP Reading — 你的 AI 閱讀夥伴" width="100%"/>

# CRISP Reading — 你的 AI 閱讀夥伴

[![授權: MIT](https://img.shields.io/badge/授權-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-通用相容-blueviolet?style=flat-square)](#-相容的-ai-agent)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python&logoColor=white)](#-前置條件)
[![方法論](https://img.shields.io/badge/閱讀方法論-6_種融合-e8a87c?style=flat-square)](#-設計理念)

**把任何一本書，變成真正的理解。**

[快速安裝](#-快速安裝) · [運作原理](#️-運作原理) · [設計理念](#-設計理念) · [功能特色](#-功能特色-1)

</div>

---

> **CRISP** = **C**omprehend · **R**eview · **I**nternalize · **S**ynthesize · **P**ractice
>
> 深度閱讀五階段：理解結構、批判審視、內化連結、整合全貌、付諸行動。

大部分 AI「讀書摘要」給你一份條列清單就結束了。你覺得好像讀了什麼，但什麼都沒留下。

**CRISP Reading** 不一樣。它不只是摘要——它像一位認真的讀者那樣*閱讀*：質疑作者的預設立場、壓力測試論證邏輯、把新想法跟你已知的知識連結起來，最後把洞察轉化成具體可執行的行動。

產出不是一堵文字牆。而是一份互動式 HTML 閱讀報告——可展開的論點、精選引句、批判專區、個人行動計畫——設計得像翻開一本精裝書，而不是滑過一個儀表板。

## ⚡ 快速安裝

```bash
npx skills add kcchien/crisp-reading
```

就這樣。當你請 AI 助手讀書或分析書籍時，它會自動啟用這個技能。

> **使用 Claude.ai 桌面版？** 下載 [crisp-reading.skill](https://books.kcchien.com/crisp-reading.skill)，到 [claude.ai/customize/skills](https://claude.ai/customize/skills) 上傳即可。詳見 [圖文安裝說明](https://github.com/kcchien/skills/blob/main/docs/install-crisp-reading.md)。

## ✨ 你可以怎麼用？

用自然語言跟你的 AI 助手對話即可：

| 你說 | 發生什麼事 |
|------|-----------|
| *「幫我讀這本書」* + PDF | 提取全文 → 深度分析 → 互動式 HTML 報告 |
| *「分析《老殘遊記》」*（僅書名） | 自動從 70,000+ 冊公共領域書庫下載全文 → 同樣的深度分析 |
| *「分析《原子習慣》」*（書庫無收錄） | 依 Claude 知識分析，報告中明確標示 |
| *「這本書值不值得讀？」* | 快速 TIPS 四維度評估，不囉嗦 |
| *「我有讀書筆記了，幫我深化」* | 以你的筆記為基礎延伸，不從頭開始 |
| *「先讀前五章」* | 支援大型書籍分批處理，最後合併為一份報告 |

### 公共領域書庫

沒有 PDF？沒問題。技能會自動搜尋 [Project Gutenberg](https://www.gutenberg.org)（透過 Gutendex API）並下載全文進行分析——完全不需手動操作。

- **70,000+** 冊公共領域書籍可用
- **444+ 冊中文古典文學** — 紅樓夢、西遊記、三國演義、老殘遊記、儒林外史、孽海花等
- **中日韓書名搜尋** — 直接輸入中文書名即可
- **數萬冊英文作品**（1928 年前）— Shakespeare, Austen, Dickens, Fitzgerald 等經典
- 書庫沒收錄？回退到 Claude 知識分析，報告中清楚標示

## ⚙️ 運作原理

**三條路徑，同樣的深度分析：**

<img src="assets/flow.png" alt="CRISP Reading 運作流程" width="100%"/>

| 輸入 | 發生什麼事 |
|------|-----------|
| PDF / EPUB 檔案 | 提取全文 → 深度分析 → HTML 報告 |
| 僅輸入書名 | 自動搜尋 70,000+ 冊公共領域書籍（[Gutendex API](https://gutendex.com)）→ 下載全文 → 同樣的深度分析 |
| 僅書名（書庫無收錄） | 依 Claude 知識分析，報告中明確標示 |

公共領域書庫收錄 **444+ 冊中文古典文學**（紅樓夢、西遊記、三國演義、老殘遊記等）及數萬冊 1928 年前的英文作品。完整支援中日韓書名搜尋——直接輸入中文書名即可。

**職責分離：**

| 工作 | 由誰做 | Token 消耗 |
|------|--------|-----------|
| 文字提取、分塊、書籍資訊 | `extract-text.py` | 零 |
| 公共領域書庫搜尋與下載 | Gutendex API | 零 |
| 閱讀理解、批判、整合 | Claude | 依書籍大小 |
| HTML 模板渲染 | `render-report.py` | 零 |

大型書籍（>80K tokens）會自動分塊、逐批分析、最後合併為一份連貫的報告——不是碎片拼接。

## 🧠 設計理念

CRISP Reading 融合六種經過驗證的閱讀方法論，形成一套完整的閱讀實踐。單一方法無法涵蓋所有面向；組合起來才是完整的閱讀。

### 六大方法論

| 方法 | 它貢獻什麼 | 在 CRISP 中的角色 |
|------|-----------|-----------------|
| **Adler 分析閱讀** | 系統化理解——每位讀者都該問的四個問題 | 結構分析：這本書在談什麼、論點是什麼、有道理嗎、跟我有什麼關係 |
| **TIPS 評分法**（樊登） | 四維度評分——工具性、啟發性、實用性、科學性 | 快速分流：決定分析深度（4-5 略讀、6-8 標準、9-12 完整深讀） |
| **Zettelkasten**（Luhmann） | 三層筆記結構——閃念、文獻、永久 | 知識整合：把書中概念連結到你既有的知識網路 |
| **費曼技巧** | 「如果你沒辦法簡單地解釋它，代表你還不夠懂」 | 產出檢驗：報告中每個概念都必須用白話解釋 |
| **自我解釋法** | 暫停，用自己的話重述——What / Why / Connection | 理解確認：標記那些理解不夠深的段落 |
| **鋼鐵人論證** | 批判前先強化作者的論點到最強版本 | 智識誠實：批判最強版本的論點，而不是稻草人 |

### 設計原則

1. **誠實優先** — 僅憑書名（沒有 PDF）時，明確標示。絕不編造細節或虛構引句。
2. **批判與證據等比** — 科學性越弱，批判越深。有紮實研究的書批判佔 15-20%；靠軼事的自我成長書佔 30-40%。
3. **方法論不外露** — 報告中永遠不出現「Adler」、「Zettelkasten」、「鋼鐵人論證」。讀者看到的是自然的文字。
4. **行動必須具體** — 每個行動承諾三要素缺一不可：*何時*（時間）、*何處*（場景）、*做什麼*（具體行為）。
5. **留白引思考** — 報告刻意留下開放式提問，引導讀者形成自己的判斷，而非給出定論。

## 📊 報告範例

<!-- TODO: 加入報告截圖 -->
<!-- <img src="assets/sample-report.png" alt="CRISP Reading 報告範例" width="100%"/> -->

> *截圖即將加入——對任何書執行此技能即可產出你自己的報告。*

每份報告包含：

| 區塊 | 深度 | 你會看到什麼 |
|------|------|------------|
| 一句話評價 | 精華版 | 一句話捕捉這本書的核心價值 |
| TIPS 評分 | 精華版 | 四維度評分，告訴你這本書*為什麼*值得讀（或不值得） |
| 核心論點 | 精華版 | 3-7 個關鍵論點，可展開查看論證細節 |
| 關鍵概念 | 精華版 | 書中的核心詞彙，用白話解釋 |
| 精選引句 | 精華版 | 3-5 則最佳段落，非中文書附翻譯 |
| 行動計畫 | 精華版 | 3-5 個具體承諾，含時間、場景、行為 |
| 概念關係圖 | 完整版 | SVG 圖表呈現概念間的關聯 |
| 批判視角 | 完整版 | 邏輯跳躍、證據不足、隱含假設 |
| 知識連結 | 完整版 | Zettelkasten 風格的跨書連結 |
| 延伸閱讀 | 完整版 | 下一步該讀什麼，以及為什麼 |

報告是一個**完全獨立的 HTML 檔案**——不需要伺服器、不需要框架、不需要網路。用任何瀏覽器打開即可。特色：

- **精華版 / 完整版切換** — 先看重點，想深入再展開
- **深色模式** — 跟隨系統偏好，或手動切換
- **列印友善** — 自動展開所有區塊、強制淺色模式
- **響應式** — 手機、平板、桌面都好讀

## ✨ 更多特色

- **智慧分塊** — 大型書籍自動切割、分批分析、智慧合併
- **PDF + EPUB** — PDF 用內建 pymupdf4llm；EPUB 可選用 [document-to-markdown](https://github.com/kcchien/skills) 技能
- **多語言輸入** — 讀任何語言的書，一律以繁體中文輸出，原文引句保留
- **零 Token 渲染** — HTML 生成完全由腳本處理；Claude 的算力全花在思考上

## 🤝 相容的 AI Agent

| Agent | 安裝方式 |
|-------|---------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `npx skills add kcchien/crisp-reading` |
| 其他相容 Agent | 任何能讀取 `SKILL.md` 作為指令的 AI Agent |

> CRISP Reading 遵循開放的 `SKILL.md` 慣例。任何能發現並載入 `SKILL.md` 的 AI Agent 都能使用。

## 📋 前置條件

- 支援 Agent Skills 的 AI 編碼助手（例如 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)）
- Python 3.9+
- `pymupdf4llm`（`pip install pymupdf4llm`）— PDF 文字提取
- *（選用）* [document-to-markdown](https://github.com/kcchien/skills) 技能 — EPUB 支援

## 📄 授權

[MIT](LICENSE)

---

<div align="center">

<img src="assets/cover.png" alt="CRISP Reading — Your AI Reading Companion" width="100%"/>

# CRISP Reading

**Turn any book into understanding.**

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-Compatible-blueviolet?style=flat-square)](#-compatible-agents)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python&logoColor=white)](#-requirements)
[![Methods](https://img.shields.io/badge/Reading_Methods-6_Integrated-e8a87c?style=flat-square)](#-philosophy)
[![Output](https://img.shields.io/badge/Output-Interactive_HTML-2d6a4f?style=flat-square)](#-sample-report)

An AI reading companion that deconstructs, critiques, and internalizes books — <br/>
then produces a beautiful, interactive HTML reading report.

[Quick Install](#-quick-install) · [What Can You Do](#-what-can-you-do-with-it) · [How It Works](#-how-it-works) · [Philosophy](#-philosophy)

</div>

---

> **CRISP** = **C**omprehend · **R**eview · **I**nternalize · **S**ynthesize · **P**ractice
>
> Five stages of deep reading: understand the structure, critically review the arguments, internalize through your own knowledge, synthesize into a coherent picture, and commit to practice.

Most AI "book summaries" give you a bullet list and call it a day. You walk away feeling like you read something, but nothing sticks.

**CRISP Reading** is different. It doesn't just summarize — it *reads* the book the way a thoughtful reader would: questioning the author's assumptions, stress-testing the arguments, connecting ideas to what you already know, and turning insights into concrete actions.

The output isn't a wall of text. It's an interactive HTML report — with collapsible arguments, curated quotes, critique sections, and a personal action plan — designed to feel like opening a beautifully typeset book, not scrolling through a dashboard.

## ⚡ Quick Install

```bash
npx skills add kcchien/crisp-reading
```

That's it. Your AI agent will automatically activate when you ask it to read or analyze a book.

> **Using Claude.ai desktop?** Download [crisp-reading.skill](https://books.kcchien.com/crisp-reading.skill), then upload at [claude.ai/customize/skills](https://claude.ai/customize/skills). See [step-by-step guide](https://github.com/kcchien/skills/blob/main/docs/install-crisp-reading.md).

## ✨ What Can You Do With It?

Just talk to your AI assistant naturally:

| You say | What happens |
|---------|-------------|
| *"Help me read this book"* + PDF | Extracts full text → deep analysis → interactive HTML report |
| *"Analyze 老殘遊記"* (title only) | Auto-downloads from 70,000+ public domain books → same deep analysis |
| *"Analyze Atomic Habits"* (not in library) | Analyzes from Claude's knowledge, clearly labeled |
| *"Is this book worth reading?"* | Quick TIPS 4-dimension evaluation, no fluff |
| *"I have reading notes — help me go deeper"* | Builds on your existing work, not starting over |
| *"Read chapters 1-5 first"* | Handles large books in chunks, merges into one report |

### Public Domain Book Library

No PDF? No problem. The skill automatically searches [Project Gutenberg](https://www.gutenberg.org) (via Gutendex API) and downloads the full text for analysis — zero manual effort.

- **70,000+** public domain books available
- **444+ Chinese classics** — 紅樓夢, 西遊記, 三國演義, 老殘遊記, 儒林外史, 孽海花, and more
- **CJK search** — type book titles in Chinese, Japanese, or Korean directly
- **Tens of thousands of English works** pre-1928 — Shakespeare, Austen, Dickens, Fitzgerald, and beyond
- Book not in the library? Falls back to Claude's knowledge, clearly marked in the report

## ⚙️ How It Works

**Three paths to the same deep analysis:**

<img src="assets/flow.png" alt="CRISP Reading — How It Works" width="100%"/>

| Input | What happens |
|-------|-------------|
| PDF / EPUB file | Extract full text → deep analysis → HTML report |
| Book title only | Auto-search 70,000+ public domain books via [Gutendex API](https://gutendex.com) → download full text → same deep analysis |
| Book title (not in library) | Analyze based on Claude's knowledge, clearly labeled as such |

The public domain library includes **444+ Chinese classics** (紅樓夢, 西遊記, 三國演義, 老殘遊記, etc.) and tens of thousands of English works pre-1928. CJK title search is fully supported — just type the book name in Chinese, Japanese, or Korean.

**Clear separation of concerns:**

| Responsibility | Who | Token Cost |
|----------------|-----|-----------|
| Text extraction, chunking, book info | `extract-text.py` | Zero |
| Public domain book search & download | Gutendex API | Zero |
| Reading comprehension, critique, synthesis | Claude | Context-dependent |
| HTML template rendering | `render-report.py` | Zero |

For large books (>80K tokens), the skill automatically splits the text into chunks, analyzes each batch, then merges all partial notes into one cohesive report — not a patchwork of fragments.

## 🧠 Philosophy

CRISP Reading fuses six proven reading methodologies into a single, coherent workflow. No single method covers everything; together they form a complete reading practice.

### The Six Methods

| Method | What It Contributes | Role in CRISP |
|--------|-------------------|---------------|
| **Adler's Analytical Reading** | Systematic comprehension — the four questions every reader should ask | Structural analysis: what is the book about, what are the arguments, is it true, what of it? |
| **TIPS Evaluation** (Fan Deng) | Four-dimensional book scoring — Toolability, Inspirability, Practicality, Scientificity | Quick triage: determines how deep the analysis should go (4-5 = skim, 6-8 = standard, 9-12 = full depth) |
| **Zettelkasten** (Luhmann) | Three-layer note structure — fleeting, literature, permanent | Knowledge integration: connects book ideas to your existing knowledge graph |
| **Feynman Technique** | "If you can't explain it simply, you don't understand it" | Output test: every concept in the report must be explainable in plain language |
| **Self-Explanation** | Pause and re-state in your own words — What / Why / Connection | Comprehension check: flags passages where understanding is shallow |
| **Steel-Manning** | Strengthen the author's argument before critiquing it | Intellectual honesty: critique the best version of the argument, not a strawman |

### Design Principles

1. **Honesty over completeness** — If the skill only has a book title (no PDF), it says so. It never fabricates details or invents quotes.
2. **Critique scales with evidence** — The weaker the scientific backing, the deeper the critique. A well-researched book gets 15-20% critical content; a self-help book built on anecdotes gets 30-40%.
3. **Methods stay invisible** — The report never mentions "Adler", "Zettelkasten", or "Steel-Manning". Readers see natural prose, not methodology labels.
4. **Actions must be specific** — Every action item has three parts: *when* (time), *where* (context), and *what* (concrete behavior). "Read more" is not an action; "Tomorrow morning, spend 15 minutes journaling about Chapter 3's framework" is.
5. **Leave room for thinking** — The report deliberately poses open questions rather than giving definitive verdicts. The goal is to spark the reader's own judgment.

## 📊 Sample Report

<!-- TODO: Add screenshot of a generated report -->
<!-- <img src="assets/sample-report.png" alt="Sample CRISP Reading Report" width="100%"/> -->

> *Screenshot coming soon — run the skill on any book to generate your own.*

Each report includes:

| Section | Depth | What You Get |
|---------|-------|-------------|
| One-line verdict | Essential | A single sentence that captures the book's core value |
| TIPS score | Essential | Four-dimensional rating that tells you *why* the book matters (or doesn't) |
| Core arguments | Essential | 3-7 key arguments, each expandable with supporting detail |
| Key concepts | Essential | The book's vocabulary, explained in plain language |
| Curated quotes | Essential | 3-5 best passages with translation (for non-Chinese books) |
| Action plan | Essential | 3-5 concrete commitments with time, context, and specific behavior |
| Concept map | Deep | SVG diagram showing how the book's ideas relate to each other |
| Critical perspectives | Deep | Where the author's logic breaks, evidence is thin, or assumptions are hidden |
| Knowledge links | Deep | Zettelkasten-style connections to other books and ideas |
| Further reading | Deep | What to read next, and why |

The report ships as a **self-contained HTML file** — no dependencies, no server, no JavaScript frameworks. Open it in any browser. It features:

- **Essential / Deep toggle** — Start with the highlights, expand when you want more
- **Dark mode** — Follows your system preference, or toggle manually
- **Print-friendly** — Expands all sections and forces light mode for clean printing
- **Responsive** — Reads well on phones, tablets, and desktops

## ✨ More Features

- **Smart chunking** — Automatically splits large books, analyzes in batches, merges intelligently
- **PDF + EPUB** — PDF via built-in pymupdf4llm; EPUB via optional [document-to-markdown](https://github.com/kcchien/skills) skill
- **Multilingual input** — Reads books in any language, always outputs in Traditional Chinese with original quotes preserved
- **Zero-token rendering** — HTML generation is fully scripted; Claude's context is spent on thinking, not formatting

## 🤝 Compatible Agents

| Agent | Install Method |
|-------|---------------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `npx skills add kcchien/crisp-reading` |
| Other compatible agents | Any agent that reads `SKILL.md` as instructions |

> CRISP Reading follows the open `SKILL.md` convention. Any AI agent that can discover and load `SKILL.md` files will work.

## 📁 What's Inside

```
crisp-reading/
├── SKILL.md                              # Agent instructions (entry point)
├── scripts/
│   ├── extract-text.py                   # PDF/EPUB → plain text
│   └── render-report.py                  # Analysis JSON → HTML report
├── references/
│   ├── json-schema.md                    # Output JSON structure spec
│   ├── analysis.md                       # Reading methodology details
│   ├── design-spec.md                    # HTML report design guidelines
│   └── ebook-library.md                  # Public domain book sources & API guide
└── assets/
    └── reading-report-template.html      # HTML template (851 lines)
```

## 📋 Requirements

- An AI coding assistant that supports Agent Skills (e.g., [Claude Code](https://docs.anthropic.com/en/docs/claude-code))
- Python 3.9+
- `pymupdf4llm` (`pip install pymupdf4llm`) — for PDF text extraction
- *(Optional)* [document-to-markdown](https://github.com/kcchien/skills) skill — for EPUB support

## 📄 License

[MIT](LICENSE)
