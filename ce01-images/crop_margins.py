# -*- coding: utf-8 -*-
"""
crop_margins.py
統一裁掉整批頁面圖片「上／下」多餘的白邊（天地），左右邊不動。

特色：
    - 先只裁一張「預覽圖」讓你檢查裁得對不對，滿意了才套用到全部頁面。
    - 套用前會自動把原圖全部備份到 _天地裁切前原圖備份 資料夾，裁壞了也能救回來。
    - 裁切數值可以直接輸入像素（例如 60），也可以輸入百分比（例如 5% 代表裁掉頁面高度的 5%）。

用法：
    放進要處理的圖片資料夾（例如 H:\\flipbook-tool\\ce01-images），
    執行：python crop_margins.py
"""

import os
import glob
import shutil

try:
    from PIL import Image
except ImportError:
    print("❌ 缺少 Pillow 套件，請先執行：pip install Pillow --break-system-packages")
    raise SystemExit(1)


def parse_amount(text, page_height):
    """接受像素數字（例如 60）或百分比（例如 5%），回傳實際像素數。"""
    text = text.strip()
    if text.endswith('%'):
        pct = float(text[:-1])
        return int(round(page_height * pct / 100.0))
    return int(round(float(text)))


def crop_amount_for(text, image_height):
    """依照這張圖自己的高度，重新算出實際要裁的像素數（百分比輸入時尤其重要，
    因為封面／封底的圖片尺寸不一定跟內頁完全一樣）。"""
    return parse_amount(text, image_height) if text else 0


def ask(prompt):
    return input(prompt).strip()


def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    print("=" * 55)
    print(" 天地（上下白邊）統一裁切工具")
    print(f" 資料夾：{folder}")
    print("=" * 55)

    all_jpgs = sorted(glob.glob(os.path.join(folder, "*.jpg")))
    cover_names = ("0000.jpg", "9999.jpg")
    content_jpgs = [fp for fp in all_jpgs if os.path.basename(fp) not in cover_names]
    cover_jpgs = [fp for fp in all_jpgs if os.path.basename(fp) in cover_names]

    if not content_jpgs:
        print("這個資料夾裡沒有找到可以處理的內頁 jpg 圖片。")
        return

    print(f"共找到 {len(content_jpgs)} 張內頁圖片。")
    if cover_jpgs:
        print(f"另外偵測到封面／封底：{', '.join(os.path.basename(f) for f in cover_jpgs)}")

    sample_path = content_jpgs[0]
    with Image.open(sample_path) as im:
        w, h = im.size
    print(f"以第一張內頁 {os.path.basename(sample_path)} 為例，尺寸是 {w} x {h} 像素。\n")

    top_text = ask("要裁掉頂部多少？（可輸入像素數字，例如 60；或百分比，例如 5%；不裁直接按 Enter）：")
    bottom_text = ask("要裁掉底部多少？（同上；不裁直接按 Enter）：")

    top_px = crop_amount_for(top_text, h)
    bottom_px = crop_amount_for(bottom_text, h)

    if top_px <= 0 and bottom_px <= 0:
        print("兩邊都輸入 0 或空白，沒有要裁的內容，結束。")
        return

    if top_px + bottom_px >= h:
        print(f"❌ 頂部 + 底部要裁的量（{top_px + bottom_px}px）超過整張圖高度（{h}px），請重新執行、輸入合理的數值。")
        return

    print(f"\n將裁掉：頂部 {top_px}px、底部 {bottom_px}px（裁完高度會變成 {h - top_px - bottom_px}px，寬度不變）。")

    include_covers = False
    if cover_jpgs:
        ans = ask(f"\n是否也要用一樣的比例／像素，裁封面／封底（{', '.join(os.path.basename(f) for f in cover_jpgs)}）？(y/n)：")
        include_covers = ans.lower() == 'y'
        if not include_covers:
            print("       好的，封面／封底不會被動到。")

    targets = list(content_jpgs)
    if include_covers:
        targets += cover_jpgs

    # ---- 先產生一張預覽圖，不動到原始檔案 ----
    preview_path = os.path.join(folder, "_天地裁切_預覽.jpg")
    with Image.open(sample_path) as im:
        cropped = im.crop((0, top_px, im.width, im.height - bottom_px))
        cropped.save(preview_path, quality=95)
    print(f"\n✅ 已產生內頁預覽圖：{preview_path}")

    if include_covers:
        for cf in cover_jpgs:
            with Image.open(cf) as im:
                ct = crop_amount_for(top_text, im.height)
                cb = crop_amount_for(bottom_text, im.height)
                if ct + cb >= im.height:
                    print(f"       ⚠️ {os.path.basename(cf)} 太小，裁不了這麼多，這張會跳過。")
                    continue
                cover_preview_path = os.path.join(
                    folder, f"_天地裁切_預覽_{os.path.basename(cf)}"
                )
                cropped_cover = im.crop((0, ct, im.width, im.height - cb))
                cropped_cover.save(cover_preview_path, quality=95)
                print(f"✅ 已產生封面／封底預覽圖：{cover_preview_path}")

    print("   請先打開上面這些預覽圖檢查裁切位置對不對（會不會切到文字／圖案），確認沒問題後再繼續。")

    proceed = ask("\n預覽沒問題，要套用到全部圖片嗎？(y/n)：")
    if proceed.lower() != 'y':
        print("已取消，沒有套用到任何檔案（原圖完全沒被動到）。")
        return

    backup_dir = os.path.join(folder, "_天地裁切前原圖備份")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"\n先備份原圖到：{backup_dir} ...")
    for fp in targets:
        shutil.copy2(fp, os.path.join(backup_dir, os.path.basename(fp)))

    print("開始裁切...")
    skipped = []
    for i, fp in enumerate(targets, start=1):
        with Image.open(fp) as im:
            ft = crop_amount_for(top_text, im.height)
            fb = crop_amount_for(bottom_text, im.height)
            if ft + fb >= im.height:
                skipped.append(os.path.basename(fp))
                continue
            cropped = im.crop((0, ft, im.width, im.height - fb))
            cropped.save(fp, quality=95)
        if i % 20 == 0 or i == len(targets):
            print(f"   已處理 {i}/{len(targets)} 張...")

    print(f"\n完成！共處理 {len(targets) - len(skipped)} 張圖片。")
    if skipped:
        print(f"⚠️ 以下圖片尺寸太小、裁不了這麼多，已跳過未處理：{', '.join(skipped)}")
    print(f"原圖備份在：{backup_dir}（確認網頁顯示沒問題後可以刪除這個備份資料夾）。")
    if not include_covers and cover_jpgs:
        print("提醒：封面／封底沒有被動到（你選擇不裁），如果之後想裁，重新執行這支程式再選 y 即可。")


if __name__ == "__main__":
    main()
