import UnityPy, os, sys, re, zipfile, shutil
from PIL import Image

apk, repl_dir = sys.argv[1], sys.argv[2]
TARGET = "sharedassets0.assets"
work = "work"
shutil.rmtree(work, ignore_errors=True)
os.makedirs(work)
os.makedirs("out", exist_ok=True)

repl = {}
for root, _, files in os.walk(repl_dir):
    for f in files:
        if f.lower().endswith(".png"):
            repl[os.path.splitext(f)[0]] = os.path.join(root, f)
ids = {k.rsplit("_", 1)[-1] for k in repl}
print("replacement images:", len(repl))

zin = zipfile.ZipFile(apk)
infos = zin.infolist()

def find(name):
    pat = re.compile(r"(^|/)" + re.escape(name) + r"(\.split(\d+))?$")
    res = []
    for i in infos:
        m = pat.search(i.filename)
        if m:
            res.append((int(m.group(3) or 0), i))
    return [i for _, i in sorted(res, key=lambda x: x[0])]

def load(parts):
    buf = bytearray()
    for i in parts:
        buf += zin.read(i)
    return buf

a_parts = find(TARGET)
r_parts = find(TARGET + ".resS")
print("assets parts:", len(a_parts), "| resS parts:", len(r_parts))
if not a_parts:
    sys.exit("sharedassets0 not found in apk")
A = load(a_parts)
R = load(r_parts) if r_parts else None

open(os.path.join(work, TARGET), "wb").write(A)
if R is not None:
    open(os.path.join(work, TARGET + ".resS"), "wb").write(R)
env = UnityPy.load(work)

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
        sd = getattr(d, "m_StreamData", None)
        streamed = bool(sd and getattr(sd, "size", 0))
        if streamed:
            if R is None:
                print("skip no resS:", key)
                continue
            off, size = sd.offset, sd.size
            old = bytes(R[off:off + size])
            target = R
        else:
            old = bytes(d.image_data)
            off = A.find(old)
            if not old or off < 0 or A.find(old, off + 1) >= 0:
                print("skip cannot locate data:", key)
                continue
            target = A
        try:
            d.set_image(img, mipmap_count=max(1, d.m_MipCount))
        except TypeError:
            d.image = img
        new = bytes(d.image_data)
        if len(new) != len(old):
            print("skip length differs:", key, len(old), len(new))
            continue
        target[off:off + len(old)] = new
        done += 1
        print("patched:", key, "(resS)" if streamed else "")
    except Exception as e:
        print("skip error:", obj.path_id, e)

print("textures patched:", done)
if done == 0:
    sys.exit("nothing patched")

def splitback(parts, buf):
    pos, res = 0, {}
    for i in parts:
        res[i.filename] = bytes(buf[pos:pos + i.file_size])
        pos += i.file_size
    return res

newdata = splitback(a_parts, A)
if R is not None:
    newdata.update(splitback(r_parts, R))

with zipfile.ZipFile("out/unsigned.apk", "w") as zo:
    for i in infos:
        if i.is_dir():
            continue
        up = i.filename.upper()
        if up.startswith("META-INF/") and up.endswith((".SF", ".RSA", ".DSA", ".EC", ".MF")):
            continue
        data = newdata.get(i.filename)
        if data is None:
            data = zin.read(i)
        zi = zipfile.ZipInfo(i.filename, i.date_time)
        zi.compress_type = i.compress_type
        zi.external_attr = i.external_attr
        zo.writestr(zi, data)
print("done")
