#!/usr/bin/env python3
"""扫描整个世界: 统计每个Y section有实际内容的区块数, 验证建筑高度分布"""
import struct
import zlib
from pathlib import Path
from collections import Counter

WORLD = Path("/home/z/my-project/mc-work/output/大连理工大学凌水校区/region")

def parse_nbt(data, offset=0):
    tag_type = data[offset]; offset += 1
    if tag_type == 0: return None, offset
    name_len = struct.unpack('>H', data[offset:offset+2])[0]; offset += 2
    name = data[offset:offset+name_len].decode('utf-8'); offset += name_len
    value, offset = read_payload(data, offset, tag_type)
    return (name, value), offset

def read_payload(data, offset, tag_type):
    if tag_type == 1: return struct.unpack('>b', data[offset:offset+1])[0], offset+1
    if tag_type == 2: return struct.unpack('>h', data[offset:offset+2])[0], offset+2
    if tag_type == 3: return struct.unpack('>i', data[offset:offset+4])[0], offset+4
    if tag_type == 4: return struct.unpack('>q', data[offset:offset+8])[0], offset+8
    if tag_type == 5: return struct.unpack('>f', data[offset:offset+4])[0], offset+4
    if tag_type == 6: return struct.unpack('>d', data[offset:offset+8])[0], offset+8
    if tag_type == 7:
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        return data[offset:offset+n], offset+n
    if tag_type == 8:
        n = struct.unpack('>H', data[offset:offset+2])[0]; offset += 2
        return data[offset:offset+n].decode('utf-8', 'replace'), offset+n
    if tag_type == 9:
        it = data[offset]; offset += 1
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        items = []
        for _ in range(n):
            v, offset = read_payload(data, offset, it)
            items.append(v)
        return items, offset
    if tag_type == 10:
        result = {}
        while True:
            tag, offset = parse_nbt(data, offset)
            if tag is None: break
            result[tag[0]] = tag[1]
        return result, offset
    if tag_type == 11:
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        return list(struct.unpack('>' + 'i'*n, data[offset:offset+4*n])), offset+4*n
    if tag_type == 12:
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        return list(struct.unpack('>' + 'q'*n, data[offset:offset+8*n])), offset+8*n
    raise ValueError(tag_type)

section_counter = Counter()
total_blocks_placed = 0

for mca in sorted(WORLD.glob("*.mca")):
    raw = mca.read_bytes()
    for idx in range(1024):
        entry_off = idx * 4
        sector = struct.unpack('>I', b'\x00' + raw[entry_off:entry_off+3])[0]
        count = raw[entry_off+3]
        if count == 0:
            continue
        chunk_data = raw[sector*4096:sector*4096+count*4096]
        length = struct.unpack('>I', chunk_data[0:4])[0]
        comp_type = chunk_data[4]
        if comp_type != 2:
            continue
        dec = zlib.decompress(chunk_data[5:4+length])
        try:
            root, _ = parse_nbt(dec)
            d = root[1]
        except Exception:
            continue
        for s in d.get('sections', []):
            bs = s.get('block_states', {})
            pal = bs.get('palette', [])
            has_data = 'data' in bs
            # 有数据的section 或 调色板非纯air
            non_air = [p for p in pal if p.get('Name') != 'minecraft:air']
            if (has_data and len(pal) > 1) or (len(pal) == 1 and non_air):
                y = s.get('Y')
                section_counter[y] += 1

print("Y分区  ->  含实际内容的区块数")
for y in sorted(section_counter):
    blocks = (y * 16, y * 16 + 15)
    print(f"  Y={y:3d} (方块y {blocks[0]:4d}~{blocks[1]:4d}): {section_counter[y]:6d} 个区块")
non_empty = sum(1 for y in section_counter if y > -5)
print(f"\n总计: {sum(section_counter.values())} 个非空section, "
      f"涉及 {len(section_counter)} 个Y层")
print(f"最高内容层: Y={max(section_counter)} (方块y≈{max(section_counter)*16})")
print(f"最低内容层: Y={min(section_counter)} (方块y≈{min(section_counter)*16})")
