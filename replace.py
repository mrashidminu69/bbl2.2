import UnityPy, os, sys, re, zipfile
from PIL import Image, ImageChops

src_obb, repl_dir = sys.argv[1], sys.argv[2]
work, tmp = "obb_unzipped", "merged_tmp"
os.makedirs("out", exist_ok=True)
os.makedirs(tmp, exist_ok=True)
out_obb = "out/main.13.com.nextwave.bigbash.obb"

repl = {}
for root, _, files in os.walk(repl_dir):
    for f in files:
        if f.lower().endswith(".png"):
            repl[os.path.splitext(f)[0]] = os.path.join(root, f)
ids = {k.rsplit("_", 1)[-1] for k in repl}
print("replacement images:", len(repl))

with zipfile.ZipFile(src_obb) as z:
    order = [i.filename for i in z.infolist() if not i.is_dir()]
    ctype = {i.filename: i.compress_type for i in z.infolist() if not i.is_dir()}
    z.extractall(work)

pat = re.compile(r"^(.*)\.split(\d+)$")
groups, singles = {}, []
for root, _, files in os.walk(work):
    for fn in files:
        p = os.path.join(root, fn)
        m = pat.match(p)
        if m:
            groups.setdefault(m.group(1), []).append((int(m.group(2)), p))
        else:
            singles.append(p)

done = 0
skipped = 0

def process(path):
    global done, skipped
    try:
        env = UnityPy.load(path)
    except Exception:
        return None
    changed = False
    for obj in env.objects:
        if obj.type.name != "Texture2D" or str(obj.path_id) not in ids:
            continue
        try:
            data = obj.read()
            key = f"{data.m_Name}_{obj.path_id}"
            if key in repl:
                img = Image.open(repl[key]).convert("RGBA")
                old = data.image.convert("RGBA")
                if img.size != old.size:
                    print("size mismatch:", key, img.size, old.size)
                    continue
                if ImageChops.difference(img, old).getbbox() is None:
                    continue
                data.image = img
                data.save()
                changed = True
                done += 1
        except Exception:
            skipped += 1
    if not changed:
        return None
    try:
        f = env.file or next(iter(env.files.values()))
        return f.save()
    except Exception as e:
        print("save failed:", path, e)
        return None

for p in singles:
    blob = process(p)
    if blob:
        with open(p, "wb") as f:
            f.write(blob)

for base, parts in groups.items():
    parts.sort()
    chunk = os.path.getsize(parts[0][1])
    merged = os.path.join(tmp, base.replace(os.sep, "_"))
    with open(merged, "wb") as mf:
        for _, pp in parts:
            with open(pp, "rb") as pf:
                mf.write(pf.read())
    blob = process(merged)
    os.remove(merged)
    if blob:
        for _, pp in parts:
            os.remove(pp)
        for i, off in enumerate(range(0, len(blob), chunk)):
            with open(f"{base}.split{i}", "wb") as nf:
                nf.write(blob[off:off + chunk])

print("textures replaced:", done, "| skipped:", skipped)

allp = set()
for root, _, files in os.walk(work):
    for fn in files:
        rel = os.path.relpath(os.path.join(root, fn), work)
        allp.add(rel.replace(os.sep, "/"))

seen = set()
with zipfile.ZipFile(out_obb, "w", zipfile.ZIP_STORED) as zo:
    for n in order + sorted(allp):
        if n in allp and n not in seen:
            seen.add(n)
            zo.write(os.path.join(work, n), n,
                     compress_type=ctype.get(n, zipfile.ZIP_STORED))
print("done")
