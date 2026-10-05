import sys, os

# Arguments: 1=Original Asset File, 2=Edited HUR_1.txt, 3=Output Asset File
asset_file = sys.argv[1]
json_file = sys.argv[2]
output_file = sys.argv[3]

with open(asset_file, "rb") as f:
    asset_bytes = bytearray(f.read())

with open(json_file, "r", encoding="utf-8") as f:
    new_json_data = f.read().encode("utf-8")

# Target string ko locate karna ya directly replace karna
# In-place safety: Agar naya JSON chhota hai to spaces se fill karo
if len(new_json_data) < len(asset_bytes):
    # Padding with spaces to maintain size
    padded_data = new_json_data + b" " * (len(asset_bytes) - len(new_json_data))
else:
    padded_data = new_json_data

os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "wb") as f:
    f.write(padded_data)

print(f"Asset file successfully packed to: {output_file}")
  
