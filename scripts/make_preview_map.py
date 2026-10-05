#!/usr/bin/env python3
"""制作大连理工大学凌水校区 Minecraft 世界生成范围预览图
底图: OpenStreetMap 瓦片 | 标注: 校区边界(蓝) + 实际生成范围(红) + 主要地点
"""
import math
import json
import io
import urllib.request

import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-SemiBold.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrow
from PIL import Image

plt.rcParams['font.sans-serif'] = ['Noto Serif SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ---------- 参数 ----------
ZOOM = 16
GEN_BBOX = (38.87318, 121.50831, 38.88981, 121.53206)  # min_lat, min_lon, max_lat, max_lon (实际生成范围)
MARGIN = 0.0016  # 地图显示外扩
UA = {'User-Agent': 'DLUT-MC-WorldGen/1.0 (one-time preview map)'}

def deg2num(lat, lon, z):
    lat_r = math.radians(lat)
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n
    return x, y

def num2deg(x, y, z):
    n = 2.0 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon

# ---------- 1. 下载并拼接OSM瓦片 ----------
min_lat, min_lon, max_lat, max_lon = (
    GEN_BBOX[0] - MARGIN, GEN_BBOX[1] - MARGIN,
    GEN_BBOX[2] + MARGIN, GEN_BBOX[3] + MARGIN,
)
x0, y0 = deg2num(max_lat, min_lon, ZOOM)
x1, y1 = deg2num(min_lat, max_lon, ZOOM)
x0i, y0i = int(x0), int(y0)
x1i, y1i = int(x1), int(y1)

tiles = []
for xi in range(x0i, x1i + 1):
    for yi in range(y0i, y1i + 1):
        url = f"https://tile.openstreetmap.org/{ZOOM}/{xi}/{yi}.png"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as resp:
            tile = Image.open(io.BytesIO(resp.read())).convert("RGB")
        tiles.append((xi, yi, tile))
print(f"downloaded {len(tiles)} tiles")

tw = th = 256
canvas_w = (x1i - x0i + 1) * tw
canvas_h = (y1i - y0i + 1) * th
canvas = Image.new("RGB", (canvas_w, canvas_h))
for xi, yi, tile in tiles:
    canvas.paste(tile, ((xi - x0i) * tw, (yi - y0i) * th))

# ---------- 2. 地理坐标 -> 像素坐标 ----------
def geo2px(lat, lon):
    x, y = deg2num(lat, lon, ZOOM)
    return (x - x0i) * tw, (y - y0i) * th

# 画布四个角的经纬度(用于matplotlib extent)
corner_tl = num2deg(x0i, y0i, ZOOM)
corner_br = num2deg(x1i + 1, y1i + 1, ZOOM)

# ---------- 3. 读取校区多边形 ----------
poly_data = json.load(open('/home/z/my-project/mc-work/campus_polygon.json'))
nodes = {e['id']: (e['lat'], e['lon']) for e in poly_data['elements'] if e['type'] == 'node'}
way = [e for e in poly_data['elements'] if e['type'] == 'way'][0]
campus_lats = [nodes[n][0] for n in way['nodes']]
campus_lons = [nodes[n][1] for n in way['nodes']]

# ---------- 4. 绘图 ----------
fig, ax = plt.subplots(figsize=(11, 10.2), dpi=150, constrained_layout=True)
extent = (corner_tl[1], corner_br[1], corner_br[0], corner_tl[0])  # lon_min, lon_max, lat_min, lat_max
ax.imshow(canvas, extent=extent, interpolation='bilinear')

# 生成范围 (红色虚线框)
glon = [GEN_BBOX[1], GEN_BBOX[3], GEN_BBOX[3], GEN_BBOX[1], GEN_BBOX[1]]
glat = [GEN_BBOX[0], GEN_BBOX[0], GEN_BBOX[2], GEN_BBOX[2], GEN_BBOX[0]]
ax.plot(glon, glat, '-', color='#e41a1c', lw=2.2, ls=(0, (6, 3)),
        label='实际生成范围 bbox', zorder=6)

# 校区多边形 (蓝色)
ax.plot(campus_lons, campus_lats, '-', color='#1f5fbf', lw=2.0,
        label='大工凌水校区边界 (OSM)', zorder=5)
ax.fill(campus_lons, campus_lats, color='#377eb8', alpha=0.12, zorder=2)

# 标注地点
marks = [
    (38.88641, 121.52582, '北门', (8, 12)),
    (38.87402, 121.52680, '南门', (8, -16)),
    (38.87776, 121.52765, '东门', (10, 4)),
    (38.87753, 121.52184, '西门', (-10, -14)),
    (38.87641, 121.52528, '体育场', (12, -6)),
    (38.88150, 121.52019, '中心广场', (-14, 12)),
]
for lat, lon, name, (dx, dy) in marks:
    px, py = geo2px(lat, lon)
    # 转回经纬度用于统一坐标系标注
    x, y = deg2num(lat, lon, ZOOM)
    ax.plot(lon, lat, 'o', ms=5, color='#ff7f00', mec='white', mew=0.8, zorder=7)
    ax.annotate(name, (lon, lat), xytext=(dx, dy), textcoords='offset points',
                fontsize=9.5, color='#111111', zorder=8,
                bbox=dict(boxstyle='round,pad=0.22', fc='white', ec='#999999', alpha=0.85))

# 出生点
ax.plot(121.5260, 38.8795, '*', ms=16, color='#e41a1c', mec='white', mew=0.8,
        label='MC 出生点', zorder=8)

# 指北针
nx, ny = geo2px(min_lat + 0.0002, min_lon + 0.0005)
arrow_ax = ax.transAxes
ax.add_patch(FancyArrow(0.945, 0.955, 0, 0.045, transform=arrow_ax, width=0.012,
                        head_width=0.038, head_length=0.03, color='#222222',
                        length_includes_head=True, zorder=10))
ax.text(0.945, 0.895, 'N', transform=arrow_ax, ha='center', va='top',
        fontsize=13, fontweight='bold', color='#222222', zorder=10)

# 比例尺 (500m)
scale_lat = min_lat + 0.0006
scale_lon0 = min_lon + 0.0008
p0 = geo2px(scale_lat, scale_lon0)
p1 = geo2px(scale_lat, scale_lon0 + 0.005768)  # ~500m经度
seg_lon = [scale_lon0, scale_lon0 + 0.005768]
ax.plot(seg_lon, [scale_lat, scale_lat], '-', color='#222222', lw=3, zorder=10,
        solid_capstyle='butt')
for lo in seg_lon:
    ax.plot([lo, lo], [scale_lat - 0.00012, scale_lat + 0.00012], '-', color='#222222', lw=2, zorder=10)
ax.text(scale_lon0 + 0.005768 / 2, scale_lat + 0.00025, '500 m',
        ha='center', va='bottom', fontsize=9.5, color='#222222', zorder=10)

# 标题与图例
ax.set_title('大连理工大学凌水校区 — Minecraft 世界生成范围\n'
             'Arnis v3.2.0 · geo-terrain 真实地形 · 1:1 比例 · Java 1.21.4',
             fontsize=13.5, fontweight='bold', pad=12)
ax.legend(loc='upper left', fontsize=10, framealpha=0.92,
          bbox_to_anchor=(0.0, 1.0))
ax.set_xlabel('经度 Longitude', fontsize=10)
ax.set_ylabel('纬度 Latitude', fontsize=10)
ax.tick_params(labelsize=8.5)

# 版权署名 (OSM 瓦片使用要求)
ax.text(0.995, 0.005,
        '底图 © OpenStreetMap 贡献者 (ODbL) · 高程: Mapterhorn GLO-30 · 生成于 2026-10-05',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=7.5,
        color='#444444',
        bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#cccccc', alpha=0.85))

ax.set_xlim(extent[0], extent[1])
ax.set_ylim(extent[2], extent[3])

out = '/home/z/my-project/mc-work/范围预览图.png'
fig.savefig(out, dpi=150)
print('saved:', out)
plt.close(fig)
