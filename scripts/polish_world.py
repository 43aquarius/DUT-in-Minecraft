#!/usr/bin/env python3
"""整理世界: 重命名为中文名 + 修改LevelName + 自定义图标"""
import nbtlib
import shutil
from pathlib import Path
from PIL import Image

SRC = Path("/home/z/my-project/mc-work/output/Arnis World 1")
DST = Path("/home/z/my-project/mc-work/output/大连理工大学凌水校区")
NEW_NAME = "大连理工大学凌水校区"

# 1) 重命名世界文件夹
if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)

# 2) 修改 level.dat 的 LevelName
level_path = DST / "level.dat"
nbt_file = nbtlib.load(level_path)
nbt_file["Data"]["LevelName"] = nbtlib.String(NEW_NAME)
nbt_file.save(level_path, gzipped=True)

# 校验回读
check = nbtlib.load(level_path)
print("LevelName =", check["Data"]["LevelName"])
print("DataVersion =", check["Data"]["DataVersion"])
print("Spawn =", check["Data"]["SpawnX"], check["Data"]["SpawnY"], check["Data"]["SpawnZ"])

# 3) 生成自定义世界图标: 从地图预览裁剪校园中心区域
preview = Image.open(DST / "arnis_world_map.png").convert("RGB")
# 校区中心在预览图中的位置(基于bbox线性映射)
min_lat, min_lon = 38.87318, 121.50831
max_lat, max_lon = 38.88981, 121.53206
w, h = preview.size
c_lat, c_lon = 38.8810, 121.5245  # 主教学区中心
px = int((c_lon - min_lon) / (max_lon - min_lon) * w)
py = int((max_lat - c_lat) / (max_lat - min_lat) * h)
half = 300
crop = preview.crop((max(0, px - half), max(0, py - half),
                     min(w, px + half), min(h, py + half)))
crop = crop.resize((128, 128), Image.LANCZOS)
crop.save(DST / "icon.png")
print("icon.png updated:", crop.size)

# 4) 删除源Arnis World 1文件夹(已复制到新名字)
shutil.rmtree(SRC)
print("done ->", DST)
