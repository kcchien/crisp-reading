# 公開電子書來源

書名模式下，嘗試從公開書庫自動取得全文。以下按自動化可行性分級。

## 可自動搜尋（有 API 或結構化查詢介面）

優先順序由上至下。找到匹配結果即停止搜尋。

| 書庫 | API / 查詢方式 | 格式 | 收錄範圍 |
|------|---------------|------|---------|
| Project Gutenberg | Gutendex API：`https://gutendex.com/books/`（見下方） | TXT, EPUB | 公共領域電子書；數量與語種依當次查詢 |
| Standard Ebooks | 網頁查詢：`https://standardebooks.org/ebooks?query={書名}` | EPUB | 公共領域書籍高品質重製版，僅英文書 |
| Open Library | API：`curl -s "https://openlibrary.org/search.json?title={書名}"` → 可取得書籍資訊與借閱連結 | EPUB, PDF | 數百萬冊，借閱制（需登入），部分可直接下載 |

### Gutendex API 搜尋指引

保留使用者提供的原文書名搜尋；需要縮小語種時加 `languages`，不要自行翻譯或拼音化後假裝匹配。

```
# 中文書（保留原書名，可加語言篩選）
https://gutendex.com/books/?languages=zh&search=老殘遊記

# 英文書（不需要 languages 參數）
https://gutendex.com/books/?search=great+gatsby

# 錯誤做法：自行翻譯或拼音化後，把相似結果當成同一本書
https://gutendex.com/books/?search=lao+can+travels
```

**搜尋規則**：
1. 使用原始書名；結果過廣或語種混雜時再加 `languages`
2. **嚴禁自行翻譯書名**：不要把中文書名翻成英文或拼音再搜尋，直接用原始書名
3. 若書名是日文，加 `languages=ja`；其他語言同理

### 完整搜尋範例

```bash
# 書名搜尋；中文書可另加：--data-urlencode 'languages=zh'
book_title='Pride and Prejudice'
response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT

if ! content_type="$(curl --fail --silent --show-error --location \
  --retry 2 --retry-delay 1 --max-time 30 \
  --user-agent 'CRISP-Reading/1.0' \
  --header 'Accept: application/json' \
  --get \
  --data-urlencode "search=${book_title}" \
  --output "$response_file" \
  --write-out '%{content_type}' \
  'https://gutendex.com/books/')"; then
  echo 'Gutendex 存取失敗；記錄原因後查下一順位書庫。' >&2
  exit 1
fi

case "$content_type" in
  application/json*) ;;
  *) echo "Gutendex 回傳非 JSON：$content_type" >&2; exit 1 ;;
esac

python3 - "$response_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as source:
    data = json.load(source)
print(f'找到 {data["count"]} 筆結果')
for book in data.get('results', []):
    print(f"ID: {book['id']}, Title: {book['title']}, Author: {book['authors'][0]['name'] if book['authors'] else 'Unknown'}")
    formats = book.get('formats', {})
    for fmt in ['text/plain; charset=utf-8', 'text/plain', 'application/epub+zip']:
        if fmt in formats:
            print(f"  {fmt}: {formats[fmt]}")
PY
```

使用 canonical `/books/` endpoint、讓 `curl` 跟隨轉址，並明確帶入 `User-Agent` 與 `Accept`。部分執行環境的預設 HTTP client 識別會被 Cloudflare 拒絕；書名與語言參數一律交給 `--data-urlencode`，避免空白或非 ASCII 書名破壞查詢。

**回傳結果處理**：
1. 只有 HTTP 請求成功且內容可解析為 JSON，才檢查 `results`；有效 JSON 的 `count: 0` 才代表 Gutendex 沒有結果
2. HTTP 4xx/5xx、轉址失敗、逾時或 JSON 解析失敗都屬於來源存取失敗；記錄原因後查下一順位書庫，不得當成零筆結果
3. 比對候選書名與作者，確認匹配後才停止搜尋
4. 優先取 `text/plain; charset=utf-8` 格式（可直接讀取，無需轉換）
5. 次選 `application/epub+zip`（需 extract-text.py 處理）
6. 下載並驗證全文後進入標準分析流程

## 手動推薦（自動搜尋無結果時，告知使用者可自行查找）

以下書庫提供可下載的電子書，但無穩定 API，需使用者自行操作：

| 書庫 | URL | 格式 | 說明 |
|------|-----|------|------|
| Internet Archive | https://archive.org | 多格式 | 數百萬冊掃描書與公共領域書籍 |
| ManyBooks | https://manybooks.net | EPUB, PDF | 50,000+ 冊多格式公共領域書 |
| Feedbooks | https://www.feedbooks.com | EPUB | 公共領域 + 獨立作者授權作品 |
| Obooko | https://www.obooko.com | EPUB, PDF | 作者主動授權的免費書籍 |
| Smashwords | https://www.smashwords.com | 多格式 | 自助出版平台，部分免費 |
| Baen Free Library | https://www.baen.com/library | EPUB, MOBI | 出版社釋出的科幻奇幻作品 |
| HathiTrust | https://www.hathitrust.org | PDF | 學術機構聯合，公共領域部分可下載 |
| Wikibooks | https://en.wikibooks.org | EPUB, PDF | 開放教科書與教學材料 |
| Wikisource | https://wikisource.org | 多格式 | 歷史文獻與文學文本，多語言 |

## 定位與失敗處理

- 下載前記錄書名、作者、版本或來源頁；取得全文後再把實際可回查位置寫入 `sources` 與 `coverage`。
- PDF 記錄實際 PDF 頁次；若頁面印有不同頁碼，另列印刷頁碼，兩者不可混用。
- EPUB 使用章節標題、檔案路徑或 EPUB CFI 等自身可定位結構，不以 PDF `--info` 或章節序號冒充頁碼。
- 圖表或掃描頁需要視覺讀取；PDF 提取另以 `coverage_verified` 記錄逐頁文字檢查。原生文字為空且沒有可回查的逐頁 OCR 證據時，該頁列入 `failed_ranges`，下游只能交付 partial。

## 限制說明

- 公共領域狀態依作品、版本、地區與來源標示查驗；搜尋到可下載檔案不等於可任意再散布
- 現代書籍（商業、自我成長、科普）幾乎不在這些書庫中
- 此功能為**錦上添花**：取得全文才可依全文分析。無全文時改為 preliminary；只陳述已實際查閱的公開資料，模型既有知識不算已查閱來源。
