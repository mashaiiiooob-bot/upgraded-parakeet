import json
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

# فقط کش پروکسی‌ها را مدیریت می‌کند.
# این فایل هیچ تغییری در فایل‌های دیتابیس ربات ایجاد نمی‌کند
# و به SMTP/ارسال ایمیل متصل نیست.

BASE_URL = "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/"
PROXY_FILES = {
    "http": "protocols/http.txt",
    "https": "protocols/https.txt",
    "socks4": "protocols/socks4.txt",
    "socks5": "protocols/socks5.txt",
}

PROXY_DIR = os.getenv("PROXY_DIR", "proxies")
STATUS_FILE = os.path.join(PROXY_DIR, "update_status.json")
INTERVAL_SECONDS = 30 * 60
TIMEOUT = 20


def atomic_write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".proxy_tmp_",
        dir=os.path.dirname(path),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "proxy-cache-updater/1.0"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8")


def valid_proxy_list(text):
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # فقط قالب host:port را برای کش قبول می‌کنیم.
        if ":" not in line:
            continue
        host, port = line.rsplit(":", 1)
        if not host or not port.isdigit():
            continue
        port_num = int(port)
        if 1 <= port_num <= 65535:
            lines.append(f"{host}:{port_num}")
    return sorted(set(lines))


def update_once():
    os.makedirs(PROXY_DIR, exist_ok=True)
    counts = {}
    errors = []

    for kind, relative_path in PROXY_FILES.items():
        try:
            raw = fetch(BASE_URL + relative_path)
            proxies = valid_proxy_list(raw)

            # اگر منبع خالی/خراب بود، فایل قبلی را دست نمی‌زنیم.
            if not proxies:
                raise ValueError("empty or invalid proxy list")

            target = os.path.join(PROXY_DIR, f"{kind}.txt")
            atomic_write(target, "\n".join(proxies) + "\n")
            counts[kind] = len(proxies)
        except Exception as exc:
            errors.append(f"{kind}: {exc}")

    status = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "errors": errors,
        "source": "IPLocate/free-proxy-list",
    }
    atomic_write(
        STATUS_FILE,
        json.dumps(status, ensure_ascii=False, indent=2),
    )

    print(f"[proxy-updater] update: {counts}")
    if errors:
        print(f"[proxy-updater] errors: {errors}")

    return not errors


def run_forever():
    while True:
        try:
            update_once()
        except Exception as exc:
            print(f"[proxy-updater] unexpected error: {exc}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
