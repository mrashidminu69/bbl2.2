import os, sys, json, struct

src = sys.argv[1]   # global-metadata.dat
out = sys.argv[2]   # output json

with open(src, "rb") as f:
    data = f.read()

print("file size:", len(data))

magic = struct.unpack_from("<I", data, 0)[0]
print("magic: %#x" % magic)
if magic != 0xFAB11BAF:
    sys.exit("magic mismatch — ye global-metadata.dat nahi hai")

version = struct.unpack_from("<i", data, 4)[0]
print("version:", version)

# version 24 ke liye header offsets
# 0x08 = stringLiteralOffset (index table)
# 0x0C = stringLiteralCount (kitne string literals)
# 0x10 = stringLiteralDataOffset (asal text)
# 0x14 = stringLiteralDataCount (kitne bytes)
# 0x18 = stringOffset
# 0x1C = stringCount

lit_off = struct.unpack_from("<I", data, 0x08)[0]
lit_count = struct.unpack_from("<i", data, 0x0C)[0]
data_off = struct.unpack_from("<I", data, 0x10)[0]
data_size = struct.unpack_from("<i", data, 0x14)[0]
str_off = struct.unpack_from("<I", data, 0x18)[0]
str_count = struct.unpack_from("<i", data, 0x1C)[0]

print("stringLiteralOffset: %#x" % lit_off)
print("stringLiteralCount:", lit_count)
print("stringLiteralDataOffset: %#x" % data_off)
print("stringLiteralDataCount:", data_size)
print("stringOffset: %#x" % str_off)
print("stringCount:", str_count)

strings = []

# --- 1) String literals: index table + data ---
# index table: har entry 8 bytes (length + data offset)
# data: asal UTF-8 text
if lit_count > 0 and data_size > 0:
    print("\n--- reading string literals ---")
    for i in range(lit_count):
        entry_off = lit_off + i * 8
        if entry_off + 8 > len(data):
            break
        slen = struct.unpack_from("<i", data, entry_off)[0]
        soff = struct.unpack_from("<I", data, entry_off + 4)[0]
        abs_off = data_off + soff
        if slen < 0 or slen > 100000 or abs_off + slen > len(data):
            continue
        s = data[abs_off:abs_off+slen].decode("utf-8", errors="replace")
        strings.append({"kind": "literal", "index": i, "offset": abs_off, "length": slen, "value": s})

# --- 2) Metadata strings: har entry 4 bytes (length) + text ---
if str_count > 0:
    print("\n--- reading metadata strings ---")
    pos = str_off
    for i in range(str_count):
        if pos + 4 > len(data):
            break
        slen = struct.unpack_from("<i", data, pos)[0]
        pos += 4
        if slen < 0 or slen > 100000 or pos + slen > len(data):
            break
        s = data[pos:pos+slen].decode("utf-8", errors="replace")
        strings.append({"kind": "meta", "index": i, "offset": pos, "length": slen, "value": s})
        pos += slen

print("\ntotal strings:", len(strings))

# --- 3) Team abbr check ---
targets = ["HUR", "STR", "HEA", "REN", "STA", "SCO", "SIX", "THU"]
print("\n--- team abbr check ---")
for t in targets:
    exact = [s for s in strings if s["value"] == t]
    part = [s for s in strings if t in s["value"]]
    print(f"{t}: exact={len(exact)} partial={len(part)}")

# --- 4) JSON likho ---
with open(out, "w", encoding="utf-8") as f:
    json.dump({"version": version, "count": len(strings), "strings": strings}, f, ensure_ascii=False, indent=1)

print("\ndone:", out)
