import UnityPy, os, sys, re, zipfile, json

obb, texts_dir = sys.argv[1], sys.argv[2]

TARGETS = [
    ("182e001bae56bcb419267264cf896a7d", "HUR", "HUR_1.txt"),
    ("301e2e6076b6de344a21203af8dac419", "BBL_Bios", "BBL_Bios_1.txt"),
    ("d21c07ca7e62f4e49937026c09a03fc0", "BBLTeam", "BBLTeam_1.txt"),
]

os.makedirs("out", exist_ok=True)
z = zipfile.ZipFile(obb)
infos = [i for i in z.infolist() if not i.is_dir()]

def find(base):
    pat = re.compile(r"(^|/)" + re.escape(base) + r"(\.split(\d+))?$")
    res = []
    for i in infos:
        m = pat.search(i.filename)
        if m:
            res.append((int(m.group(3) or 0), i))
    return [i for _, i in sorted(res, key=lambda x: x[0])]

replaced = {}
failed = False
for base, tname, fname in TARGETS:
    parts = find(base)
    print("==", base, tname, "| entries in obb:", len(parts))
    if not parts:
        print("   NOT FOUND in obb")
        failed = True
        continue
    sizes = [p.file_size for p in parts]
    buf = bytearray()
    for p in parts:
        buf += z.read(p)
    print("   container size:", len(buf), "| starts with:", bytes(buf[:8]))
    tmp = "tmp_" + base
    open(tmp, "wb").write(buf)
    old = None
    try:
        env = UnityPy.load(tmp)
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                d = obj.read()
                if d.m_Name == tname:
                    raw = d.m_Script
                    old = raw.encode("utf-8", "surrogateescape") if isinstance(raw, str) else bytes(raw)
                    break
    except Exception as e:
        print("   UnityPy could not read container:", e)
    if old is None:
        print("   TextAsset not found")
        failed = True
        continue
    new = open(os.path.join(texts_dir, fname), "rb").read()
    if new.startswith(b"\xef\xbb\xbf") and not old.startswith(b"\xef\xbb\xbf"):
        new = new[3:]
    if len(new) > len(old):
        try:
            new = json.dumps(json.loads(new.decode("utf-8")), ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
        except Exception as e:
            print("   bad json:", e)
            failed = True
            continue
    if len(new) > len(old):
        print("   NEW TEXT TOO LONG:", len(new), ">", len(old))
        failed = True
        continue
    used = len(new)
    new = new + b" " * (len(old) - len(new))
    off = buf.find(old)
    if off < 0 or buf.find(old, off + 1) >= 0:
        print("   original text not found as plain bytes in container (compressed?)")
        failed = True
        continue
    buf[off:off + len(old)] = new
    print("   patched: old", len(old), "bytes | new text", used, "bytes + padding")
    pos = 0
    for p, sz in zip(parts, sizes):
        chunk = bytes(buf[pos:pos + sz])
        pos += sz
        replaced[p.filename] = chunk
        open(os.path.join("out", os.path.basename(p.filename)), "wb").write(chunk)
        print("   wrote", os.path.basename(p.filename), "| OBB path:", p.filename)

if failed:
    sys.exit("some files failed, see above")

with zipfile.ZipFile("out/main.13.com.nextwave.bigbash.obb", "w") as zo:
    for i in infos:
        data = replaced.get(i.filename)
        if data is None:
            data = z.read(i)
        zi = zipfile.ZipInfo(i.filename, i.date_time)
        zi.compress_type = i.compress_type
        zo.writestr(zi, data)
print("done: 3 files + full obb written")
