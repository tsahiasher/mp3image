from PIL import Image
import sys
import os

def convert_to_ico(source, target):
    try:
        img = Image.open(source)
        img.save(target, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"Successfully converted {source} to {target}")
    except Exception as e:
        print(f"Error converting image: {e}")
        sys.exit(1)

if __name__ == "__main__":
    convert_to_ico("C:/Temp/mp3image/C_Sharp/icon.png", "C:/Temp/mp3image/C_Sharp/icon.ico")
