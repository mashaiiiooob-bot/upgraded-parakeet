import subprocess
import sys

def main():
    bot = subprocess.Popen([sys.executable, "ali.py"])
    bot.wait()

if __name__ == "__main__":
    main()
