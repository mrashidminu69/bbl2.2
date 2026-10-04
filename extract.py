import UnityPy, os, sys, zipfile
from collections import Counter

out = "textures_out"
os.makedirs(out, exist_ok=True)

src = sys.argv[1]
work = "obb_unzipped"

if zipfile.is_zipfile(src):
    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        print("files in obb:", len(names))
        for n in names[:40]:
            print("  ", n)
        z.extractall(work)
    targets = [work]
else:
    print("not a zip, loading directly")
    targets = [src]

types = Counter()
saved = 0
for t in targets:
    env = UnityPy.load(t)
    for obj in env.objects:
        types[obj.type.name] += 1
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                path = os.path.join(out, f"{data.m_Name}_{obj.path_id}.png")
                data.image.save(path)
                saved += 1
            except Exception as e:
                print("skip:", obj.path_id, e)

print("object types:", dict(types.most_common(15)))
print("textures saved:", saved)
