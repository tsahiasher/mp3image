import shutil
from PIL import Image
import os
import sys

source_path = r"C:\Users\zahi.asher\.gemini\antigravity\brain\4bee783e-44c3-462d-b337-dc4394c1b4a7\uploaded_image_1768896165821.png"
dest_png = r"C:\Temp\mp3image\C_Sharp\icon.png"
dest_ico = r"C:\Temp\mp3image\C_Sharp\icon.ico"

print(f"Copying from {source_path} to {dest_png}")

try:
    shutil.copy2(source_path, dest_png)
    print("Copy successful.")
except Exception as e:
    print(f"Copy failed: {e}")
    # Try install Pillow if missing, but assuming it might require it for the next step.
    
print(f"Converting to {dest_ico}")
try:
    img = Image.open(dest_png)
    img.save(dest_ico, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("Conversion successful.")
except ImportError:
    print("Pillow not installed? Trying to run without conversion (icon.png might work if renamed? No, csproj expects .ico).")
    # install pillow
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    # try again
    img = Image.open(dest_png)
    img.save(dest_ico, format='ICO', sizes=[(256, 256), (128, 128)])
    print("Conversion successful after install.")
except Exception as e:
    print(f"Conversion failed: {e}")
    sys.exit(1)
