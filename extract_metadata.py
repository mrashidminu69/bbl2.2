import os, sys, json, struct

# global-metadata.dat ka format (Unity IL2CPP)
# Header: 0x00 - magic (0xFAB11BAF)
# 0x08 - version
# 0x10 - stringLiteralOffset
# 0x14 - stringLiteralCount
# ...

src = sys.argv[1]   # global-metadata.dat
out = sys.argv[2]   # output json

with open(src, "rb") as f:
    data = f.read()

print("file size:", len(data))

# magic check
magic = struct.unpack_from("<I", data, 0)[0]
print("magic: %#x" % magic)
if magic != 0xFAB11BAF:
    print("WARNING: magic mismatch — shayad ye global-metadata.dat nahi hai")

# version
version = struct.unpack_from("<i", data, 4)[0]
print("version:", version)

# string literal table ka offset aur size
# IL2CPP metadata mein string literal table 0x10 par hoti hai (version ke hisaab se alag)
# Aksar: 0x10 = stringLiteralOffset, 0x14 = stringLiteralCount (bytes)
str_off = struct.unpack_from("<I", data, 0x10)[0]
str_size = struct.unpack_from("<I", data, 0x14)[0]

print("string literal offset:", hex(str_off))
print("string literal size:", str_size)

# strings ko nikaalo
# Har string: length (4 bytes) + UTF-8 bytes
strings = []
pos = str_off
end = str_off + str_size
idx = 0
while pos < end and pos + 4 <= len(data):
    try:
        slen = struct.unpack_from("<i", data, pos)[0]
        pos += 4
        if slen < 0 or slen > 100000:
            break
        s = data[pos:pos+slen].decode("utf-8", errors="replace")
        strings.append({"index": idx, "offset": pos, "length": slen, "value": s})
        pos += slen
        idx += 1
    except Exception as e:
        print("stop at", pos, e)
        break

print("total strings:", len(strings))

# JSON likho
with open(out, "w", encoding="utf-8") as f:
    json.dump({"version": version, "count": len(strings), "strings": strings}, f, ensure_ascii=False, indent=1)

print("done:", out)

# "HUR", "STR", "HEA" waghera dhoondo
targets = ["HUR", "STR", "HEA", "REN", "STA", "SCO", "SIX", "THU"]
print("\n--- team abbr check ---")
for t in targets:
    hits = [s for s in strings if s["value"] == t]
    print(f"{t}: {len(hits)} exact match")
    # partial bhi
    part = [s for s in strings if t in s["value"]]
    print(f"   partial: {len(part)}")
