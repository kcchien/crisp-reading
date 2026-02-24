# 公開電子書來源

書名模式下，嘗試從公開書庫自動取得全文。以下按自動化可行性分級。

## 可自動搜尋（有 API 或結構化查詢介面）

優先順序由上至下。找到匹配結果即停止搜尋。

| 書庫 | API / 查詢方式 | 格式 | 收錄範圍 |
|------|---------------|------|---------|
| Project Gutenberg | Gutendex API（見下方） | TXT, EPUB | 70,000+ 冊公共領域書籍，含 444+ 冊中文古典文學 |
| Standard Ebooks | 網頁查詢：`https://standardebooks.org/ebooks?query={書名}` | EPUB | 公共領域書籍高品質重製版，僅英文書 |
| Open Library | API：`curl -s "https://openlibrary.org/search.json?title={書名}"` → 可取得書籍資訊與借閱連結 | EPUB, PDF | 數百萬冊，借閱制（需登入），部分可直接下載 |

### Gutendex API 搜尋指引

**關鍵：中文書必須加 `languages=zh` 參數，否則搜尋不到。**

Gutendex 的 `search` 參數對 CJK（中日韓）字元支援有限。不加語言過濾時，中文字元搜尋會回傳 0 筆結果。加上 `languages=zh` 後，API 能正確搜尋中文書名。

```
# 中文書（必須加 languages=zh）
https://gutendex.com/books?languages=zh&search=老殘遊記     → 3 筆結果
https://gutendex.com/books?languages=zh&search=紅樓夢       → 命中
https://gutendex.com/books?languages=zh&search=西遊記       → 命中

# 英文書（不需要 languages 參數）
https://gutendex.com/books?search=great+gatsby              → 命中

# 錯誤做法（會失敗）
https://gutendex.com/books?search=老殘遊記                   → 0 筆結果
https://gutendex.com/books?search=lao+can+travels            → 命中無關書籍
```

**搜尋規則**：
1. 判斷書名語言：中文 → 加 `languages=zh`；英文 → 不加
2. **嚴禁自行翻譯書名**：不要把中文書名翻成英文或拼音再搜尋，直接用原始書名
3. 若書名是日文，加 `languages=ja`；其他語言同理

### 完整搜尋範例

```bash
# 中文書搜尋
curl -s "https://gutendex.com/books?languages=zh&search=老殘遊記" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'找到 {data[\"count\"]} 筆結果')
for book in data.get('results', []):
    print(f\"ID: {book['id']}, Title: {book['title']}, Author: {book['authors'][0]['name'] if book['authors'] else 'Unknown'}\")
    formats = book.get('formats', {})
    for fmt in ['text/plain; charset=utf-8', 'text/plain', 'application/epub+zip']:
        if fmt in formats:
            print(f\"  {fmt}: {formats[fmt]}\")
"
```

**回傳結果處理**：
1. 檢查 `results` 陣列是否有匹配書籍（比對書名與作者）
2. 優先取 `text/plain; charset=utf-8` 格式（可直接讀取，無需轉換）
3. 次選 `application/epub+zip`（需 extract-text.py 處理）
4. 下載後直接進入標準分析流程

### Gutenberg 中文書庫概覽

Gutenberg 收錄約 444 冊中文書籍，主要為晚清至民國時期的古典文學，包括：
- 四大名著：《紅樓夢》《西遊記》《三國演義》《水滸傳》
- 晚清小說：《老殘遊記》《孽海花》《儒林外史》
- 文學評論：《中國小說史略》（魯迅）
- 歷史文獻：《漢書》《徐霞客遊記》
- 筆記小說：《閱微草堂筆記》《池北偶談》

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

## 限制說明

- 可自動搜尋的書庫主要收錄**公共領域書籍**（美國著作權法下多為 1928 年前出版）
- 現代書籍（商業、自我成長、科普）幾乎不在這些書庫中
- 此功能為**錦上添花**：碰巧有全文時提升分析品質，無全文時回退到「依公開資料」模式
