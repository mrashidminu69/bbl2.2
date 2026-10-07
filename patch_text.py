import UnityPy, os, sys, re, zipfile, json

obb, texts_dir = sys.argv[1], sys.argv[2]

TARGETS = [
    ("4221df6f0f151fd4da6bd0ee35123a9b", "STR", "STR_1.txt"),
    ("a1d3846bf78a02641ba348f297151d28", "HEA", "HEA_1.txt"),
    ("182e001bae56bcb419267264cf896a7d", "HUR", "HUR_1.txt"),
    ("e55a407938058bf4d857737a7afc799e", "REN", "REN_1.txt"),
    ("5c887408a240d4a4d8e082224069f7be", "STA", "STA_1.txt"),
    ("44f1cd3b5ddb7ea4b91222fc5dfa1f50", "SCO", "SCO_1.txt"),
    ("2b644b239c6b4664a901147443afeab1", "SIX", "SIX_1.txt"),
    ("80f3f9fb8e627ad4ea01753dc148d016", "THU", "THU_1.txt"),
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

    env, ta, old = None, None, None
    try:
        env = UnityPy.load(tmp)
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                d = obj.read()
                if d.m_Name == tname:
                    raw = d.m_Script
                    old = raw.encode("utf-8", "surrogateescape") if isinstance(raw, str) else bytes(raw)
                    ta = obj
                    break
    except Exception as e:
        print("   UnityPy could not read container:", e)
    if old is None:
        print("   TextAsset not found")
        failed = True
        continue

    newp = os.path.join(texts_dir, fname)
    if not os.path.exists(newp):
        print("   MISSING new file in zip:", fname)
        failed = True
        continue
    new = open(newp, "rb").read()
    if new.startswith(b"\xef\xbb\xbf") and not old.startswith(b"\xef\xbb\xbf"):
        new = new[3:]
    try:
        json.loads(new.decode("utf-8"))
    except Exception as e:
        print("   new file is not valid json:", e)
        failed = True
        continue

    chunks = None
    off = buf.find(old)
    if off >= 0 and buf.find(old, off + 1) < 0:
        if len(new) > len(old):
            new = json.dumps(json.loads(new.decode("utf-8")), ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
        if len(new) > len(old):
            print("   NEW TEXT TOO LONG:", len(new), ">", len(old))
            failed = True
            continue
        used = len(new)
        new = new + b" " * (len(old) - len(new))
        buf[off:off + len(old)] = new
        pos, chunks = 0, {}
        for p, sz in zip(parts, sizes):
            chunks[p.filename] = bytes(buf[pos:pos + sz])
            pos += sz
        print("   patched in place: old", len(old), "| new", used, "+ padding")
    elif len(parts) == 1:
        try:
            tree = ta.read_typetree()
            tree["m_Script"] = new.decode("utf-8")
            ta.save_typetree(tree)
            chunks = {parts[0].filename: env.file.save()}
            print("   text was not plain bytes, container re-saved with UnityPy")
        except Exception as e:
            print("   re-save failed:", e)
            failed = True
            continue
    else:
        print("   cannot patch: text not found as plain bytes in split container")
        failed = True
        continue

    for name, data in chunks.items():
        open(os.path.join("out", os.path.basename(name)), "wb").write(data)
        print("   wrote", os.path.basename(name), "| OBB path:", name)

if failed:
    sys.exit("some files failed, see above")
print("done: 10 files written")
