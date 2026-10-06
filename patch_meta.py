import sys, zipfile, struct

src, dst = sys.argv[1], sys.argv[2]

# old abbreviation -> new abbreviation (1 to 3 letters).
# Only these six work: STR HEA HUR REN STA THU
MAP = {
    "HUR": "CL",
}

META = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
NAMES = [b"STR", b"HEA", b"HUR", b"REN", b"STA", b"THU"]

z = zipfile.ZipFile(src)
d = bytearray(z.read(META))
magic, ver = struct.unpack_from("<II", d, 0)
if magic != 0xFAB11BAF:
    sys.exit("not a il2cpp metadata file")
tab_off, tab_size, data_off, data_size = struct.unpack_from("<IIII", d, 8)
n = tab_size // 8
print("metadata version", ver, "| string literals:", n)

def entry(i):
    return struct.unpack_from("<II", d, tab_off + i * 8)

def text(i):
    ln, di = entry(i)
    return bytes(d[data_off + di: data_off + di + ln])

start = None
for i in range(n - len(NAMES)):
    if all(text(i + k) == NAMES[k] for k in range(len(NAMES))):
        start = i
        break
if start is None:
    sys.exit("abbreviation block (STR HEA HUR REN STA THU) not found")
print("abbreviation block at literal index", start)

for k, old in enumerate(NAMES):
    key = old.decode()
    if key not in MAP:
        continue
    new = MAP[key].encode("ascii")
    if not (1 <= len(new) <= 3):
        sys.exit("new abbreviation must be 1 to 3 letters: " + MAP[key])
    ln, di = entry(start + k)
    pos = data_off + di
    d[pos:pos + 3] = new + b"\x00" * (3 - len(new))
    struct.pack_into("<I", d, tab_off + (start + k) * 8, len(new))
    print("patched literal", key, "->", MAP[key])

with zipfile.ZipFile(dst, "w") as zo:
    for i in z.infolist():
        if i.is_dir():
            continue
        data = bytes(d) if i.filename == META else z.read(i)
        zi = zipfile.ZipInfo(i.filename, i.date_time)
        zi.compress_type = i.compress_type
        zi.external_attr = i.external_attr
        zo.writestr(zi, data)
print("done")
