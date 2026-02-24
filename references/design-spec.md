# HTML 報告產出指引

> 互動式單頁閱讀報告，含精華版/完整版切換與深色模式。填充模板時，嚴格遵循以下規範。

---

## 設計哲學：靜謐書房

像翻開一本精裝書的內頁。安靜、克制、讓內容自己說話。

**三個原則：**
1. **內容優先** — 排版服務於閱讀，不服務於裝飾
2. **克制** — 只用一個 accent 色，只用必要的視覺元素
3. **呼吸** — 慷慨的留白，讓每個段落都有空間

## 模板位置與使用流程

模板：`assets/reading-report-template.html`（由 render-report.py 自動讀取並填充，Claude 不需要載入模板檔案）

1. Claude 產出分析 JSON（依 json-schema.md）
2. 執行 `python scripts/render-report.py analysis.json -o report.html`
3. 腳本自動讀取模板、填充、輸出 HTML

> **注意**：僅在需要理解或修改 HTML 結構時才讀取模板檔案（851 行）。正常分析流程不需要載入。

## 模板區塊與內容對應

| Placeholder | 深度 | 說明 |
|-------------|------|------|
| `{{BOOK_TITLE}}` | 全部 | 書名 |
| `{{BOOK_AUTHOR}}` | 全部 | 作者 |
| `{{ONE_LINE_REVIEW}}` | 全部 | 一句話評價（15-25 字） |
| `{{BOOK_TYPE_TAG}}` | 全部 | 書的類型標籤 |
| `{{CORE_ARGUMENTS_HTML}}` | 精華版 | 用 `details.argument` 可展開結構（見模板範例） |
| `{{KEY_CONCEPTS_HTML}}` | 精華版 | 用 `div.concept` 垂直列表（見模板範例） |
| `{{QUOTES_HTML}}` | 精華版 | 用 `blockquote.quote` 結構（見模板範例） |
| `{{ACTION_CARDS_HTML}}` | 精華版 | 用 `div.action-item` 結構，CSS 自動編號（見模板範例） |
| `{{CONCEPT_RELATIONS_SVG}}` | 完整版 | 內嵌 SVG，包在 `[data-depth="deep"]` 內 |
| `{{CRITICAL_PERSPECTIVES_HTML}}` | 完整版 | 純散文 h3 分段，整個 panel 是 `[data-depth="deep"]` |
| `{{ZETTELKASTEN_HTML}}` | 完整版 | 用 `li` 列表，包在 `[data-depth="deep"]` 的 section 內 |
| `{{FURTHER_READING_HTML}}` | 完整版 | 用 `div.further-item`，包在 `[data-depth="deep"]` 的 section 內 |
| `{{GENERATION_DATE}}` | 全部 | YYYY-MM-DD 格式 |

**內容分配原則**：精華版呈現核心價值（論點、概念、金句、行動），完整版補充深度分析（批判、關係圖、知識連結、延伸閱讀）。

## 深度切換

模板內建「精華版 / 完整版」切換，透過 `data-depth` 和 `data-view` 屬性控制：

- `[data-depth="deep"]` 元素只在完整版可見
- 切換時自動處理 tab 可見性（隱藏的 tab 不可選取）
- 列印時強制展開所有深度內容

## 色彩與主題

所有 design token 定義在模板的 `:root` CSS 變數中，**以模板為 source of truth**。填充模板時不修改 CSS 變數。

- 預設跟隨系統偏好（`prefers-color-scheme`）
- 使用者可透過工具列按鈕手動切換
- 深色模式不是把淺色反轉——而是模擬夜晚書房的暖色調光
- accent 色只用於：引句左邊線、section label、行動編號、tab 底線、depth toggle 選中態

### 概念關係圖 SVG 配色

SVG 內不支援 CSS 變數，需硬編碼淺色模式色值：
- 節點文字 `#1c1917`、連接線 `#d6d3d1`、節點背景 `#f5f0e8`、節點邊框 `#8d7048`
- 線條寬度：1px，箭頭用 marker-end
- SVG 不需要支援深色模式（被 `.relations` 背景包裹，視覺上已統一）

## 填充規則

- 所有內容用自然語言，不含方法論術語
- 引述翻譯：英文原文 + 中文翻譯並列，都放在 `quote__text` 內
- HTML 安全：所有使用者內容需轉義特殊字元
- 保持模板的內嵌 CSS 和 JS 不變，只替換內容區塊
- **嚴格遵守禁止清單**（見下方）

## 禁止清單

| 禁止項目 | 原因 |
|---------|------|
| Emoji 作為圖示 | 破壞排版的安靜感 |
| 卡片陰影（box-shadow） | 增加視覺噪音 |
| 懸停浮起效果（translateY） | 不必要的花俏 |
| 漸層背景 | 分散注意力 |
| 彩色標籤/徽章 | 色彩應該極度克制 |
| 圓角卡片 grid 排列 | 像儀表板，不像書 |
| 粗體邊框或裝飾線 | 保持安靜 |
| 超過一個 accent 色 | 克制是核心 |

## 響應式與列印

- 640px 以下：字級降 1px、頁面 padding 收縮、tab 間距縮小、toolbar 自動換行
- 列印時：隱藏 toolbar 和 tab 導航，展開所有收合區塊和 deep 內容，強制淺色模式

## 產出條件

除「快速評估」外，所有模式均產出 HTML 報告（見 SKILL.md「觸發與深度」表）。
