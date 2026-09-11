# -*- coding: utf-8 -*-
"""
fix_backlinks.py
一次修補多本書「← 法寶園地」返回連結大小寫錯誤的小工具。

背景：
    之前一版 make_flipbook.py 有個 bug，套版時「← 法寶園地」的返回連結
    錨點可能沒有轉成小寫，導致連結跟 index.html 的 id 對不上，
    點了跳不到書單裡正確的位置。

用法：
    1. 把這支 fix_backlinks.py 放到你那 6 本 cbXX.html 所在的資料夾
       （跟 index.html 同一層，或至少跟要修的 <書碼>.html 同一層）。
    2. cmd 切到那個資料夾，執行：
           python fix_backlinks.py
    3. 它會自動掃描資料夾裡所有 <書碼>.html（跳過 index.html 本身），
       检查「法寶園地」連結錨點是否等於檔名本身（小寫），
       不一致就直接修正，並印出修改前後對照。
    4. 每個被改到的檔案都會先備份成 <書碼>.html.backlink修補前.bak，
       確認沒問題後這些備份可以自行刪除。

安全性：
    - 只會動「法寶園地」那一個連結的 #錨點文字，其他內容完全不動。
    - 已經正確的檔案不會被改動、也不會產生備份檔。
    - index.html 本身不會被這支工具處理（它是被比對的基準，不是要修的對象）。
"""

import os
import re
import glob

ANCHOR_TAG_RE = re.compile(
    r'(<a\b[^>]*href\s*=\s*")([^"]*?)(#)([^"]*)(")([^>]*>[\s\S]*?</a>)',
    re.IGNORECASE
)


def find_backlink_and_fix(content, correct_code):
    """
    在檔案內容裡找到文字包含「法寶園地」的 <a> 連結，
    檢查它的 #錨點是否等於 correct_code（忽略大小寫比對，但修正後一律小寫）。
    回傳 (new_content, changed, old_anchor) — changed 為 False 代表沒找到或不需要改。
    """
    matches = list(ANCHOR_TAG_RE.finditer(content))
    for m in matches:
        tag_and_after = m.group(6)
        if "法寶園地" not in tag_and_after:
            continue
        old_anchor = m.group(4)
        if old_anchor == correct_code:
            return content, False, old_anchor
        new_full = m.group(1) + m.group(2) + m.group(3) + correct_code + m.group(5) + m.group(6)
        new_content = content[:m.start()] + new_full + content[m.end():]
        return new_content, True, old_anchor
    return content, None, None  # None = 完全找不到這個連結，需要人工看一下


def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    print("=" * 55)
    print(" 返回連結大小寫 一次修補工具")
    print(f" 掃描資料夾：{folder}")
    print("=" * 55)

    html_files = sorted(glob.glob(os.path.join(folder, "*.html")))
    html_files = [
        f for f in html_files
        if os.path.basename(f).lower() != "index.html"
        and os.path.basename(f).lower() != "lite_template.html"
    ]

    if not html_files:
        print("\n沒有找到任何要檢查的書本 html 檔案（已排除 index.html / lite_template.html）。")
        return

    fixed = []
    already_ok = []
    not_found = []

    for fp in html_files:
        name = os.path.basename(fp)
        book_code = os.path.splitext(name)[0].lower()

        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        new_content, changed, old_anchor = find_backlink_and_fix(content, book_code)

        if changed is None:
            not_found.append(name)
            print(f"⚠️ {name}：找不到「法寶園地」返回連結，請人工看一下這個檔案。")
            continue

        if changed is False:
            already_ok.append(name)
            print(f"✅ {name}：返回連結已經是 #{old_anchor}，正確，不需要修改。")
            continue

        backup_path = fp + ".backlink修補前.bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)

        with open(fp, "w", encoding="utf-8") as f:
            f.write(new_content)

        fixed.append((name, old_anchor, book_code))
        print(f"🔧 {name}：#{old_anchor}  →  #{book_code}（已修正，原始版本備份為 {os.path.basename(backup_path)}）")

    print("\n" + "-" * 55)
    print(f"共檢查 {len(html_files)} 個檔案：")
    print(f"  已修正：{len(fixed)} 個")
    print(f"  本來就正確：{len(already_ok)} 個")
    if not_found:
        print(f"  找不到返回連結、需要人工確認：{len(not_found)} 個 → {', '.join(not_found)}")
    print("-" * 55)
    print("\n完成。確認網頁上返回連結能正確跳到書單位置後，")
    print("可以把產生的 .backlink修補前.bak 備份檔刪掉。")


if __name__ == "__main__":
    main()
