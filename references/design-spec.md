# HTML 報告產出指引

> 互動式單頁閱讀報告，含深色模式與 Copy as Markdown。填充模板時，嚴格遵循以下規範。

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

> **注意**：僅在需要理解或修改 HTML 結構時才讀取模板檔案。正常分析流程不需要載入。

## 模板區塊與內容對應

| Placeholder | 說明 |
|-------------|------|
| `{{BOOK_TITLE}}` | 書名 |
| `{{BOOK_AUTHOR}}` | 作者（若有中文譯名則顯示為「中文譯名（原文）」） |
| `{{ONE_LINE_REVIEW}}` | 一句話評價（15-25 字） |
| `{{BOOK_TYPE_TAG}}` | 書的類型標籤 |
| `{{BOOK_INTRODUCTION}}` | 書籍簡介（3-5 句），位於 header 下方 |
| `{{TIPS_SCORES_HTML}}` | TIPS 四維度評分區塊（含圓點指示器與等級表） |
| `{{CORE_ARGUMENTS_HTML}}` | 用 `details.argument` 可展開結構（見模板範例） |
| `{{KEY_CONCEPTS_HTML}}` | 用 `div.concept` 垂直列表（見模板範例） |
| `{{QUOTES_HTML}}` | 用 `blockquote.quote` 結構（見模板範例） |
| `{{ACTION_CARDS_HTML}}` | 用 `div.action-item` 結構，CSS 自動編號（見模板範例） |
| `{{CONCEPT_RELATIONS_SVG}}` | 內嵌 SVG（使用固定色板，見下方） |
| `{{CRITICAL_PERSPECTIVES_HTML}}` | 純散文 h3 分段 |
| `{{META_KNOWLEDGE_HTML}}` | 思維模型區塊，用 `div.meta-item` |
| `{{ZETTELKASTEN_HTML}}` | 用 `li` 列表 |
| `{{FURTHER_READING_HTML}}` | 用 `div.further-item` |
| `{{GENERATION_DATE}}` | YYYY-MM-DD 格式 |

## 書籍簡介區塊

- 位於 header 之後、TIPS 評分之前
- 安靜的段落式呈現，與「靜謐書房」風格一致
- 使用 serif 字體，色彩採用 `--color-body`

## TIPS 評分區塊

- 位於書籍簡介之後、toolbar 之前
- 每個維度顯示：維度中文名 + 圓點指示器（● 實心 = 已得分，○ 空心 = 未得分，共 3 顆）
- 圓點用 accent 色（`--color-accent`），空心用 muted 色（`--color-muted`）
- 總分以「N / 12」格式顯示，附簡評文字
- 底部附評分等級參考表：`4-5 一般 | 6-8 好書 | 9-12 非常值得深讀`
- 視覺風格：克制，不用彩色條/圖表

## 工具列按鈕

- 所有按鈕統一為 **icon + 文字** 格式，使用 `.toolbar-btn` 類別
- 複製為 Markdown：剪貼簿 SVG icon + 「複製為 Markdown」文字
- 深色/淺色模式切換：月亮/太陽 icon + 「深色模式」/「淺色模式」文字
- JS 邏輯：Copy 按鈕複製後顯示「已複製」回饋（2 秒後恢復）

## 色彩與主題

所有 design token 定義在模板的 `:root` CSS 變數中，**以模板為 source of truth**。填充模板時不修改 CSS 變數。

- 預設跟隨系統偏好（`prefers-color-scheme`）
- 使用者可透過工具列按鈕手動切換
- 深色模式不是把淺色反轉——而是模擬夜晚書房的暖色調光
- accent 色只用於：引句左邊線、section label、行動編號、tab 底線、TIPS 分數圓點

### 概念關係圖 SVG 固定色板

SVG 內不支援 CSS 變數，使用以下**固定色板**（深色節點 + 淺色文字風格）。Claude 產出 SVG 時**必須從此色板中選色**：

**節點色板（背景 / 文字 / 邊框）：**

| 用途 | 背景 | 文字 | 邊框 |
|------|------|------|------|
| 主要/核心概念 | `#1e293b` | `#f8fafc` | `#334155` |
| 紅色系 | `#7f1d1d` | `#fecaca` | `#991b1b` |
| 綠色系 | `#14532d` | `#bbf7d0` | `#166534` |
| 藍色系 | `#1e3a5f` | `#bfdbfe` | `#1e40af` |
| 紫色系 | `#4a1d6e` | `#e9d5ff` | `#6b21a8` |
| 棕色系 | `#713f12` | `#fde68a` | `#92400e` |
| 灰色系 | `#374151` | `#e5e7eb` | `#4b5563` |

**連接線與標註：**
- 箭頭/連接線：`#64748b`，寬度 `1.5px`
- 標註文字：`#94a3b8`，字號 `10px`
- 箭頭用 `marker-end`，fill 同線色

**共同規則：**
- 節點圓角 `rx="8"`
- 節點字號 `13-14px`，sans-serif
- SVG 外層已有 `.relations` 背景色（`--color-accent-light`），不需要在 SVG 內加背景
- 同一張圖中，每個節點選用不同色系以增加辨識度
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
- 列印時：隱藏 toolbar 和 tab 導航，展開所有收合區塊，強制淺色模式

## 產出條件

所有模式均產出 HTML 報告（見 SKILL.md 決策矩陣）。
