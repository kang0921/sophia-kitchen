#!/usr/bin/env python3
"""上傳前的自動檢查：確認網頁程式沒有語法錯誤、實際跑得起來，而且每道菜的資料和圖片都齊全。

用法（在 sophia-kitchen 資料夾裡執行）：
  python3 tools/check.py

有「錯誤」時結束代碼是 1，請修好再上傳；「提醒」不影響網頁運作。
需要：node（用來檢查網頁程式和讀取資料）。
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA_NAMES = ["DATES", "CATS", "CUISINES", "CUISINE_OF", "DISHES", "COVER", "ONE_POT",
              "STAPLES", "PRICE", "KCAL", "HAS_CARB"]

errors, warnings = [], []


def statement(src, name):
    """從 `const NAME=` 開始，取到同一層的分號為止（會跳過字串裡的符號）。"""
    m = re.search(r"^const %s=" % name, src, re.M)
    if not m:
        return None
    depth, i, quote = 0, m.end(), None
    while i < len(src):
        ch = src[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == ";" and depth == 0:
            return src[m.start():i + 1]
        i += 1
    return None


def load_data(script):
    parts = []
    for name in DATA_NAMES:
        st = statement(script, name)
        if st is None:
            errors.append(f"網頁裡找不到 {name} 這份資料")
            continue
        parts.append(st)
    parts += re.findall(r"^Object\.assign\(KCAL,.*?\);$", script, re.M)
    js = "\n".join(parts) + "\nconsole.log(JSON.stringify({" + ",".join(
        f"{n}:(typeof {n}==='undefined'?null:({n} instanceof Set?[...{n}]:{n}))" for n in DATA_NAMES) + "}));"
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    if out.returncode:
        errors.append("讀取網頁資料失敗：" + out.stderr.strip().splitlines()[-1])
        return None
    return json.loads(out.stdout)


def main():
    html = (REPO / "index.html").read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    if not scripts:
        sys.exit("index.html 裡找不到網頁程式")
    script = scripts[-1]

    # 1. 語法
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(script)
    r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
    if r.returncode:
        errors.append("網頁程式有語法錯誤：\n" + r.stderr.strip())
    else:
        # 2. 實際跑一次：排六種道數的菜單、畫清單、算購物清單、分享連結
        r = subprocess.run(["node", str(REPO / "tools" / "smoke.js"), f.name], capture_output=True, text=True, timeout=120)
        if r.returncode or "OK" not in r.stdout:
            msg = [l for l in (r.stderr or r.stdout).strip().splitlines() if not l.strip().startswith("at ")]
            errors.append("網頁程式執行時出錯：\n" + "\n".join(msg[:6]))

    # 3. 資料
    d = load_data(script)
    if d:
        dishes = d["DISHES"]
        names = [x["n"] for x in dishes]
        dup = sorted({n for n in names if names.count(n) > 1})
        if dup:
            errors.append("菜名重複：" + "、".join(dup))
        cats = {c["k"] for c in d["CATS"]}
        staples = set(d["STAPLES"])
        covers = json.loads((REPO / "tools" / "covers.json").read_text(encoding="utf-8"))
        used_photos = set()
        for x in dishes:
            n = x["n"]
            if x["c"] not in cats:
                errors.append(f"{n}：分類「{x['c']}」不存在")
            if not x["p"]:
                errors.append(f"{n}：沒有照片")
            for pid in x["p"]:
                used_photos.add(pid)
                if pid not in d["DATES"]:
                    errors.append(f"{n}：照片 {pid} 沒有拍攝日期（DATES）")
                for folder in ("img", "thumb", "mini"):
                    if not (REPO / folder / f"IMG_{pid}.webp").exists():
                        errors.append(f"{n}：缺少 {folder}/IMG_{pid}.webp")
            idx = d["COVER"].get(n)
            if not idx:
                errors.append(f"{n}：沒有封面（COVER）")
            else:
                if not (REPO / "cover" / f"D{idx}.webp").exists():
                    errors.append(f"{n}：缺少封面檔 cover/D{idx}.webp")
                if idx not in covers:
                    errors.append(f"{n}：封面 {idx} 沒有寫在 tools/covers.json，之後無法重做")
            if n not in d["KCAL"]:
                errors.append(f"{n}：沒有熱量（KCAL）")
            for ing in x["i"]:
                if ing not in staples and ing not in d["PRICE"]:
                    errors.append(f"{n}：食材「{ing}」沒有價格（PRICE）")
        nameset = set(names)
        for label, keys in (("封面（COVER）", d["COVER"]), ("菜系（CUISINE_OF）", d["CUISINE_OF"]),
                            ("一鍋到底（ONE_POT）", d["ONE_POT"]), ("含飯麵（HAS_CARB）", d["HAS_CARB"])):
            extra = sorted(set(keys) - nameset)
            if extra:
                errors.append(f"{label} 裡有不存在的菜：" + "、".join(extra))
        extra = sorted(set(d["KCAL"]) - nameset)
        if extra:
            warnings.append("熱量（KCAL）裡有已經沒用到的菜：" + "、".join(extra))
        for idx, c in covers.items():
            if not (REPO / "img" / f"IMG_{c['photo']}.webp").exists():
                errors.append(f"tools/covers.json 的封面 {idx} 用的照片 {c['photo']} 不存在")
        on_disk = {p.stem[4:] for p in (REPO / "img").glob("IMG_*.webp")}
        unused = sorted(on_disk - used_photos)
        if unused:
            warnings.append("這些照片沒有用在任何一道菜：" + "、".join(unused))
        print(f"檢查了 {len(dishes)} 道菜、{len(used_photos)} 張照片、{len(d['COVER'])} 個封面")

    for w in warnings:
        print("提醒：" + w)
    for e in errors:
        print("錯誤：" + e)
    if errors:
        print(f"\n有 {len(errors)} 個錯誤，請修好再上傳。")
        sys.exit(1)
    print("全部通過，可以上傳。")


if __name__ == "__main__":
    main()
