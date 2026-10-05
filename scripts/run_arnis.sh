#!/bin/bash
# Arnis 生成大连理工大学凌水校区 Minecraft 世界
# bbox = 校区多边形外扩约50米: lat 38.8736~38.8894, lon 121.5089~121.5315
# 模式: geo-terrain (真实OSM数据+真实高程地形), 比例 1:1, Java 1.21.1
set -u

SQFS=/home/z/my-project/mc-work/appimage/squashfs-root
HOSTLIBS=/home/z/my-project/mc-work/host-libs/extracted/usr/lib/x86_64-linux-gnu
OUTDIR=/home/z/my-project/mc-work/output
LOG=/home/z/my-project/mc-work/arnis-run.log

export LD_LIBRARY_PATH="$HOSTLIBS:$SQFS/usr/lib/x86_64-linux-gnu:$SQFS/usr/lib"

mkdir -p "$OUTDIR"

cd "$SQFS" || exit 1

./usr/bin/arnis \
  --bbox "38.87318,121.50831,38.88981,121.53206" \
  --output-dir "$OUTDIR" \
  --mode geo-terrain \
  --scale 1 \
  --spawn-lat 38.8795 \
  --spawn-lng 121.5260 \
  --map-preview \
  --gamemode creative \
  --world-time 6000 \
  >> "$LOG" 2>&1

echo "EXIT_CODE=$?" >> "$LOG"
