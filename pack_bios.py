import UnityPy, sys, os, zipfile

obb_path = sys.argv[1]
json_txt_file = sys.argv[2]
output_file = sys.argv[3]

TARGET_HASH = "301e2e6076b6de344a21203af8dac419"

with open(json_txt_file, "r", encoding="utf-8") as f:
    new_text = f.read()

# OBB zip se hash container file extract karna
os.makedirs("work", exist_ok=True)
extracted_path = None

with zipfile.ZipFile(obb_path, "r") as z:
    for item in z.infolist():
        if TARGET_HASH in item.filename:
            extracted_path = z.extract(item, "work")
            print(f"Extracted container asset from OBB: {item.filename}")
            break

if not extracted_path:
    sys.exit("Error: Target hash container file not found in OBB!")

env = UnityPy.load(extracted_path)
patched = False

for obj in env.objects:
    if obj.type.name == "TextAsset":
        data = obj.read()
        data.script = new_text
        data.save()
        patched = True
        print(f"Patched TextAsset successfully: {data.m_Name}")

if patched:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "wb") as f:
        f.write(env.file.save())
    print(f"Asset file successfully re-packed to: {output_file}")
else:
    sys.exit("Error: TextAsset not found inside the hash container!")
  
