#!/usr/bin/env python3
"""校验世界region文件完整性并打包最终交付物"""
import struct
import os
import zipfile
import shutil
from pathlib import Path

WORLD = Path("/home/z/my-project/mc-work/output/大连理工大学凌水校区")
DL = Path("/home/z/my-project/download")

# ---------- 1. 校验 region 文件 ----------
total_chunks = 0
empty_chunks = 0
total_sectors = 0
print("=== Region 文件校验 ===")
for mca in sorted((WORLD / "region").glob("*.mca")):
    data = mca.read_bytes()
    assert len(data) >= 8192, f"{mca.name} too small"
    if len(data) % 4096 != 0:
        print(f"  [WARN] {mca.name}: 大小未按4096对齐 ({len(data)})")
    occupied = 0
    for i in range(1024):
        off = struct.unpack(">I", b"\x00" + data[i*4:i*4+3])[0]
        cnt = data[i*4+3]
        if cnt > 0:
            total_chunks += 1
            occupied += cnt
            if cnt == 1:
                # 只有1个扇区的块可能是空块(全air)
                empty_chunks += 1
    total_sectors += occupied
    print(f"  {mca.name}: {len(data)//4096} 扇区, 占用 {occupied} 扇区")

print(f"合计: {total_chunks} 个区块指针, 空块(1扇区) {empty_chunks}")
print(f"世界文件夹大小: {sum(f.stat().st_size for f in WORLD.rglob('*') if f.is_file())/1e6:.1f} MB")

# ---------- 2. 组装交付目录 ----------
PKG_NAME = "大连理工大学凌水校区-Minecraft世界"
PKG = DL / PKG_NAME
if PKG.exists():
    shutil.rmtree(PKG)
PKG.mkdir(parents=True)
DL.mkdir(parents=True, exist_ok=True)

# 世界文件夹
shutil.copytree(WORLD, PKG / "大连理工大学凌水校区")

# 文档与图片
shutil.copy("/home/z/my-project/mc-work/使用说明.txt", PKG / "使用说明.txt")
shutil.copy("/home/z/my-project/mc-work/Arnis命令参数.txt", PKG / "Arnis命令参数.txt")
shutil.copy("/home/z/my-project/mc-work/范围预览图.png", PKG / "范围预览图.png")
shutil.copy(WORLD / "arnis_world_map.png", PKG / "世界俯视预览图.png")

print("\n=== 交付目录 ===")
for p in sorted(PKG.rglob("*")):
    depth = len(p.relative_to(PKG).parts)
    print("  " * depth + p.name + ("/" if p.is_dir() else f"  ({p.stat().st_size/1e6:.1f} MB)"))

# ---------- 3. 打 zip ----------
zip_path = DL / f"{PKG_NAME}.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as zf:
    for p in sorted(PKG.rglob("*")):
        if p.is_file():
            zf.write(p, p.relative_to(PKG.parent))
print(f"\nzip: {zip_path}  ({zip_path.stat().st_size/1e6:.1f} MB)")

# 单独放一份范围预览图便于快速查看
shutil.copy("/home/z/my-project/mc-work/范围预览图.png", DL / "范围预览图.png")
print("done")
