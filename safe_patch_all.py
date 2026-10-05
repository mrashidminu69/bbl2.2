import zipfile, sys, os

obb_path = sys.argv[1]         # Downloaded Original OBB
hur_json_path = sys.argv[2]    # Drive se HUR_1.txt
bios_json_path = sys.argv[3]   # Drive se BBL_Bios_1.txt
output_obb = sys.argv[4]       # Output Patched OBB

HUR_HASH = "182e001bae56bcb419267264cf896a7d"
BIOS_HASH = "301e2e6076b6de344a21203af8dac419"

with open(hur_json_path, "rb") as f:
    new_hur_bytes = f.read().strip()

with open(bios_json_path, "rb") as f:
    new_bios_bytes = f.read().strip()

def patch_raw_container(orig_bytes, new_payload_bytes):
    # JSON start locate karna
    start_idx = orig_bytes.find(b'{"')
    if start_idx == -1:
        start_idx = orig_bytes.find(b'{')
    
    if start_idx == -1:
        print("Warning: JSON payload marker not found, skipping container!")
        return orig_bytes

    # Original header structure preserve karke exact length match karwana
    header = orig_bytes[:start_idx]
    orig_length = len(orig_bytes) - start_idx

    if len(new_payload_bytes) > orig_length:
        print(f"Error: New data size ({len(new_payload_bytes)}) is larger than allocated ({orig_length})!")
        return orig_bytes

    # Invisible spaces se exact byte-level balance
    padded_payload = new_payload_bytes + (b' ' * (orig_length - len(new_payload_bytes)))
    return header + padded_payload

os.makedirs(os.path.dirname(output_obb), exist_ok=True)

with zipfile.ZipFile(obb_path, "r") as zin:
    with zipfile.ZipFile(output_obb, "w", zipfile.ZIP_STORED) as zout:  # ZIP_STORED retains original container alignment
        for item in zin.infolist():
            data = zin.read(item.filename)
            
            if HUR_HASH in item.filename or HUR_HASH.encode("utf-8") in data:
                print(f"Safe Byte-Patching HUR Container ({item.filename})...")
                data = patch_raw_container(data, new_hur_bytes)
                
            elif BIOS_HASH in item.filename or BIOS_HASH.encode("utf-8") in data:
                print(f"Safe Byte-Patching BIOS Container ({item.filename})...")
                data = patch_raw_container(data, new_bios_bytes)
                
            zout.writestr(item, data)

print("Crash-Safe OBB Successfully Generated!")
  
