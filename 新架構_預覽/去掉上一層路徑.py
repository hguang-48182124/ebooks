# -*- coding: utf-8 -*-
# 用途：把電子書 html 裡 IMG_DIR 的 ../ 拿掉，其他內容完全不動。
# 用法：把這個檔案放進「新架構_預覽」資料夾，雙擊執行（或在該資料夾用 python 執行）。
# 結果：改好的檔案存到「已修正」資料夾，原檔不會被改動。
import os, re, sys

here = os.path.dirname(os.path.abspath(sys.argv[0]))
out_dir = os.path.join(here, "已修正")
os.makedirs(out_dir, exist_ok=True)

# 只比對 IMG_DIR 那一行：const IMG_DIR = '../xxx-images/';
pattern = re.compile(rb"(const\s+IMG_DIR\s*=\s*['\"])\.\./")

changed, skipped = [], []
for name in sorted(os.listdir(here)):
    if not name.lower().endswith(".html"):
        continue
    with open(os.path.join(here, name), "rb") as f:   # 用位元組讀，編碼、換行都不會變
        data = f.read()
    new, n = pattern.subn(rb"\1", data, count=1)
    if n == 1:
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(new)
        changed.append(name)
    else:
        skipped.append(name)

print("已修正 %d 本：" % len(changed))
for n in changed: print("  ", n)
if skipped:
    print("沒有找到 ../ 而略過 %d 個：" % len(skipped))
    for n in skipped: print("  ", n)
print("\n改好的檔案在：", out_dir)
input("\n按 Enter 結束")
