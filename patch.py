import os
import sys

def patch_game_files(extracted_dir):
    print("Starting game files patching process...")
    
    # 1. Path to global-metadata.dat (Unity IL2CPP metadata)
    metadata_path = os.path.join(extracted_dir, "assets/bin/Data/Managed/Metadata/global-metadata.dat")
    
    if os.path.exists(metadata_path):
        print(f"Found metadata file at: {metadata_path}")
        with open(metadata_path, "rb") as f:
            content = f.read()
        
        # Example modification logic:
        # Unity metadata mein numbers ya string values (jaise squad size 18/20) ko 
        # binary level par search karke replace kiya ja sakta hai.
        print("Analyzing metadata structure...")
        
        # Yahan aap apna custom byte replacement ya search-replace dal sakte hain
        # Jaise agar koi specific string ya integer milta hai:
        # modified_content = content.replace(b'\x12\x00\x00\x00', b'\x0c\x00\x00\x00') # Example for 18 -> 12 hex
        
        # Filhal hum file ko as-is ya modified likhte hain
        with open(metadata_path, "wb") as f:
            f.write(content)
        print("Metadata check completed.")
    else:
        print("global-metadata.dat not found in standard Unity path.")

    # 2. Check for any JSON team files inside assets if unpacked
    json_dir = os.path.join(extracted_dir, "assets")
    if os.path.exists(json_dir):
        print("Scanning assets folder for team configuration files...")
        for root, dirs, files in os.walk(json_dir):
            for file in files:
                if file.endswith(".txt") or file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as fx:
                            data = fx.read()
                        
                        # Agar file mein team players ka data hai, toh yahan automatic fix kar sakte hain
                        if "PlayerDetails" in data:
                            print(f"Found team configuration file: {file}")
                    except Exception as e:
                        pass

    print("Patching script execution finished successfully!")

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "decompiled_game"
    patch_game_files(target_dir)
    
