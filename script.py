import rasterio
import numpy as np
from PIL import Image
import geopandas as gpd
import geodatasets # ← 新しく追加
from rasterio import features

INPUT_TIFF = 'rast_gdpTot_1990_2024_5arcmin.tif' 
OUTPUT_MAP1_DISPLAY = 'map1_display_7200.png'
OUTPUT_MAP2_HIDDEN  = 'map2_hidden_7200.png'

# --- 配色の設定 ---
COLOR_OCEAN = [65, 140, 240] # 明るく見やすい青（海）
COLOR_LAND  = [0, 120, 20]   # コントラストの効いた深い緑（陸）

print("1. GDPデータを読み込んでいます...")
with rasterio.open(INPUT_TIFF) as src:
    raw_data = src.read(1)
    nodata = src.nodata
    transform = src.transform # 座標変換データ（これが超重要）
    height, width = raw_data.shape

print("2. 完璧な海岸線を持つ「本物の世界地図」を取得しています...")
# 最新のgeodatasetsライブラリを使って世界地図（陸地）データを取得
world_map = gpd.read_file(geodatasets.get_path('naturalearth.land'))

print("3. 地図の穴を塞ぐためのマスクを作成中...")
# 本物の世界地図を、GDPデータと全く同じサイズの画像に変換（ラスタライズ）する
geom = [(shape, 1) for shape in world_map.geometry]
true_land_mask = features.rasterize(
    geom,
    out_shape=(height, width),
    transform=transform,
    fill=0,
    all_touched=True,
    dtype=np.uint8
)
# true_land_mask は「陸地が1」「海が0」の完璧な配列になる
is_land = (true_land_mask == 1)

print("4. マップ①（表示用）を作成中...")
display_arr = np.zeros((height, width, 3), dtype=np.uint8)

# 全体を海の色で塗り、本物の陸地データを使って陸の色を塗る（これで穴が完全に塞がる！）
display_arr[:] = COLOR_OCEAN
display_arr[is_land] = COLOR_LAND

img_display = Image.fromarray(display_arr, mode='RGB')
img_display_7200 = img_display.resize((7200, 3600), Image.Resampling.NEAREST)
img_display_7200.save(OUTPUT_MAP1_DISPLAY)

print("5. マップ②（白黒GDPデータ）を作成中...")
gdp_data = np.nan_to_num(raw_data, nan=0.0)
if nodata is not None:
    gdp_data[gdp_data == nodata] = 0.0

gdp_log = np.log1p(gdp_data)
max_log = np.max(gdp_log) if np.max(gdp_log) > 0 else 1
gdp_normalized = (gdp_log / max_log * 255).astype(np.uint8)

img_hidden = Image.fromarray(gdp_normalized, mode='L')
img_hidden_7200 = img_hidden.resize((7200, 3600), Image.Resampling.NEAREST)
img_hidden_7200.save(OUTPUT_MAP2_HIDDEN)

print("🎉 完了しました！穴のない美しい世界地図が生成されました。")