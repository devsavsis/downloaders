import subprocess
import sys
import os
import re
import zipfile
import shutil
import urllib.request
import urllib.parse
import json
import webbrowser
import time
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

try:
    import requests
except ImportError:
    pip_install("requests")
    import requests

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
MGT = "\033[95m"

PAGE_SIZE = 8
ARL_FILE  = os.path.join(os.path.expanduser("~"), ".deezer_arl.txt")
OUT_DIR   = os.path.join(os.path.expanduser("~"), "Downloads", "Deezer")
BROWSERS  = ["chrome", "edge", "firefox", "chromium", "opera", "brave", "vivaldi"]

os.makedirs(OUT_DIR, exist_ok=True)
ffmpeg_location = ensure_ffmpeg()

def fmt_dur(s):
    if not s: return "?:??"
    m, s = divmod(int(s), 60)
    return f"{m}:{s:02d}"

def trunc(s, n):
    return s if len(s) <= n else s[:n-1] + "…"

def read_key():
    ch = msvcrt.getch()
    if ch in (b'\x00', b'\xe0'):
        return ('spec', msvcrt.getch())
    return ('char', ch)

def draw(items, sel, query, page, total_pages):
    os.system('cls')
    W = 74
    header = f"  {CYN}{B}Deezer{R}  {GRY}▸{R}  {WHT}«{query}»{R}"
    nav    = f"  {GRY}↑↓ выбор   ←→ страница {page+1}/{total_pages}   Enter скачать   Esc новый поиск{R}"
    print(f"\n{CYN}{'▄'*W}{R}")
    print(header)
    print(nav)
    print(f"{CYN}{'▀'*W}{R}\n")
    for i, it in enumerate(items):
        artist = trunc(it.get('artist',''), 22)
        title  = trunc(it.get('title',''), 30)
        album  = trunc(it.get('album',''), 18)
        dur    = it.get('dur','')
        line   = f"{artist:<22}  {title:<30}  {GRY}{album:<18}  {dur}{R}"
        if i == sel:
            print(f"  {GRN}{B}▶  {line}{R}")
        else:
            print(f"     {GRY}{line}{R}")
    print(f"\n{CYN}{'▄'*W}{R}\n")

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

def search_deezer(query, limit=20):
    q = urllib.parse.quote(query)
    r = requests.get(f"https://api.deezer.com/search?q={q}&limit={limit}", timeout=10)
    raw = r.json().get("data", [])
    items = []
    for t in raw:
        items.append({
            'id':     t['id'],
            'artist': t['artist']['name'],
            'title':  t['title'],
            'album':  t.get('album',{}).get('title',''),
            'dur':    fmt_dur(t.get('duration',0)),
        })
    return [items[i:i+PAGE_SIZE] for i in range(0, len(items), PAGE_SIZE)] if items else []

def get_arl_from_browser():
    try:
        import browser_cookie3
    except ImportError:
        pip_install("browser-cookie3")
        import browser_cookie3
    for br in BROWSERS:
        try:
            loader = getattr(browser_cookie3, br, None)
            if not loader: continue
            for c in loader(domain_name=".deezer.com"):
                if c.name == "arl" and len(c.value) > 50:
                    return c.value
        except Exception:
            continue
    return None

def load_arl():
    if os.path.exists(ARL_FILE):
        v = open(ARL_FILE).read().strip()
        if len(v) > 50: return v
    return None

def save_arl(v):
    open(ARL_FILE, "w").write(v)

def login_flow():
    os.system('cls')
    print(f"\n{CYN}{B}  Deezer — Авторизация{R}\n")
    print("  Открываю браузер на странице входа...")
    webbrowser.open("https://www.deezer.com/login")
    time.sleep(2)
    input(f"\n  {YLW}Войди в Deezer в браузере, затем нажми Enter...{R} ")
    print("  Считываю куки автоматически...")
    arl = get_arl_from_browser()
    if arl:
        save_arl(arl)
        print(f"  {GRN}Авторизация успешна!{R}")
        time.sleep(1)
        return arl
    print(f"\n  {YLW}Не удалось считать автоматически.{R}")
    print("  F12 → Application → Cookies → deezer.com → скопируй 'arl'")
    arl = input("  Вставь ARL вручную: ").strip()
    if len(arl) > 50:
        save_arl(arl)
        return arl
    return None

def download(arl, url, is_track=True):
    opts = {
        "outtmpl": os.path.join(OUT_DIR, "%(uploader)s - %(title)s.%(ext)s"),
        "format": "flac/bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "flac"}],
        "quiet": False,
        "noplaylist": is_track,
        "http_headers": {"Cookie": f"arl={arl}"},
    }
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

def is_deezer_url(s):
    return bool(re.match(r"https?://(www\.)?deezer\.com/", s))

def main():
    os.system('cls')
    print(f"\n{CYN}{B}  ══════════════════════════════════════{R}")
    print(f"{CYN}{B}    Deezer Downloader  →  FLAC Lossless  {R}")
    print(f"{CYN}{B}  ══════════════════════════════════════{R}")
    print(f"  {GRY}Папка: {OUT_DIR}{R}\n")

    arl = load_arl()
    if arl:
        print(f"  {GRN}✓ Авторизация найдена{R}\n")
    else:
        arl = login_flow()
        if not arl:
            print("Выход."); return

    while True:
        print(f"\n  {GRY}Введи URL или поисковый запрос  │  'login' │ 'q' выход{R}")
        query = input(f"  {CYN}▸{R} ").strip()

        if not query: continue
        if query.lower() == 'q': break
        if query.lower() == 'login':
            arl = login_flow()
            continue

        if is_deezer_url(query):
            os.system('cls')
            print(f"\n  {GRN}Скачиваю: {query}{R}\n")
            try:
                download(arl, query, "/track/" in query)
                print(f"\n  {GRN}Готово! → {OUT_DIR}{R}")
            except Exception as e:
                print(f"\n  Ошибка: {e}")
            input(f"\n  {GRY}Enter чтобы продолжить...{R}")
            continue

        print(f"  {GRY}Ищу...{R}", end="\r")
        try:
            pages = search_deezer(query)
        except Exception as e:
            print(f"  Ошибка поиска: {e}\n"); continue

        if not pages:
            print(f"  {YLW}Ничего не найдено.{R}\n"); continue

        track = tui_pick(pages, query)
        if track is None:
            continue

        url = f"https://www.deezer.com/track/{track['id']}"
        os.system('cls')
        print(f"\n  {GRN}Скачиваю: {track['artist']} — {track['title']}{R}\n")
        try:
            download(arl, url, True)
            print(f"\n  {GRN}Готово! → {OUT_DIR}{R}")
        except Exception as e:
            print(f"\n  Ошибка: {e}")
            if "401" in str(e) or "403" in str(e):
                print(f"  {YLW}Попробуй обновить авторизацию → введи 'login'{R}")
        input(f"\n  {GRY}Enter чтобы продолжить...{R}")

if __name__ == "__main__":
    main()
    input("\nНажми Enter для выхода...")
