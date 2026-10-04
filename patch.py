import UnityPy, os, sys, re, zipfile
from PIL import Image

src, repl_dir = sys.argv[1], sys.argv[2]
tmp = "tmp.bin"
os.makedirs("out", exist_ok=True)

repl = {}
for root, _, files in os.walk(repl_dir):
    for f in files:
        if f.lower().endswith(".png"):
            repl[os.path.splitext(f)[0]] = os.path.join(root, f)
ids = {k.rsplit("_", 1)[-1] for k in repl}
print("replacement images:", len(repl))

is_zip = zipfile.is_zipfile(src)
parts = []
if is_zip:
    with zipfile.ZipFile(src) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        def num(i):
            m = re.search(r"\.split(\d+)$", i.filename)
            return int(m.group(1)) if m else 0
        infos.sort(key=num)
        for i in infos:
            parts.append((i.filename, z.read(i)))
else:
    parts.append(("sharedassets2.assets", open(src, "rb").read()))
print("parts:", len(parts))

buf = bytearray()
for _, d in parts:
    buf += d

with open(tmp, "wb") as f:
    f.write(buf)
env = UnityPy.load(tmp)

done = 0
for obj in env.objects:
    if obj.type.name != "Texture2D" or str(obj.path_id) not in ids:
        continue
    try:
        d = obj.read()
        key = f"{d.m_Name}_{obj.path_id}"
        if key not in repl:
            continue
        img = Image.open(repl[key]).convert("RGBA")
        if img.size != (d.m_Width, d.m_Height):
            print("skip size mismatch:", key, img.size, (d.m_Width, d.m_Height))
            continue
        old = bytes(d.image_data)
        if not old:
            print("skip streamed texture:", key)
            continue
        off = buf.find(old)
        if off < 0 or buf.find(old, off + 1) >= 0:
            print("skip cannot locate data:", key)
            continue
        try:
            d.set_image(img, mipmap_count=max(1, d.m_MipCount))
        except TypeError:
            d.image = img
        new = bytes(d.image_data)
        if len(new) != len(old):
            print("skip length differs:", key, len(old), len(new))
            continue
        buf[off:off + len(old)] = new
        done += 1
        print("patched:", key)
    except Exception as e:
        print("skip error:", obj.path_id, e)

print("textures patched:", done)
if done == 0:
    sys.exit("nothing patched")

if is_zip:
    with zipfile.ZipFile("out/sharedassets2_patched.zip", "w") as zo:
        pos = 0
        for name, d in parts:
            zo.writestr(name, bytes(buf[pos:pos + len(d)]))
            pos += len(d)
else:
    open("out/sharedassets2.assets", "wb").write(buf)
print("done")
