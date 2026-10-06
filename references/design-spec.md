# HTML 報告產出指引

> 單頁、可離線、可連續閱讀的 CRISP 報告。模板的 CSS、HTML 結構與互動行為是介面 source of truth；分析資料先通過 `report_contract.py` 才能交付。

## 設計方向：靜謐書房

像精裝書內頁，而不是儀表板：內容優先、單一 accent 色、留白充足。不要加入陰影、漸層、懸浮位移、彩色徽章、圓角卡片 grid 或 emoji 圖示。

## 正常產出流程

1. 依 `references/json-schema.md` 建立分析 JSON。
2. 先驗證：`python scripts/render-report.py --validate analysis.json`。
3. 再輸出：`python scripts/render-report.py analysis.json -o report.html`。

正常分析不需讀取模板；只有修改 renderer 或 UI 時才讀 `assets/reading-report-template.html`。

## 頁面閱讀順序

1. 標題、作者、報告模式與一句話評價。
2. 閱讀範圍：要求範圍、已讀、未讀、失敗位置、依據類型、限制。
3. 工具列：複製 Markdown、下載 Markdown、主題切換。
4. 只列出實際存在區塊的本頁目錄。
5. 連續正文：核心分析、概念、批判或文學詮釋、TIPS、引述、可選內容、來源。

正文不使用 tabs、收合或預設隱藏。無內容的 optional section 連標題也不輸出；重大缺漏則留在閱讀範圍區，不可用隱藏區塊掩蓋。

## 可見語意

- 完整、初步、快速與筆記模式必須在頁首可辨識。
- 每項來源主張與分析者推論要標示類型並連到來源清單。
- 直接引句標示「原文引句」及位置；轉述不得包裝成逐字引句。
- TIPS 逐項顯示狀態、1–3 分（若可評）與理由；沒有總分、固定等級或總結 verdict。
- `unknown` 顯示「未知」，`not_applicable` 顯示「不適用」。
- 文學分支以「詮釋與其他讀法」呈現，不強制行動建議或科學性評分。
- 未提供讀者情境時，行動只能命名為「候選應用」。

## 安全邊界

- 一般文字一律 escape。
- 只有分析正文需要有限 rich text；renderer 使用 allowlist 保留必要段落、清單、表格與少數 inline 標籤。
- 移除 script、event handler、`javascript:` URL、外部嵌入與任意 SVG。
- 來源 URL 只允許 `http`、`https`、`mailto` 或頁內 fragment。
- 允許的表格包在可聚焦、帶有可存取名稱的局部水平捲動區；整頁不得水平溢位。

## 工具列與漸進增強

- 按鈕皆為 icon 加文字，觸控高度至少 44px。
- Copy 只有在 Clipboard API 或 `execCommand("copy")` 明確成功時才顯示成功。
- Copy 失敗時顯示可選取的 Markdown，並保留下載選項。
- 下載使用自包含 Markdown Blob，檔名由報告 slug 決定。
- JavaScript 關閉時仍保留完整正文、來源、列印與手動選取能力。
- 跳至主要內容連結的目標可取得鍵盤焦點。

## 色彩與排版

所有 design token 定義於模板 `:root`，填充資料時不修改：

- 版心最大寬度 660px。
- 正文使用 serif，控制與 metadata 使用 sans-serif。
- 淺色與深色都是暖色系；深色不是機械反相。
- accent 只用於連結、引句線、分數與少量狀態。
- 文字、連結與狀態色需保持可讀對比；focus outline 必須清楚。
- 長 URL、識別字與位置只在標記為 `.breakable` 的位置斷行，不對整頁使用 `word-break: break-all`。

## 響應式、縮放與表格

- 640px 以下縮小頁面 padding、將範圍 metadata 改成單欄、工具列換行、目錄改為單欄。
- 320px 與 390px 寬度下，頁面本身不得水平捲動。
- 200% 等效回流時保留正文、控制與 focus 可見性。
- 表格欄位維持最低可讀寬度，必要時只讓 `.table-scroll` 局部捲動。

## 列印

- 隱藏工具列、skip link 與「回到目錄」。
- 強制使用可列印的淺色 token，但不以 JavaScript 改寫使用者主題狀態。
- 盡量避免標題與內容、引句、來源項目、表格跨頁斷裂。
- 列印表格取消螢幕用最小寬度，避免裁切；實際 PDF 頁面仍需人工抽查。

## Placeholder 職責

模板只接受 renderer 已產生的 HTML 片段與 escape 後文字：

| Placeholder | 內容 |
|---|---|
| `{{BOOK_TITLE}}`、`{{BOOK_AUTHOR}}` | 書籍識別資訊 |
| `{{REPORT_MODE_LABEL}}`、`{{BOOK_TYPE_TAG}}` | 報告模式與材料類型 |
| `{{ONE_LINE_REVIEW}}` | 一句話評價 |
| `{{COVERAGE_HTML}}` | 閱讀範圍與限制 |
| `{{TOOLBAR_MARKDOWN}}` | HTML attribute 已 escape 的 Markdown |
| `{{TOC_HTML}}` | 只連到存在區塊的目錄 |
| `{{SECTIONS_HTML}}` | 連續正文與來源 |
| `{{REPORT_FILENAME}}` | 下載檔名 |
| `{{GENERATION_DATE}}` | `YYYY-MM-DD` |

## 交付檢查

- 執行 renderer tests 與資料契約測試。
- 用同一組 fixtures 檢查桌面／手機、light／dark、鍵盤、Copy 成功與失敗、無 JS、下載與列印。
- 檢查長字串、寬表格、惡意 markup、未知狀態、初步報告與文學報告。
- 實際畫面與列印 PDF 是必要證據；DOM 或字串測試不能取代。
