import subprocess
import sys

def main():
    bot = subprocess.Popen([sys.executable, "ali.py"])
    updater = subprocess.Popen([sys.executable, "proxy_updater.py"])

    try:
        bot.wait()
    finally:
        updater.terminate()
        try:
            updater.wait(timeout=10)
        except subprocess.TimeoutExpired:
            updater.kill()

if __name__ == "__main__":
    main()
