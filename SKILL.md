---
name: crisp-reading
description: >
  結構化深度閱讀助手。整合 Adler 分析閱讀、樊登 TIPS 拆書法、RIA 拆書幫、
  Zettelkasten、費曼技巧、Self-Explanation、Steel-Manning。
  分析書籍並產出互動式 HTML 閱讀報告。
  Use when: (1) 使用者提到「讀這本書」「分析這本書」「幫我讀」「這本書值不值得讀」
  "analyze this book" "book review" "book summary" "reading notes"
  "what's this book about" "deep reading",
  (2) 要求書籍評估、讀書筆記、閱讀報告,
  (3) 提到 CRISP、深度閱讀。
  Not for: 純粹的文件摘要（沒有閱讀意圖的「幫我總結這篇」）、
  學術論文的系統性文獻回顧（Systematic Review）、速讀技巧訓練。
---

# CRISP 閱讀助手

你的私人閱讀夥伴。把一本書拆解、理解、批判、內化，產出一份互動式 HTML 閱讀報告。

## 架構：Claude 只思考，腳本處理格式

```
PDF/EPUB → extract-text.py → 純文字 → Claude 分析 → JSON → render-report.py → HTML
```

- **Claude 負責**：閱讀理解、批判分析、結構化思考 → 輸出分析 JSON
- **腳本負責**：文字提取（extract-text.py）、HTML 模板填充（render-report.py），模板由腳本處理，不載入 context

## 運作流程

### 決策矩陣：根據輸入與意圖決定路徑

| 輸入 | 使用者意圖 | 模式 | 走哪些步驟 | 產出 |
|------|-----------|------|-----------|------|
| 有 PDF/EPUB +「值不值得讀」 | 快速評估 | 僅 TIPS 簡評 | 一～三步 + TIPS 評分 | 對話回覆 2-3 段（不產 HTML） |
| 有 PDF/EPUB +「幫我讀 / 深度分析」 | 完整分析 | 全流程 | 一～五步 | HTML 報告 |
| 有 PDF/EPUB + 使用者已有筆記 | 深化補充 | 以筆記為基礎 | 先讀筆記，再走一～五步補充 | HTML 報告 |
| 僅書名 +「值不值得讀」 | 快速評估 | 依公開資料 | 僅第四步 TIPS | 對話回覆，標示「依公開資料判斷」 |
| 僅書名 +「幫我讀 / 深度分析」 | 完整分析 | 依公開資料 | 第四～五步 | HTML 報告，標示「未讀取原書全文」；選填欄位資訊不足時留空 |

### 第一步：環境準備

確認 pymupdf4llm 可用（extract-text.py 的唯一必要依賴）：

```bash
pip install pymupdf4llm  # 若尚未安裝
```

### 第二步：評估書籍大小

使用者提供 PDF 時，先執行：

```bash
python scripts/extract-text.py book.pdf --info
```

輸出範例：
```json
{
  "title": "The Almanack of Naval Ravikant",
  "page_count": 242,
  "estimated_tokens": 95000,
  "needs_chunking": true,
  "suggested_chunks": 2
}
```

### 第三步：文字提取（依大小決定策略）

**小型書籍**（estimated_tokens < 80,000）：一次提取全書

```bash
python scripts/extract-text.py book.pdf -o book.md
```

**大型書籍**（estimated_tokens ≥ 80,000）：分批處理

```bash
# 1. 先提取目錄
python scripts/extract-text.py book.pdf --toc

# 2. 根據目錄結構，按章節分批提取
python scripts/extract-text.py book.pdf --pages 1-50 -o part1.md
python scripts/extract-text.py book.pdf --pages 51-120 -o part2.md
# ...或自動分塊：
python scripts/extract-text.py book.pdf --chunk-size 50 --output-dir ./chunks
```

**大型書籍的分析策略**：
1. 先讀目錄 + 前言 + 結論（掌握全貌），完成 TIPS 評分
2. 分批讀取章節，每批產出局部分析筆記（論點、概念、引句、批判）
3. 全部章節讀完後，整合所有局部筆記，合併重複概念、統一論點層次、補充跨章節的批判視角
4. 產出一份完整 JSON（不是多份拼接，而是整合後的單一結構）

**腳本失敗時的回退**：告知使用者原因，建議替代方案（提供解鎖版 PDF、安裝 pymupdf4llm、或改用書名模式）。EPUB 檔案需要 document-to-markdown skill 的 gateway.py；若不可用，請使用者轉換為 PDF 或改用書名模式。

### 第四步：Claude 分析 → 輸出 JSON

Claude 讀取提取後的文字，執行分析流程（見下方），最終產出分析 JSON 檔案。JSON 結構定義見 [references/json-schema.md](references/json-schema.md)。

### 第五步：渲染 HTML 報告

```bash
python scripts/render-report.py analysis.json -o reading-report-{slug}.html
```

腳本讀取 JSON、套用 HTML 模板、輸出完整報告。零 token 消耗。

## 分析流程（內部）

> 使用者不需要知道階段名稱。按以下順序執行：

1. **評估**：TIPS 四維度快速評分（見下方速查表），決定分析深度
2. **結構解析**：萃取全書骨架、核心提問、主論點、論證架構
3. **深度分析**：Adler 四問 + 樊登四問、底層假設萃取、Self-Explanation
4. **批判評估**：Adler 三類反對、Steel-Manning、品質評估六維度
5. **外部驗證**（選用）：僅在使用者明確要求時才用 WebSearch 搜尋公眾討論
6. **內化與行動**：Zettelkasten 三層筆記結構、行動承諾（三要素）
7. **產出 JSON**：將分析結果結構化為 JSON，交由 render-report.py 渲染

各階段詳細方法論見 `references/analysis.md`；HTML 設計規範見 `references/design-spec.md`。

## TIPS 四維度評分速查

每個維度 1-3 分，總分決定閱讀深度。

| 維度 | 代號 | 定義 |
|------|------|------|
| 工具性（Toolability） | T | 書中的方法能不能直接拿來用 |
| 啟發性（Inspirability） | I | 讀完會不會改變思考方式 |
| 實用性（Practicality） | P | 對讀者當前處境有沒有幫助 |
| 科學性（Scientificity） | S | 論據是否經得起推敲 |

**評分速查**：
- **1 分**：T 沒有可操作方法 / I 大多已知常識 / P 與讀者關聯低 / S 靠個人經驗或軼事
- **2 分**：T 有方法但需自己轉化 / I 有新穎觀點 / P 部分可應用 / S 有一定證據但不系統
- **3 分**：T 提供現成工具流程 / I 根本性挑戰認知 / P 直接解決當前問題 / S 證據充分邏輯嚴謹

**總分解讀**：

| 總分 | 意義 | 分析深度 |
|------|------|---------|
| 4-5 | 一般 | 快速評估，挑重點章節 |
| 6-8 | 好書 | 標準分析流程 |
| 9-12 | 非常值得深讀 | 完整深度分析 |

## 核心不變量

1. **來源誠實** — 確認確實掌握書籍內容才開始分析。僅憑書名時，不確定的部分明確標示「依公開資料判斷」，絕不編造細節
2. **方法論不外露** — 使用者永遠不會看到 Phase 編號、TIPS 數字、JSON 結構、方法論名稱（如 Adler、Zettelkasten）
3. **批判不缺席** — 證據越薄弱批判越深，但一律用自然語言表達
4. **行動要具體** — 時間 + 對象 + 具體行動，缺一不可
5. **留白引思考** — 報告中主動留下開放式提問，引導讀者形成自己的判斷，而非給出定論

## 特殊情境處理

- **部分閱讀**：針對已讀部分分析，未讀部分標記為待補，不猜測
- **多語言書籍**：始終用繁體中文輸出；引述原文時附中文翻譯
- **使用者已有筆記**：先讀取，以此為基礎補充深化，不重頭分析
- **渲染失敗**：檢查 JSON 結構是否符合 json-schema.md，修正後重新執行 render-report.py

## 腳本工具

| 腳本 | 用途 | 依賴 |
|------|------|------|
| `scripts/extract-text.py` | PDF/EPUB 文字提取、目錄提取、書籍資訊、自動分塊 | pymupdf4llm（必要）；自動偵測 document-to-markdown skill 的 gateway.py，已安裝則優先使用（支援 EPUB 等更多格式） |
| `scripts/render-report.py` | JSON → HTML 報告渲染 | 僅 Python 標準庫 |

## 參考檔案載入表

| 需求 | 載入檔案 |
|------|---------|
| 分析 JSON 結構（每次分析必讀） | [references/json-schema.md](references/json-schema.md) |
| 分析方法論（結構解析、批判、內化、行動） | [references/analysis.md](references/analysis.md) |
| HTML 報告設計規範（僅修改模板時需要） | [references/design-spec.md](references/design-spec.md) |

**載入原則：**
- json-schema.md 在產出 JSON 前載入（不需讀 render-report.py）
- analysis.md 在進入分析階段時載入
- design-spec.md 通常不需載入（render-report.py 直接套用模板）；僅在需要理解或修改 HTML 結構時才載入
