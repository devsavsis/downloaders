# made by im.savsis.xyz with ♥
import os
import sys
import subprocess
import msvcrt

os.system('')

try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

R   = "\033[0m"
B   = "\033[1m"
GRN = "\033[92m"
GRY = "\033[90m"
WHT = "\033[97m"
CYN = "\033[96m"
RED = "\033[91m"
ORG = "\033[38;5;208m"
MGT = "\033[95m"
DIM = "\033[2m"

BASE = os.path.dirname(os.path.abspath(__file__))

MENU = [
    {
        "label":  "Deezer",
        "sub":    "FLAC Lossless  │  поиск + URL",
        "icon":   "◈",
        "color":  MGT,
        "script": "deezer_dl.py",
    },
    {
        "label":  "SoundCloud",
        "sub":    "FLAC  │  поиск + URL",
        "icon":   "◈",
        "color":  ORG,
        "script": "soundcloud_dl.py",
    },
    {
        "label":  "YouTube",
        "sub":    "MP4 (макс. качество)  │  поиск + URL",
        "icon":   "◈",
        "color":  RED,
        "script": "youtube_dl.py",
    },
]

def draw(sel):
    os.system('cls')
    W = 60
    print()
    print(f"  {WHT}{B}{'━'*W}{R}")
    print(f"  {WHT}{B}{'':^{W}}{R}")
    title = "MUSIC  DOWNLOADER  PACK"
    print(f"  {WHT}{B}{title:^{W}}{R}")
    brand = "im.savsis.xyz"
    print(f"  {GRY}{'made by  ' + brand:^{W}}{R}")
    print(f"  {WHT}{B}{'':^{W}}{R}")
    sub = "↑↓ выбор   Enter запустить   Q выход"
    print(f"  {GRY}{sub:^{W}}{R}")
    print(f"  {WHT}{B}{'':^{W}}{R}")
    print(f"  {WHT}{B}{'━'*W}{R}")
    print()

    for i, item in enumerate(MENU):
        c   = item["color"]
        lbl = item["label"]
        sub = item["sub"]
        if i == sel:
            print(f"  {c}{B}  ▶  {lbl:<14}{R}  {WHT}{sub}{R}")
        else:
            print(f"  {GRY}     {lbl:<14}  {sub}{R}")
        print()

    print(f"  {WHT}{B}{'━'*W}{R}")
    print(f"\n  {DIM}{GRY}Файлы скачиваются в ~/Downloads/<сервис>{R}")
    print(f"  {DIM}{GRY}made by im.savsis.xyz  ♥{R}\n")

def read_key():
    ch = msvcrt.getch()
    if ch in (b'\x00', b'\xe0'):
        return ('spec', msvcrt.getch())
    return ('char', ch)

def run_script(name):
    path = os.path.join(BASE, name)
    os.system('cls')
    subprocess.run([sys.executable, path])

def main():
    sel = 0
    while True:
        draw(sel)
        kind, key = read_key()
        if kind == 'spec':
            if key == b'H':
                sel = (sel - 1) % len(MENU)
            elif key == b'P':
                sel = (sel + 1) % len(MENU)
        elif kind == 'char':
            if key == b'\r':
                run_script(MENU[sel]["script"])
            elif key in (b'q', b'Q', b'\x1b'):
                os.system('cls')
                break

if __name__ == "__main__":
    main()
