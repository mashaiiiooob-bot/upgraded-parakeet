import os
import random
import requests
from telebot import apihelper

PROXY_DIR = os.getenv("PROXY_DIR", "proxies")

def load_proxies():
    """خوندن پروکسی‌ها از پوشه proxies"""
    all_proxies = []
    for kind in ["socks5", "http", "https"]:
        path = os.path.join(PROXY_DIR, f"{kind}.txt")
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and ":" in line:
                        all_proxies.append(f"{kind}://{line}")
        except FileNotFoundError:
            pass
    return all_proxies

def test_proxy(proxy_url, timeout=5):
    """تست یه پروکسی"""
    try:
        r = requests.get(
            "https://api.telegram.org",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=timeout,
        )
        return r.status_code == 200
    except:
        return False

def apply_random_proxy(max_test=30):
    """پیدا کردن و اعمال یه پروکسی سالم"""
    proxies = load_proxies()
    if not proxies:
        print("⚠️ هیچ پروکسی‌ای توی proxies/ پیدا نشد")
        return False
    
    random.shuffle(proxies)
    
    for proxy_url in proxies[:max_test]:
        if test_proxy(proxy_url):
            apihelper.proxy = {"http": proxy_url, "https": proxy_url}
            print(f"✅ پروکسی اعمال شد: {proxy_url}")
            return True
    
    print("❌ هیچ پروکسی سالمی پیدا نشد")
    return False
