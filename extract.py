import UnityPy, os, sys

out = "textures_out"
os.makedirs(out, exist_ok=True)

for src in sys.argv[1:]:
    print("loading", src)
    env = UnityPy.load(src)
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            data = obj.read()
            path = os.path.join(out, f"{data.m_Name}_{obj.path_id}.png")
            try:
                data.image.save(path)
            except Exception as e:
                print("skip:", data.m_Name, e)
