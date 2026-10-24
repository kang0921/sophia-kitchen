# Sophia 的廚房：怎麼更新網頁

網址：https://kang0921.github.io/sophia-kitchen/

## 資料夾裡有什麼

| 位置 | 內容 |
|---|---|
| `index.html` | 整個網頁。菜名、分類、食材、熱量、價格、菜系都寫在這個檔案裡 |
| `img/` `thumb/` `mini/` | 每張照片的大圖、中圖、迷你圖（WebP） |
| `cover/` | 每道菜的正方形封面 |
| `tools/build_images.py` | 把原始照片做成上面那些圖片的程式 |
| `tools/covers.json` | 每個封面用哪張照片、裁哪一塊 |

原始照片（HEIC、zip）放在上一層的「料理照片」資料夾，不會上傳到 GitHub。

## 最簡單的方式：請 Claude 幫忙

在 Claude Code 打開 `sophia-kitchen` 資料夾，直接說要改什麼，例如：

- 「我把新照片放進料理照片資料夾了，幫我加進網頁」
- 「照燒雞腿 2026/01/31 那張往右轉 90 度」
- 「清炒高麗菜的封面裁得不好，重裁」
- 「把某某菜改名成某某」

Claude 讀這份說明就知道要改哪裡、怎麼重做圖片，改好後推上 GitHub，網頁約 1～2 分鐘後更新。

## 自己動手時的步驟

### 新增照片
1. 把照片（HEIC 或 JPG，或 iPhone 匯出的 zip）放進「料理照片」資料夾。
2. 在 `sophia-kitchen` 資料夾執行：`python3 tools/build_images.py 照片編號`
   例如照片叫 `IMG_1234.HEIC`，編號就是 `1234`。
3. 在 `index.html` 的 `DATES` 加上這張照片的拍攝日期，再把編號加到對應料理的 `p:[...]` 裡。
   新的料理要在 `DISHES` 加一行，並在 `KCAL`（熱量）、`COVER`（封面編號）補上資料。
4. 新封面：在 `tools/covers.json` 加一筆 `{"photo": "照片編號", "box": [左, 上, 右, 下]}`，
   box 的單位是照片寬高的十分之一（0～10），然後執行 `python3 tools/build_images.py --covers`。

### 照片轉向
在 `tools/build_images.py` 的 `ROTATE` 加上 `"照片編號": 90`（往右轉 90 度；往左轉填 270，倒過來填 180），
再執行 `python3 tools/build_images.py 照片編號`。用到這張照片的封面也會一起重做。

### 上傳
```
git add -A
git commit -m "說明改了什麼"
git push
```

## 需要的工具
- macOS 內建的 `sips`（讀 HEIC 照片）
- ImageMagick 7（`magick` 指令），用 Homebrew 安裝：`brew install imagemagick`

## 網頁裡的資料存在哪
排好的菜單、改過的價格和熱量，只存在使用者自己的瀏覽器裡。
換手機或清除瀏覽紀錄前，請到「本週菜單 → 備份與還原」下載備份檔。
