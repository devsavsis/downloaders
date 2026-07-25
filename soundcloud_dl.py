import subprocess
import sys
import os
import re
import zipfile
import shutil
import urllib.request
import msvcrt

os.system('')

def pip_install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--upgrade", pkg],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    import yt_dlp
except ImportError:
    print("Устанавливаю yt-dlp...")
    pip_install("yt-dlp")
    import yt_dlp

FFMPEG_DIR = os.path.join(os.path.expanduser("~"), ".local_ffmpeg")
FFMPEG_EXE = os.path.join(FFMPEG_DIR, "ffmpeg.exe")

def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return None
    if os.path.exists(FFMPEG_EXE):
        return FFMPEG_DIR
    os.makedirs(FFMPEG_DIR, exist_ok=True)
    zip_path = os.path.join(FFMPEG_DIR, "ffmpeg.zip")
    url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    print("Скачиваю ffmpeg (один раз)...")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            bname = os.path.basename(name)
            if bname in ("ffmpeg.exe", "ffprobe.exe"):
                src = zf.extract(name, FFMPEG_DIR)
                dst = os.path.join(FFMPEG_DIR, bname)
                if src != dst:
                    shutil.move(src, dst)
    os.remove(zip_path)
    for item in os.listdir(FFMPEG_DIR):
        p = os.path.join(FFMPEG_DIR, item)
        if os.path.isdir(p):
            shutil.rmtree(p)
    print("ffmpeg готов.")
    return FFMPEG_DIR

try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

R   = "\033[0m"
B   = "\033[1m"
CYN = "\033[96m"
GRN = "\033[92m"
YLW = "\033[93m"
GRY = "\033[90m"
WHT = "\033[97m"
ORG = "\033[38;5;208m"

PAGE_SIZE = 8
OUT_DIR   = os.path.join(os.path.expanduser("~"), "Downloads", "SoundCloud")
os.makedirs(OUT_DIR, exist_ok=True)
ffmpeg_location = ensure_ffmpeg()

def fmt_dur(s):
    if not s: return "?:??"
    m, s = divmod(int(s), 60)
    return f"{m}:{s:02d}"

def trunc(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n-1] + "…"

def read_key():
    ch = msvcrt.getch()
    if ch in (b'\x00', b'\xe0'):
        return ('spec', msvcrt.getch())
    return ('char', ch)

def draw(items, sel, query, page, total_pages):
    os.system('cls')
    W = 74
    print(f"\n{ORG}{'▄'*W}{R}")
    print(f"  {ORG}{B}SoundCloud{R}  {GRY}▸{R}  {WHT}«{query}»{R}")
    print(f"  {GRY}↑↓ выбор   ←→ страница {page+1}/{total_pages}   Enter скачать   Esc новый поиск{R}")
    print(f"{ORG}{'▀'*W}{R}\n")
    for i, it in enumerate(items):
        uploader = trunc(it.get('uploader',''), 24)
        title    = trunc(it.get('title',''), 32)
        dur      = it.get('dur','')
        line     = f"{uploader:<24}  {title:<32}  {GRY}{dur}{R}"
        if i == sel:
            print(f"  {GRN}{B}▶  {line}{R}")
        else:
            print(f"     {GRY}{line}{R}")
    print(f"\n{ORG}{'▄'*W}{R}\n")

def tui_pick(pages, query):
    page = 0
    sel  = 0
    while True:
        cur = pages[page]
        draw(cur, sel, query, page, len(pages))
        kind, key = read_key()
        if kind == 'spec':
            if key == b'H':
                sel = max(0, sel - 1)
            elif key == b'P':
                sel = min(len(cur)-1, sel + 1)
            elif key == b'M' and page < len(pages)-1:
                page += 1; sel = 0
            elif key == b'K' and page > 0:
                page -= 1; sel = 0
        elif kind == 'char':
            if key == b'\r':
                return cur[sel]
            elif key == b'\x1b':
                return None

def search_soundcloud(query, limit=16):
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"scsearch{limit}:{query}", download=False)
        raw  = info.get("entries", []) if info else []
    items = []
    for t in raw:
        items.append({
            'url':      t.get('url') or t.get('webpage_url',''),
            'uploader': t.get('uploader',''),
            'title':    t.get('title',''),
            'dur':      fmt_dur(t.get('duration')),
        })
    return [items[i:i+PAGE_SIZE] for i in range(0, len(items), PAGE_SIZE)] if items else []

def is_sc_url(s):
    return bool(re.match(r"https?://(www\.)?soundcloud\.com/", s))

def download(url):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(OUT_DIR, "%(uploader)s - %(title)s.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "flac"}],
        "quiet": False,
    }
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

def main():
    os.system('cls')
    print(f"\n{ORG}{B}  ══════════════════════════════════════{R}")
    print(f"{ORG}{B}    SoundCloud Downloader  →  FLAC       {R}")
    print(f"{ORG}{B}  ══════════════════════════════════════{R}")
    print(f"  {GRY}Папка: {OUT_DIR}{R}\n")

    while True:
        print(f"\n  {GRY}Введи URL или поисковый запрос  │  'q' выход{R}")
        query = input(f"  {ORG}▸{R} ").strip()

        if not query: continue
        if query.lower() == 'q': break

        if is_sc_url(query):
            os.system('cls')
            print(f"\n  {GRN}Скачиваю: {query}{R}\n")
            try:
                download(query)
                print(f"\n  {GRN}Готово! → {OUT_DIR}{R}")
            except Exception as e:
                print(f"\n  Ошибка: {e}")
            input(f"\n  {GRY}Enter чтобы продолжить...{R}")
            continue

        print(f"  {GRY}Ищу...{R}", end="\r")
        try:
            pages = search_soundcloud(query)
        except Exception as e:
            print(f"  Ошибка поиска: {e}\n"); continue

        if not pages:
            print(f"  {YLW}Ничего не найдено.{R}\n"); continue

        track = tui_pick(pages, query)
        if track is None:
            continue

        url = track['url']
        os.system('cls')
        print(f"\n  {GRN}Скачиваю: {track['uploader']} — {track['title']}{R}\n")
        try:
            download(url)
            print(f"\n  {GRN}Готово! → {OUT_DIR}{R}")
        except Exception as e:
            print(f"\n  Ошибка: {e}")
        input(f"\n  {GRY}Enter чтобы продолжить...{R}")

if __name__ == "__main__":
    main()
    input("\nНажми Enter для выхода...")
