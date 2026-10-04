import UnityPy, os, sys, zipfile, csv, re

out = "textures_out"
os.makedirs(out, exist_ok=True)
src = sys.argv[1]
work = "obb_unzipped"

with zipfile.ZipFile(src) as z:
    z.extractall(work)

env = UnityPy.load(work)
rows = []
saved = 0
for obj in env.objects:
    if obj.type.name != "Texture2D":
        continue
    fname = getattr(obj.assets_file, "name", "unknown")
    fname = re.sub(r"\.split\d+$", "", str(fname))
    try:
        d = obj.read()
        folder = os.path.join(out, fname)
        os.makedirs(folder, exist_ok=True)
        d.image.save(os.path.join(folder, f"{d.m_Name}_{obj.path_id}.png"))
        rows.append([fname, obj.path_id, d.m_Name, d.m_Width, d.m_Height])
        saved += 1
    except Exception as e:
        print("skip:", fname, obj.path_id, e)

with open(os.path.join(out, "index.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["source_file", "path_id", "name", "width", "height"])
    w.writerows(rows)

print("textures saved:", saved)
