#!/usr/bin/env python3
"""
從 PDF/EPUB 提取文字。
優先使用 document-to-markdown (gateway.py)，不可用時 fallback 到 pymupdf4llm。

用法：
  python extract-text.py input.pdf                    # 全書提取
  python extract-text.py input.pdf --pages 1-10       # 指定頁碼
  python extract-text.py input.pdf --toc              # 僅提取目錄結構
  python extract-text.py input.pdf --info             # 書籍基本資訊（頁數、大小）
  python extract-text.py input.pdf --chunk-size 30    # 每 30 頁一塊，輸出到目錄

輸出：Markdown 文字至 stdout（或 --output 指定檔案）
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def find_gateway():
    """尋找 document-to-markdown 的 gateway.py"""
    candidates = [
        # 同層 skill
        Path(__file__).resolve().parent.parent.parent
        / "document-to-markdown"
        / "scripts"
        / "gateway.py",
        # 使用者安裝目錄
        Path.home() / ".claude" / "skills" / "document-to-markdown" / "scripts" / "gateway.py",
    ]
    for p in candidates:
        if p.is_file():
            return str(p)
    return None


def extract_via_gateway(gateway_path, input_path, pages=None, output_path=None):
    """透過 document-to-markdown gateway.py 提取。
    一律用 stdout 模式取得內容，再由本腳本決定是否寫入檔案，
    避免 --output + --json 混用導致輸出檔只有 metadata。
    """
    cmd = [sys.executable, gateway_path, "--input", str(input_path)]
    if pages:
        cmd.extend(["--pages", pages])
    # 一律讓 gateway 輸出到 stdout，由本腳本處理寫入
    cmd.extend(["--output", "-"])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        return {"success": False, "error": result.stderr or "gateway failed"}

    content = result.stdout
    # gateway 可能輸出 JSON 或直接輸出 markdown
    try:
        data = json.loads(content)
        if data.get("success"):
            content = data.get("content", "")
        else:
            return {"success": False, "error": data.get("error", "gateway returned failure")}
    except json.JSONDecodeError:
        pass  # 直接是 markdown，使用 content as-is

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
        return {"success": True, "output_path": output_path}
    return {"success": True, "content": content}


def extract_via_pymupdf(input_path, pages=None):
    """Fallback：直接用 pymupdf4llm"""
    try:
        import pymupdf4llm
    except ImportError:
        return {
            "success": False,
            "error": (
                "需要安裝 pymupdf4llm：pip install pymupdf4llm\n"
                "或安裝 document-to-markdown skill 以獲得完整功能。"
            ),
        }

    kwargs = {}
    if pages:
        page_list = parse_page_range(pages)
        kwargs["pages"] = page_list

    try:
        text = pymupdf4llm.to_markdown(str(input_path), **kwargs)
        return {"success": True, "content": text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_page_range(pages_str):
    """解析頁碼範圍字串，如 '1-5,10,15-20' → [0,1,2,3,4,9,14,15,16,17,18,19]"""
    result = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            result.extend(range(int(start) - 1, int(end)))
        else:
            result.append(int(part) - 1)
    return sorted(set(result))


def get_pdf_info(input_path):
    """取得 PDF 基本資訊"""
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            return {"success": False, "error": "需要安裝 pymupdf：pip install pymupdf4llm"}

    doc = pymupdf.open(str(input_path))
    info = doc.metadata or {}
    page_count = len(doc)
    file_size = os.path.getsize(input_path)

    # 估算文字量（前中後分散取樣，避免封面/空白頁偏差）
    if page_count <= 10:
        sample_indices = list(range(page_count))
    else:
        # 跳過前 3 頁（封面/版權），從前段、中段、後段各取樣
        front = list(range(3, min(8, page_count)))
        mid_start = page_count // 2 - 2
        middle = list(range(max(mid_start, 0), min(mid_start + 5, page_count)))
        back_start = max(page_count - 8, 0)
        back = list(range(back_start, page_count - 1))  # 跳過最後一頁（常為空白）
        sample_indices = sorted(set(front + middle + back))
    sample_count = len(sample_indices)
    total_chars = sum(len(doc[i].get_text()) for i in sample_indices)
    avg_chars_per_page = total_chars / sample_count if sample_count > 0 else 0
    estimated_chars = int(avg_chars_per_page * page_count)
    # 粗估 token（中文約 1.5 字/token，英文約 4 字/token，取平均 2.5）
    estimated_tokens = int(estimated_chars / 2.5)

    doc.close()

    return {
        "success": True,
        "title": info.get("title", ""),
        "author": info.get("author", ""),
        "page_count": page_count,
        "file_size_mb": round(file_size / 1024 / 1024, 1),
        "estimated_chars": estimated_chars,
        "estimated_tokens": estimated_tokens,
        "needs_chunking": estimated_tokens > 80000,
        "suggested_chunks": max(1, -(-estimated_tokens // 60000)),  # 無條件進位
    }


def get_toc(input_path):
    """提取 PDF 目錄結構"""
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            return {"success": False, "error": "需要安裝 pymupdf：pip install pymupdf4llm"}

    doc = pymupdf.open(str(input_path))
    toc = doc.get_toc()
    doc.close()

    if not toc:
        return {"success": True, "toc": [], "note": "此 PDF 無內嵌目錄"}

    entries = []
    for level, title, page in toc:
        entries.append({"level": level, "title": title, "page": page})

    return {"success": True, "toc": entries}


def chunk_extract(input_path, chunk_size, output_dir, gateway_path=None):
    """分塊提取 PDF，每塊 chunk_size 頁"""
    info = get_pdf_info(input_path)
    if not info["success"]:
        return info

    page_count = info["page_count"]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chunks = []
    for start in range(1, page_count + 1, chunk_size):
        end = min(start + chunk_size - 1, page_count)
        pages = f"{start}-{end}"
        chunk_file = output_dir / f"chunk_{start:04d}-{end:04d}.md"

        if gateway_path:
            result = extract_via_gateway(
                gateway_path, input_path, pages=pages, output_path=str(chunk_file)
            )
        else:
            result = extract_via_pymupdf(input_path, pages=pages)
            if result["success"] and "content" in result:
                chunk_file.write_text(result["content"], encoding="utf-8")
                result["output_path"] = str(chunk_file)

        chunks.append({"pages": pages, "file": str(chunk_file), "success": result["success"]})

    return {"success": True, "chunks": chunks, "total_pages": page_count}


def main():
    parser = argparse.ArgumentParser(description="CRISP 閱讀助手：文件文字提取")
    parser.add_argument("input", help="PDF 或 EPUB 檔案路徑")
    parser.add_argument("--pages", "-p", help="頁碼範圍，如 1-10,15,20-25")
    parser.add_argument("--output", "-o", help="輸出檔案路徑（預設 stdout）")
    parser.add_argument("--toc", action="store_true", help="僅提取目錄結構（JSON）")
    parser.add_argument("--info", action="store_true", help="僅顯示書籍資訊（JSON）")
    parser.add_argument("--chunk-size", type=int, help="分塊頁數，自動切割並輸出到目錄")
    parser.add_argument("--output-dir", help="分塊輸出目錄（搭配 --chunk-size）")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        print(json.dumps({"success": False, "error": f"找不到檔案：{args.input}"}))
        sys.exit(1)

    ext = input_path.suffix.lower()
    is_pdf = ext == ".pdf"
    is_epub = ext == ".epub"
    gateway_path = find_gateway()

    # EPUB 需要 gateway；若不可用，提前告知
    if is_epub and not gateway_path:
        print(json.dumps({
            "success": False,
            "error": (
                "EPUB 格式需要 document-to-markdown skill 的 gateway.py 才能處理。\n"
                "請安裝 document-to-markdown skill，或將 EPUB 轉換為 PDF 後重試。"
            ),
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    if not is_pdf and not is_epub:
        print(json.dumps({
            "success": False,
            "error": f"不支援的檔案格式：{ext}。僅支援 .pdf 和 .epub。",
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    # 資訊模式（僅 PDF 支援；EPUB 需透過 gateway 提取後自行評估）
    if args.info:
        if not is_pdf:
            print(json.dumps({
                "success": False,
                "error": f"--info 僅支援 PDF 格式。EPUB 請先提取文字後自行評估大小。",
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        print(json.dumps(get_pdf_info(input_path), ensure_ascii=False, indent=2))
        return

    # 目錄模式（僅 PDF 支援）
    if args.toc:
        if not is_pdf:
            print(json.dumps({
                "success": False,
                "error": f"--toc 僅支援 PDF 格式。",
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        print(json.dumps(get_toc(input_path), ensure_ascii=False, indent=2))
        return

    # 分塊模式
    if args.chunk_size:
        output_dir = args.output_dir or str(input_path.parent / f"{input_path.stem}_chunks")
        result = chunk_extract(input_path, args.chunk_size, output_dir, gateway_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 一般提取
    if gateway_path:
        result = extract_via_gateway(gateway_path, input_path, pages=args.pages, output_path=args.output)
    else:
        result = extract_via_pymupdf(input_path, pages=args.pages)

    if not result["success"]:
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    if args.output and "content" in result:
        Path(args.output).write_text(result["content"], encoding="utf-8")
        print(json.dumps({"success": True, "output_path": args.output}, ensure_ascii=False))
    elif "content" in result:
        print(result["content"])
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
