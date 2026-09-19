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
ROUND_DELAY = 5

working_proxies = []
lock = threading.Lock()
_stop_flag = threading.Event()
_round_counter = 0
_loop_started = False
_loop_lock = threading.Lock()


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
    try:
        url = proxy_url.replace("socks5h://", "").replace("socks5://", "")
        host, port = url.rsplit(":", 1)
        port = int(port)

        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.set_proxy(socks.SOCKS5, host, port, rdns=True)
        sock.settimeout(timeout)
        sock.connect((TEST_HOST, TEST_PORT))
        sock.close()
        return (proxy_url, True)
    except Exception:
        return (proxy_url, False)


def proxy_loop():
    global working_proxies, _round_counter

    while not _stop_flag.is_set():
        try:
            _round_counter += 1
            round_num = _round_counter
            all_proxies = load_all_socks5()

            if not all_proxies:
                print(f"⚠️ [دور {round_num}] فایل socks5 خالیه، ۳۰ ثانیه صبر...")
                time.sleep(30)
                continue

            print(f"🔍 [دور {round_num}] تست {len(all_proxies)} پروکسی...")
            start = time.time()

            found = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(test_socks5_for_gmail, p): p for p in all_proxies}
                for future in as_completed(futures):
                    if _stop_flag.is_set():
                        break
                    try:
                        proxy, ok = future.result()
                        if ok:
                            found.append(proxy)
                    except Exception:
                        pass

            with lock:
                working_proxies = found

            elapsed = round(time.time() - start, 1)
            print(f"🎯 [دور {round_num}] {len(found)} سالم از {len(all_proxies)} — {elapsed}s")

        except Exception as e:
            print(f"⚠️ [دور {_round_counter}] خطا: {e}")

        time.sleep(ROUND_DELAY)

    print("🛑 [proxy-loop] متوقف شد")


def start_proxy_loop():
    global _loop_started
    with _loop_lock:
        if _loop_started:
            return None
        _loop_started = True

    thread = threading.Thread(target=proxy_loop, daemon=True, name="proxy-loop")
    thread.start()
    print("✅ [proxy-loop] استارت خورد")
    return thread


def stop_proxy_loop():
    _stop_flag.set()


def get_proxy_url(max_attempts=5):
    global working_proxies

    with lock:
        candidates = list(working_proxies)

    if not candidates:
        print("⚠️ لیست پروکسی خالی، تست فوری...")
        all_proxies = load_all_socks5()
        random.shuffle(all_proxies)

        executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        futures = [executor.submit(test_socks5_for_gmail, p) for p in all_proxies[:500]]

        found = []
        for future in as_completed(futures):
            try:
                proxy, ok = future.result()
                if ok:
                    found.append(proxy)
                if len(found) >= 50:
                    for f in futures:
                        f.cancel()
                    break
            except Exception:
                pass

        executor.shutdown(wait=False, cancel_futures=True)

        with lock:
            working_proxies = found

        with lock:
            candidates = list(working_proxies)

    if not candidates:
        return None

    random.shuffle(candidates)

    for proxy_url in candidates[:max_attempts]:
        if test_socks5_for_gmail(proxy_url, timeout=5)[1]:
            return proxy_url
        else:
            with lock:
                if proxy_url in working_proxies:
                    working_proxies.remove(proxy_url)
                    print(f"🗑️ پروکسی مرده حذف شد: {proxy_url}")

    return None


def get_working_count():
    with lock:
        return len(working_proxies)
