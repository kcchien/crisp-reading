---
name: crisp-reading
description: "CRISP Reading：AI 深度閱讀夥伴，整合 Adler 分析閱讀、拆書法、Zettelkasten、費曼技巧，分析書籍並產出互動式 HTML 閱讀報告。觸發：讀這本書、分析這本書、這本書值不值得讀、book review、reading notes、深度閱讀。"
---

# CRISP Reading

把書籍材料轉成可核對的繁體中文閱讀報告。先確認使用者要什麼與實際掌握哪些材料，再決定分析強度；完整度服從證據，不用版面或流暢文字掩蓋缺漏。

CRISP 是五個依序檢查的內部完成關卡：**Comprehend** 理解問題、材料與結構，**Review** 審視主張、證據與其他解釋，**Internalize** 用白話重建並連到已知讀者情境，**Synthesize** 整合跨章關係與可遷移知識，**Practice** 判斷適用性、取捨與下一步。它們共同形成既有報告欄位，不是五個固定的使用者可見章節；材料或情境不足時，相應關卡降低強度或停止。

除非使用者明確要求說明方法，使用者可見內容不得列出 C／R／I／S／P、五階段名稱、啟停狀態、完成關卡、內部方法名稱，或「依 schema／契約／規則所以選擇某模式」等流程自述；只呈現實際已讀、未讀、能支持的判斷與限制。

## 適用與退場

適用於書籍評估、完整或指定範圍閱讀、讀書筆記深化、閱讀報告，以及使用者明確提到 CRISP Reading。

以下情況退場，不啟動完整 CRISP：

- 只有「摘要這份文件」而沒有書籍閱讀、評估或內化意圖的純文件摘要。
- 學術論文的系統性文獻回顧。
- 速讀技巧訓練。

若輸入看似一本書但使用者只要求摘要，完成摘要即可；不要自行擴成深度閱讀專案。

## 先判斷模式

| 使用者意圖與材料 | `report_mode` | 處理方式 | 預設交付 |
|---|---|---|---|
| 「幫我讀這本書」並提供可讀全文 | `full` | 完整深讀要求範圍 | HTML |
| 指定章節或頁面 | `full` | 完整分析指定範圍；coverage 明列範圍外內容 | HTML |
| 「值不值得讀」「快速評估」 | `quick` | 精簡評估；不為湊完整而延伸 | 精簡 HTML；明確不要 HTML 時依指示 |
| 已有讀書筆記，要求整理或深化 | `notes` | 以筆記為主，必要時回查提供的原文 | HTML |
| 只有書名，沒有可讀全文 | `preliminary` | 先嘗試合法可用全文；仍無全文時只做初步評估 | HTML，清楚標示來源範圍 |

部分提取不是完整閱讀。提取結果為 `partial` 或 `failed` 時，先交代缺漏；只有使用者接受縮小範圍，才依已成功位置繼續。

階段深度由模式與閱讀 lens 決定：

| 情境 | 內部處理深度 |
|---|---|
| `full` + `nonfiction` | 完成五個關卡；Practice 仍受讀者情境限制 |
| `full` + `literature` | 以 Comprehend、Internalize、Synthesize 為主；Review 檢查文本依據與其他可成立讀法；Practice 可空 |
| `full` + `mixed` | 論證內容按非虛構標準 Review，敘事內容按文學標準 Review，最後在 Synthesize 合流 |
| `notes` | 保留讀者原判斷與疑問，再補材料界線、理解缺口、挑戰與連結 |
| `quick` | 做到足以回答是否值得讀的 Comprehend 與 Review；其他關卡只在已有材料支持時精簡處理 |
| `preliminary` | 以材料盤點與可核對書目為主；不能完成的關卡明確停下 |
| 提取 `partial`／`failed` | 先縮小範圍或降低模式，再依成功位置處理，不以五階段名稱掩蓋缺口 |

## 不可跨越的證據界線

1. 只有實際讀到的材料才算已讀。模型既有知識不是已查閱的公開資料。
2. `coverage` 要列出要求範圍、已讀、未讀、失敗位置、依據類型與限制。
3. 來源主張連到可回查的 `source_id`；分析者推論要明示，不冒充作者原意。
4. 直接引句必須有原文與位置；轉述明標為轉述。找不到位置就不要當引句交付。
5. 不虛構版本、頁碼、章節、外部來源、讀者經驗或個人化效果。
6. 缺少來源、範圍或必要欄位時讓契約拒絕，不補造相容資料。
7. 未讀章節只能標示未確認與需要何種材料；即使使用「可能」「也許」或保留語氣，也不得猜測該章內容、功能或會解決什麼問題。

## 工作流程

### 1. 盤點材料與能力

- 確認輸入類型、要求範圍、可定位方式與使用者是否提供情境。
- 依要執行的功能檢查可用能力，不以檔案存在推定後端可用。
- PDF/EPUB 內容提取優先使用能成功啟動的文件轉 Markdown 能力；PDF 才能在該路徑失敗時改用 `pymupdf4llm`。
- PDF 的 `--info`、`--toc` 需要 PyMuPDF；EPUB 使用章節標題、檔案路徑或 CFI，不硬套 PDF 頁碼。
- 圖表或掃描頁需要影像閱讀能力；無法讀取就記入失敗範圍與影響。

缺能力時說明具體缺口與仍可行的選項。只有另一條路徑已確認可用時才自動回退。

### 2. 提取與長文處理

已知宿主本次可用容量時明列；未知就由腳本採保守預設，不用模型標稱 context 推測可用容量。

```bash
python scripts/extract-text.py book.pdf --info --usable-context-tokens 120000
python scripts/extract-text.py book.pdf -o book.md
```

需要分塊時先取得目錄，再依可回查範圍提取：

```bash
python scripts/extract-text.py book.pdf --toc
python scripts/extract-text.py book.pdf --chunk-size 50 --output-dir ./chunks
```

每批筆記保留來源位置、關鍵定義、論點、反證、未解問題及無法讀取的內容。整合時回查關鍵原文，重建跨章關係與矛盾，不把多份摘要直接拼接。

提取回傳 `status: complete|partial|failed`、`success`、`chunks` 與 `failed_ranges`。只有要求範圍全數成功且內容非空白，`success` 才能是 `true`。

### 3. 僅書名時尋找可合法使用的全文

需要時載入 [references/ebook-library.md](references/ebook-library.md)。使用原始書名搜尋公共領域書庫，核對書名、作者與版本；不要自行翻譯或拼音化後把相似結果當同一本書。

找到全文才進入相應範圍的完整分析。沒有全文時改為 `preliminary`：

- 查閱到的書目或出版資料列為 `public_metadata`。
- 沒有實際查閱資料時使用 `none`。
- 不生成逐章細節、引句或完整閱讀結論。

### 4. 選擇閱讀分支並完成 CRISP 分析

進入分析前載入 [references/analysis.md](references/analysis.md)，依 Comprehend → Review → Internalize → Synthesize → Practice 完成內部分析，再把結果映射到既有 JSON 欄位。各關卡的詳細工作與完成條件以該參考檔為準。

- `nonfiction`：結構、論點、證據、假設、替代解釋與適用邊界。
- `literature`：敘事結構、人物、語言、意象、主題與其他可成立的詮釋；不強套科學性或行動。
- `mixed`：分開處理論證與文學性內容，不用同一標準硬評全部段落。

重要反例、矛盾或限制不受固定篇幅與項目數排除。事實查核與公眾評價是不同工作：前者核對可驗證主張，後者整理讀者或評論界反應；公眾評價只在使用者明確要求時執行。

後一關不能用流暢文字補回前一關缺少的基礎。沒有可核對材料時，不生成跨章合成；沒有讀者情境時，不生成個人化 Practice；無法完成的關卡要反映在 coverage、限制或空的 optional 欄位。

### 5. 產出並驗證資料

產出 JSON 前載入 [references/json-schema.md](references/json-schema.md)，保留 JSON 檔案或 stdin 入口，先驗證再渲染：

```bash
python scripts/render-report.py analysis.json --validate
python scripts/render-report.py analysis.json -o reading-report-{slug}.html
```

驗證失敗就修正資料，不輸出半成品 HTML。HTML 模板由 renderer 載入；正常分析不需讀模板。只有修改 UI 時才載入 [references/design-spec.md](references/design-spec.md)。

### 6. 檢查實際交付

- 頁首可看出模式、閱讀範圍與限制。
- 論點、引述與來源可互相回查。
- optional section 沒有內容時不顯示空標題。
- TIPS 狀態與理由沒有在 HTML、Markdown 或列印中遺失。
- 完整 HTML 可離線閱讀；必要時實際開啟、匯出或列印檢查。

## TIPS 四維度

每個維度獨立呈現，不加總、不映射固定好書等級：

| 維度 | 代號 | 判斷問題 |
|---|---|---|
| 工具性 | T | 是否提供可執行、可檢驗的方法 |
| 啟發性 | I | 相對已知背景，是否帶來新的理解角度 |
| 實用性 | P | 對已知讀者情境是否有幫助 |
| 科學性 | S | 可驗證主張的證據與推論品質如何 |

`assessed` 使用 1–3 分並附理由；資訊不足用 `unknown`，不適用用 `not_applicable`，兩者 `score` 都是 `null`。未提供讀者背景時，P 通常是 `unknown`；無法判斷相對新穎性時，I 也可以是 `unknown`。文學作品的 S 可以是 `not_applicable`。

## 個人化、筆記與應用

- 有讀者情境時才能把應用連到其實際目標或限制。
- 沒有讀者情境時，只有在適用條件、主要成本與風險都能由材料界定時，才提供明確標示的候選應用；否則 actions 留空。不能宣稱讀者已內化、承諾、會受益，或未經依據就把行動稱為低成本、低風險、可逆。
- 已有筆記時先保留原判斷與疑問，再補來源、替代解釋與跨章關係，不重頭覆寫。
- 知識連結要說明連結機制與關鍵差異；只有書名相似或泛泛「相關」不構成連結。

## 多語言與譯名

預設輸出繁體中文，原文引句保留並可附翻譯。書名、作者或延伸閱讀的繁體中文譯名只有在需要使用且能透過公開搜尋能力找到台灣出版品或可靠來源時才採用；否則保留原文，不靠記憶猜測或自行音譯。

## 參考檔案載入

| 需求 | 載入 |
|---|---|
| 產出 JSON | [references/json-schema.md](references/json-schema.md) |
| 進行分析 | [references/analysis.md](references/analysis.md) |
| 僅書名且要找全文 | [references/ebook-library.md](references/ebook-library.md) |
| 修改 HTML 或 UI | [references/design-spec.md](references/design-spec.md) |

不要一次載入所有參考檔案。主文件負責分流、證據界線、步驟與完成判準；細節只在相應分支使用。
