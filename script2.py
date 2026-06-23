import os
import cv2
import numpy as np
import rasterio

# --- 設定 ---
INPUT_TIFF = "rast_gdpTot_1990_2024_5arcmin.tif"
OUTPUT_PNG = "map2_hidden_7200.png"
TARGET_BAND = None  # Noneで最新年（最終バンド）を使用

print("🔄 GeoTIFFの解析を開始します...")

if not os.path.exists(INPUT_TIFF):
    raise FileNotFoundError(f"エラー: {INPUT_TIFF} が見つかりません。")

with rasterio.open(INPUT_TIFF) as src:
    band_idx = TARGET_BAND if TARGET_BAND is not None else src.count
    print(f"📖 バンド {band_idx} を読み込み中...")
    gdp_raw = src.read(band_idx).astype(np.float32)

    # 欠損値（NoData）やマイナス値の排除
    if src.nodata is not None:
        gdp_raw[gdp_raw == src.nodata] = 0.0
    gdp_raw = np.nan_to_num(gdp_raw, nan=0.0)
    gdp_raw[gdp_raw < 0] = 0.0
    gdp_raw[gdp_raw > 1e13] = 0.0  # 10兆ドル以上のゴミ値を排除

    meta_width = src.width
    meta_height = src.height

# 🌍 データ内の最高値を見つけて UNIT_SCALE を自動逆算
actual_max = np.max(gdp_raw)
print(f"📈 TIFF内の1セルあたりの最大値: {actual_max:,} USD")

# 白潰れ（16777215）を防ぐため、16,000,000 を上限としてフィットさせる
UNIT_SCALE = 160000.0 / actual_max
print(f"🔮 自動計算された最適な精度係数 (UNIT_SCALE): {UNIT_SCALE:.15f}")

# 24bit整数化
int_gdp = np.clip(np.round(gdp_raw * UNIT_SCALE * 100), 0, 16777215).astype(
    np.uint32
)

# BGRに分解（OpenCVはBGR順）
r = (int_gdp >> 16) & 0xFF
g = (int_gdp >> 8) & 0xFF
b = int_gdp & 0xFF

rgb_map = np.zeros((meta_height, meta_width, 3), dtype=np.uint8)
rgb_map[:, :, 0] = b
rgb_map[:, :, 1] = g
rgb_map[:, :, 2] = r

# 保存
cv2.imwrite(OUTPUT_PNG, rgb_map, [cv2.IMWRITE_PNG_COMPRESSION, 9])
print(f"💾 高精度PNGを出力しました: {OUTPUT_PNG}")

# JS用の復元倍率を計算
js_multiplier = 1.0 / (UNIT_SCALE * 100.0 * 1e9)

print("\n" + "=" * 60)
print("📋 JavaScript側 (index.html) に貼り付ける数式")
print("=" * 60)
print(f"// 計算用マルチプライヤー（この値をJS側に書き換えてください）")
print(f"const JS_MULTIPLIER = {js_multiplier:.15f};")
print("=" * 60)