# -*- coding: utf-8 -*-
"""
fix_mobile_book_size.py — 修正「手機版書本比應有的還小」這個問題，套用到整個
資料夾裡所有書的 html（不管是很久以前上線的舊書，還是最近用
convert_old_skeleton.py 轉出來的新書，用的都是同一套共用排版邏輯，這支工具
兩種都能修）。

問題根源：
  原本手機版的浮動翻頁圓鈕是「浮在書本外側」的設計，JS 算書本寬度時要
  幫這兩顆圓鈕預留安全邊界空間——手機螢幕本來就窄，這樣白白讓書本變得
  比實際需要的小很多。但完全拿掉翻頁鈕又怕老人家不知道可以滑動/點擊
  翻頁，所以改成參考坊間電子書 App 常見的做法：**把翻頁提示疊在書本
  左右邊緣「內側」，做成半透明三角形**——不佔書本以外的任何寬度（疊在
  書本圖片上面，不會讓書本變小），同時保留清楚的視覺提示。

會套用的修正：
  1. 翻頁鈕改成疊在書本邊緣內側的半透明三角形（手機版），電腦/平板
     （≥640px）維持原本浮在外側的圓鈕不變
  2. 算書本寬度時，不用再預留翻頁鈕的安全邊界（因為疊在書本上，不佔
     額外空間）
  3. .wrap 左右留白從 16px 縮小成 10px，書本可用寬度再增加一點
  4. 寬度上限比例從 0.98 提高到 0.99
  5. 頁碼列改成緊貼書本下方，不再被強制推到畫面最底部（避免書變大後
     書跟頁碼中間留一大截空白）

用法：
  python fix_mobile_book_size.py                # 掃目前資料夾底下所有 .html
  python fix_mobile_book_size.py "H:\\某資料夾"   # 掃指定資料夾

安全機制（跟 batch_fix_layout.py 完全一樣）：
  - 每個檔案改之前都會先備份成 <檔名>.html.手機書本尺寸修正前備份.bak
    （已經有備份就不會覆蓋掉）
  - 每一步驟都只在偵測到「舊樣式」時才動手，已經是新樣式的部分會自動跳過，
    重複執行這支工具不會壞掉
  - 找不到任何一步舊樣式可套用的檔案，會標成「需要人工檢查」——通常代表
    這本書的 html 結構跟其他書不一樣（例如更早期的版型、或已經手動改過），
    這種要另外上傳給 Claude 個別看，不會硬套版面壞掉
"""
import os
import re
import sys
import glob


NAV_BTN_CANONICAL = (
    '  .nav-btn{ position:absolute; top:50%; transform: translateY(-50%); width:22px; height:36px; '
    'border:none; background:transparent; color: rgba(43,42,37,0.32); font-size:18px; font-weight:300; '
    'display:flex; align-items:center; justify-content:center; cursor:pointer; z-index:5; }\n'
    '  .nav-btn:disabled{ opacity:0.15; cursor:default; }\n'
    '  .nav-prev{ left:2px; } .nav-next{ right:2px; }\n'
    '  @media (min-width: 640px){ .nav-btn{ width:42px; height:42px; border-radius:50%; '
    'background: rgba(255,255,255,0.85); color: var(--pine-deep); font-size:18px; font-weight:400; } '
    '.nav-prev{ left: -54px; } .nav-next{ right: -54px; } }\n'
)

def fix_nav_btn_triangle(content):
    """手機版翻頁鈕統一改成貼在書本邊緣的淡色空心箭頭符號（不佔額外寬度），
    涵蓋最原始版本（浮在外側的實心圓鈕）、上一輪暫時做法（display:none
    直接隱藏）、以及再上一輪的實心三角形版本，一律升級成最新的淡箭頭版本。"""
    pattern = re.compile(r'  \.nav-btn\{.*?(?=  \.book-footer\{)', re.DOTALL)
    m = pattern.search(content)
    if not m:
        return content, 0
    if m.group(0) == NAV_BTN_CANONICAL:
        return content, 0
    new_content = pattern.sub(NAV_BTN_CANONICAL, content, count=1)
    return new_content, 1


def fix_wrap_padding_side(content):
    pattern = re.compile(
        r'(\.wrap\{ max-width: 960px; margin: 0 auto; padding: \d+px) 16px(.*?; display:flex; flex-direction:column; \})'
    )
    new_content, n = pattern.subn(r'\1 10px\2', content, count=1)
    return new_content, n


def fix_vw_frac(content):
    pattern = re.compile(r'const vwFrac = 0\.98;')
    new_content, n = pattern.subn('const vwFrac = 0.99;', content, count=1)
    return new_content, n


def fix_nav_clearance(content):
    if 'const navVisible = window.innerWidth >= 640;' in content:
        return content, 0
    pattern = re.compile(r'  const NAV_CLEARANCE = 20;\n')
    replacement = (
        "  // 翻頁圓鈕在窄螢幕（<640px）是隱藏的（改用點擊/滑動翻頁），\n"
        "  // 不需要再幫它預留安全邊界，書本可以用到更接近螢幕全寬。\n"
        "  const navVisible = window.innerWidth >= 640;\n"
        "  const NAV_CLEARANCE = navVisible ? 20 : 0;\n"
    )
    new_content, n = pattern.subn(replacement, content, count=1)
    return new_content, n


def fix_book_footer_gap(content):
    pattern = re.compile(r'\.book-footer\{ margin-top:auto; \}')
    replacement = '.book-footer{ margin-top:0; }'
    new_content, n = pattern.subn(replacement, content, count=1)
    return new_content, n


STEPS = [
    ("翻頁鈕改成貼在書本邊緣的淡色空心箭頭", fix_nav_btn_triangle),
    ("wrap 左右留白縮小",               fix_wrap_padding_side),
    ("寬度上限比例調高",                fix_vw_frac),
    ("手機版不再預留翻頁鈕安全邊界",     fix_nav_clearance),
    ("頁碼列改貼近書本、不再推到畫面最底部", fix_book_footer_gap),
]


def process_file(path):
    with open(path, 'rb') as f:
        raw = f.read().decode('utf-8')
    content = raw.replace('\r\n', '\n')

    applied = []
    skipped = []
    for label, fn in STEPS:
        content, n = fn(content)
        if n > 0:
            applied.append(label)
        else:
            skipped.append(label)

    if not applied:
        print(f"ℹ️  {os.path.basename(path)}：已經是最新版，或結構跟預期不一樣，跳過。")
        return 'uptodate_or_review'

    backup_path = path + '.手機書本尺寸修正前備份.bak'
    if not os.path.exists(backup_path):
        with open(backup_path, 'wb') as f:
            f.write(raw.encode('utf-8'))

    out = content.replace('\n', '\r\n')
    with open(path, 'wb') as f:
        f.write(out.encode('utf-8'))

    print(f"✅ {os.path.basename(path)}")
    print(f"   已套用：{'、'.join(applied)}")
    if skipped:
        print(f"   跳過（已是新版或找不到對應舊樣式）：{'、'.join(skipped)}")
    return 'updated'


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    html_files = sorted(glob.glob(os.path.join(target_dir, '*.html')))
    if not html_files:
        print(f"在「{target_dir}」裡沒找到任何 .html 檔案。")
        return

    print(f"在「{target_dir}」裡找到 {len(html_files)} 個 html 檔案，開始逐一檢查、套用手機書本尺寸修正...\n")
    updated = 0
    other = 0
    for path in html_files:
        try:
            result = process_file(path)
            if result == 'updated':
                updated += 1
            else:
                other += 1
        except Exception as e:
            print(f"❌ {os.path.basename(path)} 處理時發生錯誤：{e}（這個檔案已略過，沒有被改動）")
            other += 1
        print()

    print("=" * 60)
    print(f"完成。{updated} 個檔案已更新，{other} 個已是最新版或需要人工檢查。")
    print("每個有改動的檔案都留了一份 <檔名>.html.手機書本尺寸修正前備份.bak，")
    print("如果套用後畫面有問題，把備份檔改回原檔名就能復原。")


if __name__ == '__main__':
    main()
