#!/usr/bin/env python3
"""解剖Anvil区块: 解压并解析NBT验证方块数据真实性"""
import struct
import zlib
import gzip
import sys

MCA = "/home/z/my-project/mc-work/output/大连理工大学凌水校区/region/r.2.1.mca"

def parse_nbt(data, offset=0):
    tag_type = data[offset]; offset += 1
    if tag_type == 0: return None, offset
    name_len = struct.unpack('>H', data[offset:offset+2])[0]; offset += 2
    name = data[offset:offset+name_len].decode('utf-8'); offset += name_len
    value, offset = read_payload(data, offset, tag_type)
    return (name, value), offset

def read_payload(data, offset, tag_type):
    if tag_type == 1: return struct.unpack('>b', data[offset:offset+1])[0], offset+1
    elif tag_type == 2: return struct.unpack('>h', data[offset:offset+2])[0], offset+2
    elif tag_type == 3: return struct.unpack('>i', data[offset:offset+4])[0], offset+4
    elif tag_type == 4: return struct.unpack('>q', data[offset:offset+8])[0], offset+8
    elif tag_type == 5: return struct.unpack('>f', data[offset:offset+4])[0], offset+4
    elif tag_type == 6: return struct.unpack('>d', data[offset:offset+8])[0], offset+8
    elif tag_type == 7:
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        return data[offset:offset+n], offset+n
    elif tag_type == 8:
        n = struct.unpack('>H', data[offset:offset+2])[0]; offset += 2
        return data[offset:offset+n].decode('utf-8', 'replace'), offset+n
    elif tag_type == 9:
        it = data[offset]; offset += 1
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        items = []
        for _ in range(n):
            v, offset = read_payload(data, offset, it)
            items.append(v)
        return items, offset
    elif tag_type == 10:
        result = {}
        while True:
            tag, offset = parse_nbt(data, offset)
            if tag is None: break
            result[tag[0]] = tag[1]
        return result, offset
    elif tag_type == 11:
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        return list(struct.unpack('>' + 'i'*n, data[offset:offset+4*n])), offset+4*n
    elif tag_type == 12:
        n = struct.unpack('>i', data[offset:offset+4])[0]; offset += 4
        return list(struct.unpack('>' + 'q'*n, data[offset:offset+8*n])), offset+8*n
    raise ValueError(f'unknown tag {tag_type}')

with open(MCA, 'rb') as f:
    raw = f.read()

# 读第(16,16)区块 (校园中心附近)
for idx in [16*32+16, 0, 500, 700]:
    entry_off = idx * 4
    sector = struct.unpack('>I', b'\x00' + raw[entry_off:entry_off+3])[0]
    count = raw[entry_off+3]
    if count == 0:
        print(f'chunk {idx}: EMPTY')
        continue
    chunk_data = raw[sector*4096:sector*4096+count*4096]
    length = struct.unpack('>I', chunk_data[0:4])[0]
    comp_type = chunk_data[4]
    payload = chunk_data[5:4+length]
    if comp_type == 2:
        dec = zlib.decompress(payload)
    elif comp_type == 1:
        dec = gzip.decompress(payload)
    elif comp_type == 3:
        dec = payload
    else:
        print(f'chunk {idx}: unknown compression {comp_type}')
        continue
    root, _ = parse_nbt(dec)
    d = root[1]
    sections = d.get('sections', [])
    print(f'=== chunk idx={idx} status={d.get("status","?")[:30]} ===')
    print(f'  xPos={d.get("xPos")} zPos={d.get("zPos")} sections={len(sections)}')
    total_palette = set()
    for s in sections:
        bs = s.get('block_states', {})
        pal = [p.get('Name', '?') for p in bs.get('palette', [])]
        data = bs.get('data', None)
        total_palette.update(pal)
        print(f'  Y={s.get("Y")}: palette={len(pal)} data={"yes" if data else "no(shared/single)"} '
              f'blocks={pal[:4]}{"..." if len(pal) > 4 else ""}')
    print(f'  合计不同方块类型: {len(total_palette)}')
    hm = d.get('heightmaps', {})
    print(f'  heightmaps: {list(hm.keys())}')
    print()
