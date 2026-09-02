"""Empacota o Subliminal Pro num executável standalone (.exe) com PyInstaller.

Uso:
    pip install pyinstaller pystray pillow
    python build.py

O executável final fica em dist/SubliminalPro.exe
"""
import os
import subprocess
import sys

from build_icon import make_icon


def main():
    if not os.path.exists("icon.ico"):
        make_icon()
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed",
        "--name", "SubliminalPro",
        "--icon", "icon.ico",
        "subliminal_pro.py",
    ], check=True)


if __name__ == "__main__":
    main()
