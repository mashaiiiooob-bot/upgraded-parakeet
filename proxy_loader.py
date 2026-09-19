import os
import random
import threading
import requests
from telebot import apihelper
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXY_DIR = os.getenv("PROXY_DIR", "proxies")

# پروکسی‌های سالم که پیدا شدن
working_proxies = []
lock = threading.Lock()


def load_proxies_from_file(file_path, proxy_type):
    """خوندن پروکسی‌ها از یه فایل"""
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
    """تست یه پروکسی - اگه سالم بود برمی‌گردونه"""
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
    """تست موازی پروکسی‌ها"""
    global working_proxies

    # خوندن پروکسی‌ها از فایل‌ها
    all_proxies = []
    
    # socks5 (بهترین برای تلگرام)
    all_proxies.extend(load_proxies_from_file(
        os.path.join(PROXY_DIR, "socks5.txt"), "socks5"
    ))
    # http
    all_proxies.extend(load_proxies_from_file(
        os.path.join(PROXY_DIR, "http.txt"), "http"
    ))
    # https
    all_proxies.extend(load_proxies_from_file(
        os.path.join(PROXY_DIR, "https.txt"), "https"
    ))

    if not all_proxies:
        print("❌ هیچ پروکسی‌ای توی فایل‌ها پیدا نشد")
        return []

    # نمونه‌برداری تصادفی
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


def apply_random_proxy(sample_size=200):
    """پیدا کردن و اعمال یه پروکسی سالم"""
    global working_proxies

    # اگه پروکسی سالم داریم، ازشون استفاده کن
    if working_proxies:
        proxy_url = random.choice(working_proxies)
        apihelper.proxy = {"http": proxy_url, "https": proxy_url}
        print(f"✅ پروکسی اعمال شد (از کش): {proxy_url}")
        return True

    # وگرنه یه سری جدید تست کن
    found = find_working_proxies(sample_size=sample_size)
    if not found:
        print("⚠️ هیچ پروکسی سالمی پیدا نشد")
        return False

    proxy_url = random.choice(found)
    apihelper.proxy = {"http": proxy_url, "https": proxy_url}
    print(f"✅ پروکسی اعمال شد: {proxy_url}")
    return True
