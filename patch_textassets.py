import os
import sys
import json
import shutil
import zipfile
import UnityPy


# ============================================================
# TARGET FILES
# ============================================================

TARGETS = {
    "STA_1.txt": "5c887408a240d4a4d8e082224069f7be",
    "SIX_1.txt": "2b644b239c6b4664a901147443afeab1",
    "SCO_1.txt": "44f1cd3b5ddb7ea4b91222fc5dfa1f50",
    "THU_1.txt": "80f3f9fb8e627ad4ea01753dc148d016",
    "HUR_1.txt": "182e001bae56bcb419267264cf896a7d",
    "BBL_Bios_1.txt": "301e2e6076b6de344a21203af8dac419",
    "STR_1.txt": "4221df6f0f151fd4da6bd0ee35123a9b",
    "HEA_1.txt": "a1d3846bf78a02641ba348f297151d28",
    "BBLTeam_1.txt": "d21c07ca7e62f4e49937026c09a03fc0",
    "REN_1.txt": "e55a407938058bf4d857737a7afc799e",
}


# ============================================================
# ARGUMENTS
# ============================================================

if len(sys.argv) != 3:
    print("Usage:")
    print("python patch_textassets.py <obb> <updated_text_zip>")
    sys.exit(1)


obb_path = sys.argv[1]
updated_zip = sys.argv[2]


# ============================================================
# DIRECTORIES
# ============================================================

WORK = "textasset_work"
OBB_DIR = os.path.join(WORK, "obb")
UPDATED_DIR = os.path.join(WORK, "updated")
OUTPUT_DIR = "updated_10_files"

shutil.rmtree(WORK, ignore_errors=True)
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

os.makedirs(OBB_DIR, exist_ok=True)
os.makedirs(UPDATED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# EXTRACT ORIGINAL OBB
# ============================================================

print("==========================================")
print("EXTRACTING ORIGINAL OBB")
print("==========================================")

with zipfile.ZipFile(obb_path, "r") as z:
    z.extractall(OBB_DIR)

print("OBB extracted.")


# ============================================================
# EXTRACT UPDATED TEXT FILES
# ============================================================

print("")
print("==========================================")
print("EXTRACTING UPDATED TEXT ZIP")
print("==========================================")

with zipfile.ZipFile(updated_zip, "r") as z:
    z.extractall(UPDATED_DIR)

print("Updated text files extracted.")


# ============================================================
# FIND HASH FILE
# ============================================================

def find_hash_file(root, hash_name):

    found = []

    for current_root, dirs, files in os.walk(root):

        for filename in files:

            if filename == hash_name:

                found.append(
                    os.path.join(current_root, filename)
                )

    if len(found) == 0:
        raise RuntimeError(
            f"Target hash file not found: {hash_name}"
        )

    if len(found) > 1:
        raise RuntimeError(
            f"Target hash file found more than once: {hash_name}\n"
            + "\n".join(found)
        )

    return found[0]


# ============================================================
# FIND UPDATED TEXT
# ============================================================

def find_updated_file(filename):

    direct = os.path.join(UPDATED_DIR, filename)

    if os.path.isfile(direct):
        return direct

    for root, dirs, files in os.walk(UPDATED_DIR):

        if filename in files:
            return os.path.join(root, filename)

    raise RuntimeError(
        f"Updated file not found inside ZIP: {filename}"
    )


# ============================================================
# PATCH ONE UNITY TEXTASSET
# ============================================================

def patch_one(filename, hash_name):

    print("")
    print("------------------------------------------")
    print("FILE:", filename)
    print("HASH:", hash_name)
    print("------------------------------------------")

    target_path = find_hash_file(
        OBB_DIR,
        hash_name
    )

    replacement_path = find_updated_file(
        filename
    )

    print("Target:")
    print(target_path)

    print("Replacement:")
    print(replacement_path)

    # --------------------------------------------------------
    # Read replacement text
    # --------------------------------------------------------

    with open(
        replacement_path,
        "rb"
    ) as f:

        replacement_bytes = f.read()

    if not replacement_bytes:
        raise RuntimeError(
            f"Replacement file is empty: {filename}"
        )

    # --------------------------------------------------------
    # Load Unity asset
    # --------------------------------------------------------

    print("Loading Unity asset...")

    env = UnityPy.load(target_path)

    textassets = []

    for obj in env.objects:

        if obj.type.name == "TextAsset":

            textassets.append(obj)

    print(
        "TextAssets found:",
        len(textassets)
    )

    if len(textassets) == 0:

        raise RuntimeError(
            f"No TextAsset found inside {hash_name}"
        )

    if len(textassets) > 1:

        print(
            "WARNING: more than one TextAsset found."
        )

    # --------------------------------------------------------
    # Replace TextAsset payload
    # --------------------------------------------------------

    changed = 0

    for obj in textassets:

        data = obj.read()

        old_script = getattr(
            data,
            "m_Script",
            None
        )

        if old_script is None:

            print(
                "WARNING: TextAsset has no m_Script field."
            )

            continue

        print(
            "Old TextAsset size:",
            len(old_script)
            if hasattr(old_script, "__len__")
            else "unknown"
        )

        # ----------------------------------------------------
        # FIX: Force the payload to be raw bytes.
        # UnityPy expects m_Script to be bytes, not str.
        # ----------------------------------------------------

        if isinstance(replacement_bytes, str):
            data.m_Script = replacement_bytes.encode("utf-8")
        else:
            data.m_Script = replacement_bytes

        # Save the modified TextAsset
        obj.save_typetree(data)

        changed += 1

    if changed == 0:

        raise RuntimeError(
            f"Could not modify TextAsset in {hash_name}"
        )

    # --------------------------------------------------------
    # Save ONLY this Unity hash file
    # --------------------------------------------------------

    temp_dir = os.path.join(
        WORK,
        "save",
        hash_name
    )

    shutil.rmtree(
        temp_dir,
        ignore_errors=True
    )

    os.makedirs(
        temp_dir,
        exist_ok=True
    )

    # UnityPy saves the modified environment.
    env.save(
        pack=True,
        out_path=temp_dir
    )

    # Find generated file.
    generated = []

    for root, dirs, files in os.walk(temp_dir):

        for f in files:

            generated.append(
                os.path.join(root, f)
            )

    if not generated:

        raise RuntimeError(
            f"UnityPy did not produce output for {hash_name}"
        )

    # Prefer file with same hash name.
    output_source = None

    for f in generated:

        if os.path.basename(f) == hash_name:

            output_source = f
            break

    if output_source is None:

        if len(generated) == 1:

            output_source = generated[0]

        else:

            raise RuntimeError(
                "Could not identify saved Unity asset for "
                + hash_name
            )

    # --------------------------------------------------------
    # Put ONLY modified hash file into final output
    # --------------------------------------------------------

    final_path = os.path.join(
        OUTPUT_DIR,
        hash_name
    )

    shutil.copy2(
        output_source,
        final_path
    )

    print("")
    print("SUCCESS")
    print("Output:")
    print(final_path)

    print(
        "Original size:",
        os.path.getsize(target_path)
    )

    print(
        "New size:",
        os.path.getsize(final_path)
    )


# ============================================================
# PATCH ALL 10
# ============================================================

for filename, hash_name in TARGETS.items():

    patch_one(
        filename,
        hash_name
    )


# ============================================================
# CREATE FINAL ZIP
# ============================================================

final_zip = "updated_10_textassets.zip"

if os.path.exists(final_zip):
    os.remove(final_zip)


print("")
print("==========================================")
print("CREATING FINAL ZIP")
print("==========================================")


with zipfile.ZipFile(
    final_zip,
    "w",
    compression=zipfile.ZIP_DEFLATED
) as z:

    for filename, hash_name in TARGETS.items():

        path = os.path.join(
            OUTPUT_DIR,
            hash_name
        )

        if not os.path.isfile(path):

            raise RuntimeError(
                f"Missing final file: {hash_name}"
            )

        z.write(
            path,
            arcname=hash_name
        )


# ============================================================
# VALIDATION
# ============================================================

print("")
print("==========================================")
print("FINAL VALIDATION")
print("==========================================")

with zipfile.ZipFile(
    final_zip,
    "r"
) as z:

    names = z.namelist()

    print(
        "Files in final ZIP:",
        len(names)
    )

    if len(names) != 10:

        raise RuntimeError(
            "FINAL ZIP DOES NOT CONTAIN EXACTLY 10 FILES"
        )

    for filename, hash_name in TARGETS.items():

        if hash_name not in names:

            raise RuntimeError(
                f"Missing: {hash_name}"
            )

        print(
            "OK:",
            filename,
            "->",
            hash_name
        )


print("")
print("==========================================")
print("DONE")
print("==========================================")

print(
    "Final ZIP:",
    final_zip
)

print(
    "Size:",
    os.path.getsize(final_zip)
)
