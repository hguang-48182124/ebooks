# -*- coding: utf-8 -*-
"""
restore_backlinks.py
把 fix_backlinks.py 改過的檔案，全部還原回修改前的樣子。

用法：
    放在跟 .backlink修補前.bak 備份檔同一個資料夾（就是 H:\\ebooks），
    執行：python restore_backlinks.py
    它會找出所有 *.backlink修補前.bak，把內容寫回對應的原始檔名，
    然後把 .bak 檔刪掉。
"""

import os
import glob

def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    bak_files = sorted(glob.glob(os.path.join(folder, "*.backlink修補前.bak")))

    if not bak_files:
        print("沒有找到任何 .backlink修補前.bak 備份檔，可能已經還原過了，或本來就沒有備份。")
        return

    print(f"找到 {len(bak_files)} 個備份檔，開始還原...\n")
    restored = 0
    for bak in bak_files:
        original = bak[:-len(".backlink修補前.bak")]
        if not os.path.exists(original):
            print(f"⚠️ 找不到對應的原始檔案：{os.path.basename(original)}，跳過。")
            continue
        with open(bak, "r", encoding="utf-8") as f:
            content = f.read()
        with open(original, "w", encoding="utf-8") as f:
            f.write(content)
        os.remove(bak)
        restored += 1
        print(f"↩️  {os.path.basename(original)}：已還原成修改前的內容，備份檔已刪除。")

    print(f"\n完成，共還原 {restored} 個檔案。所有連結都回到修改前的原始狀態了。")

if __name__ == "__main__":
    main()
