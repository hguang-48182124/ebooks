# -*- coding: utf-8 -*-
"""
safe_fix_backlinks.py

只修正「大小寫不一致，但 index.html 裡確實有唯一對應 id」的返回連結。
任何 index.html 裡找不到對應 id 的情況，一律跳過、不猜、不動，只印出來讓你知道。

用法：
    放在 H:\\ebooks（跟 index.html 同一層），執行：
        python safe_fix_backlinks.py
"""

import os
import re
import glob

ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']')
ANCHOR_TAG_RE = re.compile(
    r'(<a\b[^>]*href\s*=\s*")([^"]*?)(#)([^"]*)(")([^>]*>[\s\S]*?</a>)',
    re.IGNORECASE
)


def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(folder, "index.html")

    if not os.path.exists(index_path):
        print("❌ 找不到 index.html，請確認這支程式放在跟 index.html 同一層。")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()

    index_ids = set(ID_RE.findall(index_content))
    index_ids_lower_map = {}
    for i in index_ids:
        index_ids_lower_map.setdefault(i.lower(), []).append(i)

    html_files = sorted(glob.glob(os.path.join(folder, "*.html")))
    book_files = [
        f for f in html_files
        if os.path.basename(f).lower() not in ("index.html", "lite_template.html")
    ]

    fixed, skipped_no_match, skipped_ambiguous, already_ok, no_link = [], [], [], [], []

    for fp in book_files:
        name = os.path.basename(fp)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        m_found = None
        for m in ANCHOR_TAG_RE.finditer(content):
            tail = m.group(6)
            if "法寶園地" in tail:
                m_found = m
                break

        if not m_found:
            no_link.append(name)
            continue

        anchor = m_found.group(4)

        if anchor in index_ids:
            already_ok.append(name)
            continue

        candidates = index_ids_lower_map.get(anchor.lower())
        if not candidates:
            skipped_no_match.append((name, anchor))
            continue
        if len(candidates) > 1:
            skipped_ambiguous.append((name, anchor, candidates))
            continue

        correct_id = candidates[0]
        new_full = (
            m_found.group(1) + m_found.group(2) + m_found.group(3)
            + correct_id + m_found.group(5) + m_found.group(6)
        )
        new_content = content[:m_found.start()] + new_full + content[m_found.end():]

        backup_path = fp + ".backlink修補前.bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(new_content)

        fixed.append((name, anchor, correct_id))
        print(f"🔧 {name}：#{anchor} → #{correct_id}（已修正，備份為 {os.path.basename(backup_path)}）")

    print("\n" + "-" * 55)
    print(f"已修正：{len(fixed)} 個")
    print(f"本來就正確：{len(already_ok)} 個（未動）")
    if skipped_no_match:
        print(f"⚠️ index.html 找不到對應 id，跳過未動：{len(skipped_no_match)} 個 → " +
              ", ".join(n for n, a in skipped_no_match))
    if skipped_ambiguous:
        print(f"⚠️ 對應到多個可能 id，跳過未動（需人工確認）：{len(skipped_ambiguous)} 個")
    if no_link:
        print(f"（無「法寶園地」連結，略過）：{len(no_link)} 個 → {', '.join(no_link)}")
    print("-" * 55)
    print("\n完成。確認網頁正常後，.backlink修補前.bak 備份檔可以刪除。")


if __name__ == "__main__":
    main()
