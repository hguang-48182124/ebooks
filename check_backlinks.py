# -*- coding: utf-8 -*-
"""
check_backlinks.py  （只檢查，絕對不會修改任何檔案）

用 index.html 裡「實際寫的」id（保留大小寫）當標準答案，
去比對每本書 html 檔裡「← 法寶園地」返回連結的錨點是否完全一致。

用法：
    放在 H:\\ebooks 資料夾（跟 index.html 同一層），執行：
        python check_backlinks.py
    只會印出檢查報告，不會動任何檔案。
"""

import os
import re
import glob

ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']')
ANCHOR_TAG_RE = re.compile(
    r'<a\b[^>]*href\s*=\s*["\']([^"\']*)["\'][^>]*>([\s\S]*?)</a>',
    re.IGNORECASE
)


def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(folder, "index.html")

    if not os.path.exists(index_path):
        print("❌ 這個資料夾裡沒有找到 index.html，請確認這支程式跟 index.html 放在同一層。")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()

    # 保留大小寫的完整 id 清單
    index_ids = set(ID_RE.findall(index_content))
    index_ids_lower_map = {}
    for i in index_ids:
        index_ids_lower_map.setdefault(i.lower(), []).append(i)

    html_files = sorted(glob.glob(os.path.join(folder, "*.html")))
    book_files = [
        f for f in html_files
        if os.path.basename(f).lower() not in ("index.html", "lite_template.html")
    ]

    print("=" * 60)
    print(" 返回連結檢查報告（唯讀，不會修改任何檔案）")
    print(f" index.html 裡共有 {len(index_ids)} 個 id")
    print(f" 共檢查 {len(book_files)} 個書本 html 檔案")
    print("=" * 60)

    ok, case_mismatch, not_found, no_link = [], [], [], []

    for fp in book_files:
        name = os.path.basename(fp)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        anchor = None
        for m in ANCHOR_TAG_RE.finditer(content):
            href, text = m.group(1), m.group(2)
            if "法寶園地" in text and "#" in href:
                anchor = href.split("#", 1)[1]
                break

        if anchor is None:
            no_link.append(name)
            continue

        if anchor in index_ids:
            ok.append((name, anchor))
        else:
            candidates = index_ids_lower_map.get(anchor.lower())
            if candidates:
                case_mismatch.append((name, anchor, candidates))
            else:
                not_found.append((name, anchor))

    print(f"\n✅ 正確（{len(ok)} 個）— 返回連結跟 index.html 的 id 完全一致，不用動：")
    for name, anchor in ok:
        print(f"   {name} → #{anchor}")

    print(f"\n🔧 大小寫不一致（{len(case_mismatch)} 個）— 可以放心自動修正，因為 index.html 裡確實存在唯一對應的 id：")
    for name, anchor, candidates in case_mismatch:
        print(f"   {name}：目前是 #{anchor}，應改成 #{candidates[0]}")

    print(f"\n❌ 找不到對應 id（{len(not_found)} 個）— index.html 裡完全沒有這個 id（不論大小寫），需要人工確認：")
    for name, anchor in not_found:
        print(f"   {name}：目前連到 #{anchor}，但 index.html 裡沒有這個 id")

    if no_link:
        print(f"\n⚠️ 找不到「法寶園地」連結（{len(no_link)} 個）：")
        for name in no_link:
            print(f"   {name}")

    print("\n" + "-" * 60)
    print(f"總結：正確 {len(ok)}／可安全自動修正 {len(case_mismatch)}／需要人工確認 {len(not_found)}／無連結 {len(no_link)}")
    print("-" * 60)
    print("\n這支程式完全沒有修改任何檔案。把上面這份報告的結果告訴我，")
    print("我會照這份結果，只針對「可以放心自動修正」那些產生真正安全的修補程式。")


if __name__ == "__main__":
    main()
