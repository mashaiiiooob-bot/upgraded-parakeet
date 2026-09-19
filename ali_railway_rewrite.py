import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import requests
import telebot
from telebot import types

# Optional proxy support. The bot can still start if the proxy helper is unavailable.
try:
    from proxy_loader import apply_random_proxy
except Exception:
    apply_random_proxy = None

try:
    from proxy_updater import run_forever
except Exception:
    run_forever = None


# =========================
# Configuration
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")

ADMIN_ID = int(os.getenv("ADMIN_ID", "7587661627"))
DATA_DIR = os.getenv("DATA_DIR", "data")
POLL_TIMEOUT = int(os.getenv("POLL_TIMEOUT", "30"))

os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
BLACKLIST_FILE = os.path.join(DATA_DIR, "blacklist.json")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("telegram-bot")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# =========================
# JSON storage
# =========================

def load_json(path, default):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return default


def save_json(path, data):
    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
    except OSError:
        logger.exception("Could not save %s", path)


def load_users():
    return load_json(USERS_FILE, {})


def save_users(data):
    save_json(USERS_FILE, data)


def load_reports():
    return load_json(REPORTS_FILE, {})


def save_reports(data):
    save_json(REPORTS_FILE, data)


def load_blacklist():
    return load_json(BLACKLIST_FILE, {})


def save_blacklist(data):
    save_json(BLACKLIST_FILE, data)


# =========================
# Helpers
# =========================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def is_admin(user_id):
    return int(user_id) == ADMIN_ID


def has_access(user_id):
    user_id = str(user_id)
    if is_admin(int(user_id)):
        return True

    users = load_users()
    return bool(users.get(user_id, {}).get("has_subscription", False))


def ensure_user(tg_user):
    user_id = str(tg_user.id)
    users = load_users()

    if user_id not in users:
        users[user_id] = {
            "username": tg_user.username or "",
            "first_name": tg_user.first_name or "کاربر",
            "join_date": now_iso(),
            "last_activity": now_iso(),
            "has_subscription": False,
            "total_actions": 0,
            "total_reports": 0,
            "preferences": {
                "language": "fa",
                "notifications": True,
            },
        }
    else:
        users[user_id]["username"] = tg_user.username or users[user_id].get("username", "")
        users[user_id]["first_name"] = tg_user.first_name or users[user_id].get("first_name", "کاربر")
        users[user_id]["last_activity"] = now_iso()

    save_users(users)
    return users[user_id]


def safe_text(value, limit=1000):
    value = str(value or "")
    return value[:limit]


def send_admin_log(text):
    try:
        bot.send_message(ADMIN_ID, text)
    except Exception:
        logger.exception("Could not send admin log")


def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("👤 حساب کاربری", callback_data="profile"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
    )
    markup.add(
        types.InlineKeyboardButton("📋 گزارش‌ها", callback_data="reports"),
        types.InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
    )
    markup.add(
        types.InlineKeyboardButton("❓ راهنما", callback_data="help")
    )

    if is_admin(user_id):
        markup.add(
            types.InlineKeyboardButton("👑 پنل مدیریت", callback_data="admin")
        )

    return markup


def show_main_menu(chat_id, user_id, edit_message_id=None):
    user = load_users().get(str(user_id), {})
    status = "فعال ✅" if has_access(user_id) else "بدون اشتراک ⛔"

    text = (
        "<b>🤖 پنل اصلی</b>\n\n"
        f"👤 نام: {safe_text(user.get('first_name', 'کاربر'), 100)}\n"
        f"🆔 آیدی: <code>{user_id}</code>\n"
        f"📌 وضعیت: {status}\n\n"
        "از دکمه‌های زیر استفاده کنید."
    )

    markup = main_menu(user_id)

    if edit_message_id is None:
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.edit_message_text(
            text,
            chat_id,
            edit_message_id,
            reply_markup=markup,
        )


# =========================
# /start
# =========================

@bot.message_handler(commands=["start"])
def start_handler(message):
    user = ensure_user(message.from_user)

    if is_admin(message.from_user.id):
        show_main_menu(message.chat.id, message.from_user.id)
        return

    if not user.get("has_subscription", False):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "📞 تماس با پشتیبانی",
            callback_data="support",
        ))

        bot.send_message(
            message.chat.id,
            "<b>⛔ دسترسی محدود</b>\n\n"
            "حساب شما هنوز فعال نشده است.\n"
            f"🆔 آیدی شما: <code>{message.from_user.id}</code>\n\n"
            "برای فعال‌سازی با پشتیبانی تماس بگیرید.",
            reply_markup=markup,
        )
        return

    show_main_menu(message.chat.id, message.from_user.id)


# =========================
# /admin
# =========================

@bot.message_handler(commands=["admin"])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return

    show_admin_panel(
        message.chat.id,
        message.from_user.id,
        edit_message_id=None,
    )


def show_admin_panel(chat_id, user_id, edit_message_id=None):
    if not is_admin(user_id):
        return

    users = load_users()
    reports = load_reports()
    blacklist = load_blacklist()

    subscribed = sum(
        1 for user in users.values()
        if user.get("has_subscription", False)
    )

    text = (
        "<b>👑 پنل مدیریت</b>\n\n"
        f"👥 کاربران: {len(users)}\n"
        f"🎫 دارای اشتراک: {subscribed}\n"
        f"📋 گزارش‌ها: {len(reports)}\n"
        f"🚫 لیست سیاه: {len(blacklist)}\n"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 کاربران", callback_data="admin_users"),
        types.InlineKeyboardButton("🎫 اشتراک", callback_data="admin_subscription"),
    )
    markup.add(
        types.InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
        types.InlineKeyboardButton("📋 گزارش‌ها", callback_data="admin_reports"),
    )
    markup.add(
        types.InlineKeyboardButton("🚫 لیست سیاه", callback_data="admin_blacklist"),
        types.InlineKeyboardButton("🔄 بازگشت", callback_data="back"),
    )

    if edit_message_id is None:
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.edit_message_text(
            text,
            chat_id,
            edit_message_id,
            reply_markup=markup,
        )


# =========================
# Callbacks
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if data == "back":
        show_main_menu(call.message.chat.id, user_id, call.message.message_id)
        return

    if data == "support":
        bot.edit_message_text(
            "<b>📞 پشتیبانی</b>\n\n"
            f"🆔 آیدی شما: <code>{user_id}</code>\n\n"
            "برای فعال‌سازی حساب، این آیدی را برای مدیر ارسال کنید.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 بازگشت", callback_data="back")
            ),
        )
        return

    if data == "profile":
        show_profile(call)
        return

    if data == "stats":
        show_stats(call)
        return

    if data == "reports":
        show_reports(call)
        return

    if data == "settings":
        show_settings(call)
        return

    if data == "help":
        show_help(call)
        return

    if data == "admin":
        if is_admin(user_id):
            show_admin_panel(
                call.message.chat.id,
                user_id,
                call.message.message_id,
            )
        return

    if data.startswith("admin_"):
        handle_admin_callback(call)
        return


def show_profile(call):
    user = load_users().get(str(call.from_user.id), {})
    status = "فعال ✅" if has_access(call.from_user.id) else "غیرفعال ⛔"

    text = (
        "<b>👤 حساب کاربری</b>\n\n"
        f"نام: {safe_text(user.get('first_name', 'کاربر'), 100)}\n"
        f"یوزرنیم: @{safe_text(user.get('username', 'ندارد'), 100)}\n"
        f"آیدی: <code>{call.from_user.id}</code>\n"
        f"وضعیت: {status}\n"
        f"تعداد فعالیت: {user.get('total_actions', 0)}\n"
        f"تعداد گزارش: {user.get('total_reports', 0)}"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 بازگشت", callback_data="back")
        ),
    )


def show_stats(call):
    user = load_users().get(str(call.from_user.id), {})

    text = (
        "<b>📊 آمار شما</b>\n\n"
        f"فعالیت‌ها: {user.get('total_actions', 0)}\n"
        f"گزارش‌ها: {user.get('total_reports', 0)}"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 بازگشت", callback_data="back")
        ),
    )


def show_reports(call):
    reports = load_reports()
    user_id = str(call.from_user.id)

    own = [
        report for report in reports.values()
        if str(report.get("user_id")) == user_id
    ]

    if not own:
        text = "<b>📋 گزارش‌ها</b>\n\nهنوز گزارشی ثبت نشده است."
    else:
        lines = ["<b>📋 آخرین گزارش‌ها</b>\n"]
        for report in own[-10:]:
            lines.append(
                f"• {safe_text(report.get('title', 'بدون عنوان'), 80)}"
            )
        text = "\n".join(lines)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 بازگشت", callback_data="back")
        ),
    )


def show_settings(call):
    user_id = str(call.from_user.id)
    users = load_users()
    user = users.get(user_id, {})
    prefs = user.setdefault("preferences", {"language": "fa", "notifications": True})

    text = (
        "<b>⚙️ تنظیمات</b>\n\n"
        f"🌐 زبان: {prefs.get('language', 'fa')}\n"
        f"🔔 اعلان‌ها: {'فعال' if prefs.get('notifications', True) else 'غیرفعال'}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔔 تغییر اعلان‌ها",
            callback_data="toggle_notifications",
        )
    )
    markup.add(
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="back")
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
    )


def show_help(call):
    text = (
        "<b>❓ راهنما</b>\n\n"
        "/start — پنل اصلی\n"
        "/admin — پنل مدیریت\n\n"
        "این نسخه برای پایداری Railway و مدیریت امن ربات طراحی شده است."
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 بازگشت", callback_data="back")
        ),
    )


# =========================
# User settings
# =========================

@bot.callback_query_handler(func=lambda call: call.data == "toggle_notifications")
def toggle_notifications(call):
    user_id = str(call.from_user.id)
    users = load_users()

    if user_id not in users:
        ensure_user(call.from_user)
        users = load_users()

    prefs = users[user_id].setdefault(
        "preferences",
        {"language": "fa", "notifications": True},
    )
    prefs["notifications"] = not prefs.get("notifications", True)

    save_users(users)
    show_settings(call)


# =========================
# Admin actions
# =========================

def handle_admin_callback(call):
    if not is_admin(call.from_user.id):
        return

    data = call.data

    if data == "admin_users":
        users = load_users()
        lines = ["<b>👥 کاربران</b>\n"]

        for uid, user in list(users.items())[-30:]:
            status = "✅" if user.get("has_subscription") else "⛔"
            name = safe_text(user.get("first_name", "کاربر"), 40)
            lines.append(f"{status} {name} — <code>{uid}</code>")

        bot.edit_message_text(
            "\n".join(lines),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 مدیریت", callback_data="admin")
            ),
        )
        return

    if data == "admin_subscription":
        bot.edit_message_text(
            "<b>🎫 مدیریت اشتراک</b>\n\n"
            "برای فعال/غیرفعال کردن اشتراک یک کاربر، از این فرمت استفاده کنید:\n\n"
            "<code>/subscription USER_ID on</code>\n"
            "<code>/subscription USER_ID off</code>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 مدیریت", callback_data="admin")
            ),
        )
        return

    if data == "admin_stats":
        users = load_users()
        reports = load_reports()

        total_actions = sum(
            user.get("total_actions", 0) for user in users.values()
        )

        text = (
            "<b>📊 آمار کلی</b>\n\n"
            f"کاربران: {len(users)}\n"
            f"گزارش‌ها: {len(reports)}\n"
            f"فعالیت‌ها: {total_actions}"
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 مدیریت", callback_data="admin")
            ),
        )
        return

    if data == "admin_reports":
        reports = load_reports()

        if not reports:
            text = "<b>📋 گزارش‌ها</b>\n\nگزارشی وجود ندارد."
        else:
            lines = ["<b>📋 آخرین گزارش‌ها</b>\n"]
            for report in list(reports.values())[-20:]:
                lines.append(
                    f"• {safe_text(report.get('title', 'بدون عنوان'), 80)}"
                    f" — {report.get('created_at', '')}"
                )
            text = "\n".join(lines)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 مدیریت", callback_data="admin")
            ),
        )
        return

    if data == "admin_blacklist":
        blacklist = load_blacklist()

        if not blacklist:
            text = "<b>🚫 لیست سیاه</b>\n\nخالی است."
        else:
            lines = ["<b>🚫 لیست سیاه</b>\n"]
            for uid in blacklist:
                lines.append(f"• <code>{uid}</code>")
            text = "\n".join(lines)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 مدیریت", callback_data="admin")
            ),
        )


@bot.message_handler(commands=["subscription"])
def subscription_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return

    parts = message.text.split()

    if len(parts) != 3 or parts[2].lower() not in {"on", "off"}:
        bot.reply_to(
            message,
            "فرمت صحیح:\n"
            "<code>/subscription USER_ID on</code>\n"
            "<code>/subscription USER_ID off</code>",
        )
        return

    target_id = parts[1]

    if not target_id.isdigit():
        bot.reply_to(message, "❌ USER_ID باید عدد باشد.")
        return

    users = load_users()
    if target_id not in users:
        users[target_id] = {
            "username": "",
            "first_name": "کاربر",
            "join_date": now_iso(),
            "last_activity": now_iso(),
            "has_subscription": False,
            "total_actions": 0,
            "total_reports": 0,
            "preferences": {
                "language": "fa",
                "notifications": True,
            },
        }

    users[target_id]["has_subscription"] = parts[2].lower() == "on"
    save_users(users)

    status = "فعال ✅" if users[target_id]["has_subscription"] else "غیرفعال ⛔"

    bot.reply_to(
        message,
        f"اشتراک <code>{target_id}</code>: {status}",
    )


@bot.message_handler(commands=["health"])
def health_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return

    bot.reply_to(
        message,
        "<b>🟢 Bot health</b>\n\n"
        f"Python process: OK\n"
        f"Proxy helper: {'available' if apply_random_proxy else 'unavailable'}\n"
        f"Updater: {'available' if run_forever else 'unavailable'}",
    )


# =========================
# Safe action/report registration
# =========================

@bot.message_handler(commands=["report"])
def report_command(message):
    if not has_access(message.from_user.id):
        bot.reply_to(message, "⛔ حساب شما فعال نیست.")
        return

    text = message.text.partition(" ")[2].strip()

    if not text:
        bot.reply_to(
            message,
            "فرمت:\n<code>/report عنوان گزارش</code>",
        )
        return

    users = load_users()
    reports = load_reports()
    user_id = str(message.from_user.id)

    report_id = f"{int(time.time())}_{user_id}"
    reports[report_id] = {
        "user_id": user_id,
        "title": safe_text(text, 200),
        "created_at": now_iso(),
        "status": "created",
    }

    users[user_id]["total_actions"] = users[user_id].get("total_actions", 0) + 1
    users[user_id]["total_reports"] = users[user_id].get("total_reports", 0) + 1

    save_reports(reports)
    save_users(users)

    bot.reply_to(
        message,
        "✅ گزارش شما در سیستم ثبت شد.\n"
        f"شناسه: <code>{report_id}</code>",
    )


# =========================
# Optional proxy updater
# =========================

def start_optional_updater():
    if run_forever is None:
        logger.info("proxy_updater.py not available; continuing without updater")
        return

    try:
        thread = threading.Thread(
            target=run_forever,
            name="proxy-updater",
            daemon=True,
        )
        thread.start()
        logger.info("Proxy updater started")
    except Exception:
        logger.exception("Could not start proxy updater")


def apply_optional_proxy():
    if apply_random_proxy is None:
        logger.info("proxy_loader.py not available; using direct Telegram connection")
        return

    try:
        result = apply_random_proxy()
        logger.info("Proxy setup result: %s", result)
    except Exception:
        logger.exception("Proxy setup failed; using current Telegram connection")


# =========================
# Main
# =========================

def run_bot():
    start_optional_updater()

    # Do not block startup for a fixed 10 seconds.
    # The updater runs independently.
    apply_optional_proxy()

    logger.info("Bot starting")
    logger.info("Admin ID: %s", ADMIN_ID)

    # Remove an old webhook so polling can start cleanly.
    try:
        bot.delete_webhook(drop_pending_updates=False)
        logger.info("Webhook cleared")
    except Exception:
        logger.exception("Could not clear webhook")

    # One polling loop only. Railway should run one replica for this bot token.
    while True:
        try:
            logger.info("Starting Telegram polling")
            bot.infinity_polling(
                timeout=POLL_TIMEOUT,
                long_polling_timeout=POLL_TIMEOUT,
                skip_pending=False,
                allowed_updates=["message", "callback_query"],
            )
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            break
        except Exception:
            logger.exception("Telegram polling stopped; retrying in 10 seconds")
            time.sleep(10)


if __name__ == "__main__":
    run_bot()
