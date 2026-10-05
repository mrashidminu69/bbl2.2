import UnityPy, os, sys, zipfile, csv, re

out = "text_out"
os.makedirs(out, exist_ok=True)
rows = []

for src in sys.argv[1:]:
    tag = os.path.splitext(os.path.basename(src))[0]
    work = "unz_" + tag
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    env = UnityPy.load(work)
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        fname = re.sub(r"\.split\d+$", "", str(getattr(obj.assets_file, "name", "unknown")))
        try:
            d = obj.read()
            raw = d.m_Script
            if isinstance(raw, str):
                raw = raw.encode("utf-8", "surrogateescape")
            name = re.sub(r"[^\w.\-]", "_", d.m_Name or "noname")
            try:
                txt = raw.decode("utf-8")
                ext = ".txt"
                prev = txt[:60].replace("\n", " ").replace("\r", " ")
            except UnicodeDecodeError:
                ext = ".bin"
                prev = "(binary)"
            folder = os.path.join(out, tag, fname)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, f"{name}_{obj.path_id}{ext}"), "wb") as f:
                f.write(raw)
            rows.append([tag, fname, obj.path_id, d.m_Name, len(raw), prev])
        except Exception as e:
            print("skip:", tag, fname, obj.path_id, e)

with open(os.path.join(out, "index_text.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["source", "file", "path_id", "name", "bytes", "preview"])
    w.writerows(rows)
print("text assets saved:", len(rows))
