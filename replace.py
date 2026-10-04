import UnityPy, os, sys, zipfile
from PIL import Image

src_obb, repl_dir = sys.argv[1], sys.argv[2]
work = "obb_unzipped"
os.makedirs("out", exist_ok=True)
out_obb = "out/main.13.com.nextwave.bigbash.obb"

repl = {}
for root, _, files in os.walk(repl_dir):
    for f in files:
        if f.lower().endswith(".png"):
            repl[os.path.splitext(f)[0]] = os.path.join(root, f)
print("replacement images:", len(repl))

with zipfile.ZipFile(src_obb) as z:
    infos = z.infolist()
    z.extractall(work)

done = 0
for root, _, files in os.walk(work):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            env = UnityPy.load(p)
        except Exception:
            continue
        changed = False
        for obj in env.objects:
            if obj.type.name != "Texture2D":
                continue
            data = obj.read()
            key = f"{data.m_Name}_{obj.path_id}"
            if key in repl:
                data.image = Image.open(repl[key]).convert("RGBA")
                data.save()
                changed = True
                done += 1
        if changed:
            with open(p, "wb") as f:
                f.write(env.file.save())

print("textures replaced:", done)

with zipfile.ZipFile(out_obb, "w", zipfile.ZIP_STORED) as zo:
    for info in infos:
        if not info.is_dir():
            zo.write(os.path.join(work, info.filename), info.filename)
