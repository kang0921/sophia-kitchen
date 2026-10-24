#!/usr/bin/env python3
"""把「料理照片」資料夾裡的原始照片，做成網頁用的圖片。

產生的檔案（都是 WebP，已移除 GPS 等拍攝資訊）：
  img/IMG_xxxx.webp    點開看的大圖（長邊 1000px）
  thumb/IMG_xxxx.webp  中圖（長邊 480px）
  mini/IMG_xxxx.webp   大圖下方小圖列用的迷你圖（長邊 160px）
  cover/Dxxx.webp      每道菜的正方形封面（400x400，依 tools/covers.json 裁切）

需要：macOS 的 sips（讀 HEIC）、ImageMagick 7（magick 指令）。

用法（在 sophia-kitchen 資料夾裡執行）：
  python3 tools/build_images.py                 # 全部重做
  python3 tools/build_images.py 7308 5907       # 只重做這幾張照片（也會重做用到它們的封面）
  python3 tools/build_images.py --covers        # 只重做封面
"""
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO.parent  # 原始照片放在 sophia-kitchen 的上一層「料理照片」資料夾

# 原始照片要轉幾度才會是正的（順時針）。手機拍歪的照片在這裡加一行。
ROTATE = {
    "5974": 90, "6410": 90, "6522": 90, "4032": 180,
    "4995": 90, "6832": 270, "7308": 90, "5907": 90,
    "3212": 90, "9600": 270,
}
# 重複的照片（有標字的版本已經另外存在），不放進網頁
SKIP = {"2331", "2378", "2394"}

# 調色：自然提亮（微暖、提亮、加一點飽和與對比）
GRADE = ["-channel", "R", "-evaluate", "multiply", "1.02",
         "-channel", "B", "-evaluate", "multiply", "0.97", "+channel",
         "-sigmoidal-contrast", "2,50%", "-modulate", "103,112"]

SIZES = {"img": (1000, 70), "thumb": (480, 66), "mini": (160, 60)}


def find_sources():
    """回傳 {照片編號: 原始檔路徑或 (zip, 檔名)}。"""
    found = {}
    for f in SRC.iterdir():
        if f.suffix.lower() in (".heic", ".jpg", ".jpeg") and f.stem.upper().startswith("IMG_"):
            found[f.stem[4:]] = f
        elif f.suffix.lower() == ".zip":
            with zipfile.ZipFile(f) as z:
                for name in z.namelist():
                    p = Path(name)
                    if p.suffix.lower() == ".heic" and p.stem.upper().startswith("IMG_"):
                        found.setdefault(p.stem[4:], (f, name))
    return {k: v for k, v in found.items() if k not in SKIP}


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_photo(pid, src, tmp):
    """原始照片 → 1200px JPEG（sips）→ 轉正 → 調色 → 三種尺寸的 WebP。"""
    if isinstance(src, tuple):
        zf, name = src
        with zipfile.ZipFile(zf) as z:
            raw = tmp / f"IMG_{pid}.heic"
            raw.write_bytes(z.read(name))
    else:
        raw = src
    jpg = tmp / f"IMG_{pid}.jpg"
    run("sips", "-s", "format", "jpeg", "-s", "formatOptions", "75", "-Z", "1200", str(raw), "--out", str(jpg))
    # sips 已經把方向轉正，但會留下方向標記；-strip 拿掉標記，避免瀏覽器再轉一次
    rot = ["-rotate", str(ROTATE[pid])] if pid in ROTATE else []
    for folder, (size, q) in SIZES.items():
        out = REPO / folder / f"IMG_{pid}.webp"
        out.parent.mkdir(exist_ok=True)
        run("magick", str(jpg), "-strip", *rot, "-resize", f"{size}x{size}>", *GRADE,
            "-quality", str(q), "-define", "webp:method=6", str(out))


def build_cover(idx, info):
    """從大圖裁出正方形封面。box 是 [左, 上, 右, 下]，單位是十分之一（0～10）。"""
    src = REPO / "img" / f"IMG_{info['photo']}.webp"
    w, h = map(int, subprocess.check_output(["magick", "identify", "-format", "%w %h", str(src)]).split())
    x1, y1, x2, y2 = info["box"]
    bw, bh = (x2 - x1) / 10 * w, (y2 - y1) / 10 * h
    cx, cy = (x1 + x2) / 20 * w, (y1 + y2) / 20 * h
    side = min(max(bw, bh) * 1.03, w, h)
    bx = min(max(cx - side / 2, 0), w - side)
    by = min(max(cy - side / 2, 0), h - side)
    out = REPO / "cover" / f"D{idx}.webp"
    out.parent.mkdir(exist_ok=True)
    run("magick", str(src), "-crop", f"{int(side)}x{int(side)}+{int(bx)}+{int(by)}", "+repage",
        "-resize", "400x400", "-strip", "-quality", "72", str(out))


def main():
    args = sys.argv[1:]
    covers = json.loads((REPO / "tools" / "covers.json").read_text(encoding="utf-8"))
    only_covers = "--covers" in args
    ids = [a for a in args if not a.startswith("--")]

    if not only_covers:
        sources = find_sources()
        todo = ids or sorted(sources)
        missing = [i for i in todo if i not in sources]
        if missing:
            sys.exit("找不到這些照片：" + "、".join(missing))
        with tempfile.TemporaryDirectory() as t:
            for n, pid in enumerate(todo, 1):
                build_photo(pid, sources[pid], Path(t))
                print(f"照片 {n}/{len(todo)}：IMG_{pid}")

    cover_todo = {i: c for i, c in covers.items() if only_covers or not ids or c["photo"] in ids}
    for idx, info in cover_todo.items():
        build_cover(idx, info)
    print(f"封面：{len(cover_todo)} 張")


if __name__ == "__main__":
    main()
