import os
import random
import threading
import time
import socket
import socks
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXY_DIR = os.getenv("PROXY_DIR", "proxies")
SOCKS5_FILE = os.path.join(PROXY_DIR, "socks5.txt")

TEST_HOST = "smtp.gmail.com"
TEST_PORT = 465
TEST_TIMEOUT = 8
MAX_WORKERS = 200

working_proxies = []
lock = threading.Lock()
_scan_lock = threading.Lock()


def load_all_socks5():
    proxies = []
    try:
        with open(SOCKS5_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith(("socks5://", "socks5h://")):
                    proxies.append(line)
                elif ":" in line:
                    proxies.append(f"socks5://{line}")
    except FileNotFoundError:
        print(f"⚠️ فایل {SOCKS5_FILE} پیدا نشد")
    return list(set(proxies))


def test_socks5_for_gmail(proxy_url, timeout=TEST_TIMEOUT):
    sock = None
    try:
        url = proxy_url.replace("socks5h://", "").replace("socks5://", "")
        host, port = url.rsplit(":", 1)
        port = int(port)

        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.set_proxy(socks.SOCKS5, host, port, rdns=True)
        sock.settimeout(timeout)
        sock.connect((TEST_HOST, TEST_PORT))
        return (proxy_url, True)
    except Exception:
        return (proxy_url, False)
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


def scan_all_proxies():
    global working_proxies

    all_proxies = load_all_socks5()
    if not all_proxies:
        print("⚠️ فایل پروکسی خالیه")
        with lock:
            working_proxies = []
        return []

    print(f"🔍 تست {len(all_proxies)} پروکسی...")
    start = time.time()

    found = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_socks5_for_gmail, p) for p in all_proxies]
        for future in as_completed(futures):
            try:
                proxy, ok = future.result()
                if ok:
                    found.append(proxy)
            except Exception:
                pass

    with lock:
        working_proxies = found

    elapsed = round(time.time() - start, 1)
    print(f"🎯 {len(found)} پروکسی سالم از {len(all_proxies)} — {elapsed}s")
    return found


def get_proxy_url():
    global working_proxies

    with lock:
        candidates = list(working_proxies)

    if not candidates:
        with _scan_lock:
            with lock:
                candidates = list(working_proxies)
            if not candidates:
                print("📡 لیست خالی، اسکن کامل...")
                scan_all_proxies()
                with lock:
                    candidates = list(working_proxies)

    if not candidates:
        return None

    random.shuffle(candidates)
    return candidates[0]


def report_proxy_failure(proxy_url):
    with lock:
        if proxy_url in working_proxies:
            working_proxies.remove(proxy_url)
            print(f"🗑️ پروکسی حذف شد: {proxy_url}")


def get_working_count():
    with lock:
        return len(working_proxies)


def start_proxy_loop():
    scan_all_proxies()
    return None
