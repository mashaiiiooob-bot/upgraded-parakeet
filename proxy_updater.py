import os
import time

PROXY_DIR = os.getenv("PROXY_DIR", "proxies")
UPDATE_INTERVAL = int(os.getenv("PROXY_UPDATE_INTERVAL", "1800"))


def run_forever():
    os.makedirs(PROXY_DIR, exist_ok=True)

    while True:
        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    run_forever()
