import os
import random
import threading
import requests
from telebot import apihelper
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

PROXY_DIR = os.getenv("PROXY_DIR", "proxies")

working_proxies = []
lock = threading.Lock()


def load_proxies_from_file(file_path, proxy_type):
    proxies = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    proxies.append(f"{proxy_type}://{line}")
    except FileNotFoundError:
        print(f"⚠️ فایل {file_path} پیدا نشد")
    return proxies


def test_proxy(proxy_url, timeout=8):
    try:
        r = requests.get(
            "https://api.telegram.org",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=timeout,
            verify=False,
        )
        if r.status_code == 200:
            return proxy_url
    except Exception:
        pass
    return None


def find_working_proxies(sample_size=200, max_workers=50):
    global working_proxies

    all_proxies = []
    all_proxies.extend(load_proxies_from_file(
        os.path.join(PROXY_DIR, "socks5.txt"), "socks5"
    ))
    all_proxies.extend(load_proxies_from_file(
        os.path.join(PROXY_DIR, "https.txt"), "https"
    ))

    if not all_proxies:
        print("❌ هیچ پروکسی‌ای پیدا نشد")
        return []

    random.shuffle(all_proxies)
    sample = all_proxies[:sample_size]

    print(f"🔍 تست {len(sample)} پروکسی از {len(all_proxies)} تا...")

    found = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy, p): p for p in sample}
        for future in as_completed(futures):
            result = future.result()
            if result:
                with lock:
                    found.append(result)
                    print(f"✅ پروکسی سالم: {result}")

    with lock:
        working_proxies = found

    print(f"🎯 تعداد پروکسی سالم: {len(found)}")
    return found


def get_proxy():
    """یه پروکسی سالم برمی‌گردونه (برای استفاده توی requests)"""
    global working_proxies

    if not working_proxies:
        find_working_proxies()

    if not working_proxies:
        return None

    proxy_url = random.choice(working_proxies)
    return {"http": proxy_url, "https": proxy_url}


def get_proxy_url(proxy_type=None):
    """
    یه پروکسی سالم رو به‌صورت رشته (URL) برمی‌گردونه، نه دیکشنری.
    مثال خروجی: "socks5://1.2.3.4:1080"

    proxy_type: اگه مقدار بدی (مثلاً "socks5")، فقط پروکسی از همون نوع
    برگردونده می‌شه. برای اتصال SMTP از طریق SOCKS5 معمولاً باید
    proxy_type="socks5" پاس بدی.
    """
    global working_proxies

    if not working_proxies:
        find_working_proxies()

    if not working_proxies:
        return None

    candidates = working_proxies
    if proxy_type:
        candidates = [p for p in working_proxies if p.startswith(f"{proxy_type}://")]
        if not candidates:
            return None

    return random.choice(candidates)


def build_socks5_proxy_dict(proxy_url):
    """
    رشته‌ی پروکسی مثل 'socks5://user:pass@1.2.3.4:1080' یا 'socks5://1.2.3.4:1080'
    رو به دیکشنری‌ای تبدیل می‌کنه که کلاس Socks5SMTP_SSL توی ali.py انتظارش رو داره:
    {"host": ..., "port": ..., "rdns": ..., "username": ..., "password": ...}

    اگه proxy_url خالی/None باشه، None برمی‌گردونه.
    """
    if not proxy_url:
        return None

    parsed = urlparse(proxy_url)

    if not parsed.hostname or not parsed.port:
        return None

    return {
        "host": parsed.hostname,
        "port": parsed.port,
        "rdns": True,
        "username": parsed.username,
        "password": parsed.password,
    }


def get_socks5_proxy_dict():
    """
    یه پروکسی سالم از نوع socks5 پیدا می‌کنه و مستقیم به‌صورت دیکشنری
    آماده برای Socks5SMTP_SSL برمی‌گردونه. اگه پروکسی سالمی پیدا نشه، None می‌ده.
    """
    proxy_url = get_proxy_url(proxy_type="socks5")
    return build_socks5_proxy_dict(proxy_url)


def apply_random_proxy(sample_size=200):
    """پیدا کردن و اعمال یه پروکسی سالم روی telebot"""
    global working_proxies

    if not working_proxies:
        find_working_proxies(sample_size=sample_size)

    if not working_proxies:
        print("⚠️ هیچ پروکسی سالمی پیدا نشد")
        return False

    proxy_url = random.choice(working_proxies)
    apihelper.proxy = {"http": proxy_url, "https": proxy_url}
    print(f"✅ پروکسی اعمال شد: {proxy_url}")
    return True
