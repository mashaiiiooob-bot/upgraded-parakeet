import telebot
from telebot import types
import json
import os
import time
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re
import threading
import random
import imaplib
import hashlib
import base64
import uuid
import requests
import math
import statistics
import collections
import itertools
import functools
import operator
import string
import textwrap
import difflib
import heapq
import bisect
import array
import struct
import pickle
import shelve
import csv
import xml.etree.ElementTree as ET
import html
import urllib.parse
import urllib.request
import urllib.error
import http.client
import socket
import subprocess
import sys
import platform
import logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("telegram-bot")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")

ADMIN_ID = 7587661627


bot = telebot.TeleBot(BOT_TOKEN)

# ============ دیتابیس‌های اصلی ============
USERS_FILE = "email_users.json"
EMAILS_FILE = "email_accounts.json"
TEMP_FILE = "email_temp.json"
REPORTS_FILE = "email_reports.json"
BLACKLIST_FILE = "email_blacklist.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_emails():
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_emails(data):
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_temp():
    if os.path.exists(TEMP_FILE):
        with open(TEMP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_temp(data):
    with open(TEMP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_reports():
    if os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_reports(data):
    with open(REPORTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_blacklist(data):
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ============ ایموجی‌های پرمیوم ============
EMOJIS = {
    "رادار": "5319091153830688459",
    "جام": "5474546992598264488",
    "سگ": "5255975823436973213",
    "اکسیر": "5395624997144255311",
    "چشم": "4924695675817428819",
    "سکه": "4927246675937855288",
    "سکه۲": "4924687042933164139",
    "کیف": "4927248857781241629",
    "گزارش": "4924844148541884632",
    "گنج": "4927224535381444576",
    "آژیر": "4924878495395350442",
    "متن": "4925167954716264711",
    "خطر": "4925196417464537381",
    "پذیرش": "4927434232864704273",
    "نپذیرفتن": "4926947595890198959",
    "مستهجن": "4927258134910601155",
    "خشونت": "5260707404223378352",
    "کودک": "5987584714460893789",
    "فحاشی": "5803449618121364579",
    "چشم۲": "6019434284962552470",
    "سیگار": "6051104398845680693",
    "خطا": "5303059389534466718"
}

# ============ ایمیل‌های پیشفرض ============
DEFAULT_EMAILS = [
    "abuse@telegram.org",
    "recover@telegram.org",
    "dmca@telegram.org",
    "security@telegram.org",
    "spam@telegram.org"
]

# ============ تابع بررسی اشتراک ============
def has_access(user_id):
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str == str(ADMIN_ID):
        return True
    if user_id_str in users:
        return users[user_id_str].get("has_subscription", False)
    return False

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def log_to_admin(message):
    try:
        bot.send_message(ADMIN_ID, message)
    except:
        pass

# ============ استارت ============
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "ندارد"
    first_name = message.from_user.first_name or "کاربر"
    
    users = load_users()
    
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "first_name": first_name,
            "join_date": str(datetime.now()),
            "has_subscription": False,
            "total_sent": 0,
            "total_failed": 0,
            "total_reports": 0,
            "last_activity": str(datetime.now()),
            "preferences": {
                "language": "fa",
                "timezone": "Asia/Tehran",
                "notifications": True
            }
        }
        save_users(users)
        log_to_admin(f"📥 کاربر جدید: {first_name} (@{username}) - آیدی: {user_id}")
    
    if has_access(int(user_id)):
        user_panel(message)
    else:
        no_access_panel(message)

# ============ پنل بدون دسترسی ============
def no_access_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_contact = types.InlineKeyboardButton(
        text="📞 تماس با پشتیبانی",
        callback_data="contact_support",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_contact)
    
    text = (
        "<b>⛔ دسترسی محدود!</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["خطر"]}">⚠️</tg-emoji> <b>شما به این ربات دسترسی ندارید!</b>\n\n'
        "<blockquote>"
        "برای استفاده از این ربات، نیاز به <b>اشتراک ویژه</b> دارید.\n"
        "لطفاً با پشتیبانی تماس بگیرید.\n"
        "</blockquote>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>آیدی شما:</b> <code>{message.from_user.id}</code>'
    )
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# ============ پنل کاربر ============
def user_panel(message):
    user_id = str(message.from_user.id)
    users = load_users()
    user_data = users.get(user_id, {})
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_attack = types.InlineKeyboardButton(
        text="🎯 حمله به مقصد",
        callback_data="attack_menu",
        style="danger",
        icon_custom_emoji_id=EMOJIS["آژیر"]
    )
    
    btn_profile = types.InlineKeyboardButton(
        text="👤 حساب کاربری",
        callback_data="user_profile",
        style="primary",
        icon_custom_emoji_id=EMOJIS["کیف"]
    )
    
    btn_help = types.InlineKeyboardButton(
        text="❓ راهنما",
        callback_data="user_help",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    btn_reports = types.InlineKeyboardButton(
        text="📊 گزارشات من",
        callback_data="user_reports",
        style="primary",
        icon_custom_emoji_id=EMOJIS["گزارش"]
    )
    
    btn_stats = types.InlineKeyboardButton(
        text="📈 آمار من",
        callback_data="user_stats",
        style="primary",
        icon_custom_emoji_id=EMOJIS["سکه"]
    )
    
    btn_settings = types.InlineKeyboardButton(
        text="⚙️ تنظیمات",
        callback_data="user_settings",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم۲"]
    )
    
    markup.add(btn_attack, btn_profile)
    markup.add(btn_help, btn_reports)
    markup.add(btn_stats, btn_settings)
    
    text = (
        f"<b>🌀 ربات ایمیل سندر</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>کاربر:</b> {user_data.get("first_name", "کاربر")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["جام"]}">🏆</tg-emoji> <b>وضعیت:</b> فعال ✅\n'
        f'<tg-emoji emoji-id="{EMOJIS["سکه"]}">🪙</tg-emoji> <b>ارسال شده:</b> {user_data.get("total_sent", 0)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">❌</tg-emoji> <b>ناموفق:</b> {user_data.get("total_failed", 0)}\n\n'
        "<blockquote>"
        "🎯 برای شروع حمله، روی دکمه <b>حمله به مقصد</b> کلیک کنید.\n"
        "📧 ایمیل‌ها به صورت گروهی ارسال می‌شوند."
        "</blockquote>"
    )
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# ============ پنل مدیریت ============
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ شما دسترسی ندارید!")
        return
    
    users = load_users()
    emails = load_emails()
    reports = load_reports()
    blacklist = load_blacklist()
    
    total_users = len(users)
    total_emails = len(emails)
    total_reports = len(reports)
    active_emails = len([e for e in emails.values() if e.get("status") == "active"])
    total_blacklisted = len(blacklist)
    total_sent = sum(u.get("total_sent", 0) for u in users.values())
    total_failed = sum(u.get("total_failed", 0) for u in users.values())
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_add_email = types.InlineKeyboardButton(
        text="📧 افزودن ایمیل",
        callback_data="admin_add_email",
        style="success",
        icon_custom_emoji_id=EMOJIS["پذیرش"]
    )
    
    btn_subscription = types.InlineKeyboardButton(
        text="🎁 مدیریت اشتراک",
        callback_data="admin_subscription",
        style="primary",
        icon_custom_emoji_id=EMOJIS["گنج"]
    )
    
    btn_emails_list = types.InlineKeyboardButton(
        text="📋 لیست ایمیل‌ها",
        callback_data="admin_emails_list",
        style="primary",
        icon_custom_emoji_id=EMOJIS["گزارش"]
    )
    
    btn_users_list = types.InlineKeyboardButton(
        text="👥 لیست کاربران",
        callback_data="admin_users_list",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    btn_reports = types.InlineKeyboardButton(
        text="📊 گزارشات",
        callback_data="admin_reports",
        style="primary",
        icon_custom_emoji_id=EMOJIS["متن"]
    )
    
    btn_stats = types.InlineKeyboardButton(
        text="📊 آمار کامل",
        callback_data="admin_stats",
        style="primary",
        icon_custom_emoji_id=EMOJIS["سکه"]
    )
    
    btn_check_emails = types.InlineKeyboardButton(
        text="🔍 بررسی سلامت ایمیل‌ها",
        callback_data="admin_check_emails",
        style="danger",
        icon_custom_emoji_id=EMOJIS["رادار"]
    )
    
    btn_broadcast = types.InlineKeyboardButton(
        text="📢 ارسال همگانی",
        callback_data="admin_broadcast",
        style="success",
        icon_custom_emoji_id=EMOJIS["آژیر"]
    )
    
    btn_delete_email = types.InlineKeyboardButton(
        text="🗑️ حذف ایمیل",
        callback_data="admin_delete_email",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    
    btn_clear_reports = types.InlineKeyboardButton(
        text="🧹 پاک کردن گزارشات",
        callback_data="admin_clear_reports",
        style="danger",
        icon_custom_emoji_id=EMOJIS["خطا"]
    )
    
    btn_blacklist = types.InlineKeyboardButton(
        text="🚫 لیست سیاه",
        callback_data="admin_blacklist",
        style="danger",
        icon_custom_emoji_id=EMOJIS["خطر"]
    )
    
    btn_add_blacklist = types.InlineKeyboardButton(
        text="➕ افزودن به لیست سیاه",
        callback_data="admin_add_blacklist",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    
    btn_reset = types.InlineKeyboardButton(
        text="🔄 ریست دیتابیس",
        callback_data="admin_reset",
        style="danger",
        icon_custom_emoji_id=EMOJIS["خطا"]
    )
    
    btn_export = types.InlineKeyboardButton(
        text="📤 خروجی دیتابیس",
        callback_data="admin_export",
        style="success",
        icon_custom_emoji_id=EMOJIS["گنج"]
    )
    
    markup.add(btn_add_email, btn_subscription)
    markup.add(btn_emails_list, btn_users_list)
    markup.add(btn_reports, btn_stats)
    markup.add(btn_check_emails, btn_broadcast)
    markup.add(btn_delete_email, btn_clear_reports)
    markup.add(btn_blacklist, btn_add_blacklist)
    markup.add(btn_reset, btn_export)
    
    text = (
        "<b>👑 پنل مدیریت</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>کل کاربران:</b> {total_users}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌های ثبت شده:</b> {total_emails}\n'
        f'<tg-emoji emoji-id="{EMOJIS["پذیرش"]}">✅</tg-emoji> <b>ایمیل‌های فعال:</b> {active_emails}\n'
        f'<tg-emoji emoji-id="{EMOJIS["متن"]}">📝</tg-emoji> <b>کل گزارشات:</b> {total_reports}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گنج"]}">💰</tg-emoji> <b>کل ارسال:</b> {total_sent}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">❌</tg-emoji> <b>کل ناموفق:</b> {total_failed}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">🚫</tg-emoji> <b>لیست سیاه:</b> {total_blacklisted}\n\n'
        "<blockquote>مدیریت کامل ربات ایمیل سندر</blockquote>"
    )
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# ============ ارسال ایمیل با Gmail SMTP ============
def send_single_email(sender_email, password, target_email, subject, description):
    """
    ارسال مستقیم از حساب Gmail با SMTP.
    password باید App Password همان حساب Gmail باشد، نه رمز عادی حساب.
    """

    clean_desc = description.replace("\n", "<br>").replace("\r", "")
    html_body = f"""<html><body style="font-family:Arial,sans-serif;direction:rtl;">
    <div style="max-width:600px;margin:0 auto;padding:20px;border:1px solid #e0e0e0;border-radius:10px;">
    <h2 style="color:#333;">{subject}</h2>
    <div style="background-color:#f9f9f9;padding:15px;border-radius:8px;margin:15px 0;">
    {clean_desc}
    </div></div></body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = subject

        # نسخه متنی ساده
        plain_body = re.sub(r"<br\\s*/?>", "\n", description, flags=re.IGNORECASE)
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Gmail SMTP over SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, [target_email], msg.as_string())

        return True

    except Exception as e:
        log_to_admin(f"❌ خطا در ارسال SMTP از {sender_email}: {str(e)}")
        return False

# ============ بررسی سلامت حساب Gmail ============
def check_email_validity(email, password):
    """
    بررسی ورود به Gmail.
    برای Gmail از App Password استفاده شود.
    """
    # ابتدا SMTP را بررسی می‌کنیم چون ارسال ربات هم از همین مسیر انجام می‌شود.
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=15) as server:
            server.login(email, password)
        return True
    except Exception:
        pass

    # fallback: STARTTLS روی پورت 587
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(email, password)
        return True
    except Exception:
        return False

# ============ تابع ارسال همگانی گزارشات ============
def send_emails(chat_id, progress_msg_id, target, emails, count, user_id, subject, description):
    all_emails = load_emails()
    sent = 0
    failed = 0
    total = len(emails) * count
    
    reports = load_reports()
    report_id = f"{int(time.time())}_{user_id}"
    reports[report_id] = {
        "user_id": user_id,
        "target": target,
        "emails_used": emails,
        "count_per_email": count,
        "total": total,
        "sent": 0,
        "failed": 0,
        "start_time": str(datetime.now()),
        "status": "running",
        "subject": subject,
        "description": description
    }
    save_reports(reports)
    
    clean_subject = subject.replace('\n', ' ').replace('\r', '')
    clean_description = description.replace('\n', '<br>').replace('\r', '')
    
    for email in emails:
        if email not in all_emails:
            continue
        
        email_data = all_emails[email]
        
        for i in range(count):
            try:
                if send_single_email(email, email_data["password"], target, clean_subject, clean_description):
                    sent += 1
                    all_emails[email]["sent_count"] = all_emails[email].get("sent_count", 0) + 1
                    
                    # به‌روزرسانی آمار کاربر
                    users = load_users()
                    if user_id in users:
                        users[user_id]["total_sent"] = users[user_id].get("total_sent", 0) + 1
                        save_users(users)
                    
                    progress = int((sent / total) * 100) if total > 0 else 0
                    update_progress(chat_id, progress_msg_id, sent, total, failed, target, email, progress)
                else:
                    failed += 1
                    users = load_users()
                    if user_id in users:
                        users[user_id]["total_failed"] = users[user_id].get("total_failed", 0) + 1
                        save_users(users)
            except Exception as e:
                failed += 1
                log_to_admin(f"❌ خطا در ارسال ایمیل از {email}: {str(e)}")
                users = load_users()
                if user_id in users:
                    users[user_id]["total_failed"] = users[user_id].get("total_failed", 0) + 1
                    save_users(users)
            
            time.sleep(random.uniform(2, 5))
        
        save_emails(all_emails)
    
    reports[report_id]["sent"] = sent
    reports[report_id]["failed"] = failed
    reports[report_id]["status"] = "completed"
    reports[report_id]["end_time"] = str(datetime.now())
    save_reports(reports)
    
    temp = load_temp()
    if user_id in temp:
        del temp[user_id]
        save_temp(temp)
    
    final_text = (
        f"<b>✅ حمله کامل شد!</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["جام"]}">🏆</tg-emoji> <b>مقصد:</b> {target}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ارسال شده:</b> {sent}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">❌</tg-emoji> <b>ناموفق:</b> {failed}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گنج"]}">💰</tg-emoji> <b>کل:</b> {total}\n\n'
        f'<b>📝 موضوع:</b> {subject}\n\n'
        "<blockquote>"
        "🎯 حمله با موفقیت انجام شد!\n"
        "📊 برای مشاهده جزئیات به گزارشات مراجعه کنید."
        "</blockquote>"
    )
    
    bot.edit_message_text(
        final_text,
        chat_id,
        progress_msg_id,
        parse_mode="HTML"
    )

# ============ به‌روزرسانی پیشرفت ============
def update_progress(chat_id, msg_id, sent, total, failed, target, current_email, progress):
    progress_bar = "█" * (progress // 2) + "░" * (50 - (progress // 2))
    
    text = (
        f"<b>🚀 حمله در حال اجرا...</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["آژیر"]}">🚨</tg-emoji> <b>مقصد:</b> {target}\n'
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>پیشرفت:</b> {progress}%\n'
        f"<code>{progress_bar}</code>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ارسال شده:</b> {sent}/{total}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">❌</tg-emoji> <b>ناموفق:</b> {failed}\n'
        f'<tg-emoji emoji-id="{EMOJIS["سکه"]}">🪙</tg-emoji> <b>ایمیل فعلی:</b> {current_email}\n\n'
        "<blockquote>⏳ لطفاً صبر کنید...</blockquote>"
    )
    
    try:
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML")
    except:
        pass

# ============ افزودن ایمیل ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_email")
def admin_add_email(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="admin_back",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>📧 افزودن ایمیل</b>\n\n"
        "لطفاً به این فرمت ارسال کن:\n"
        "<code>ایمیل:آپ‌پسوورد</code>\n\n"
        "مثال:\n"
        "<code>example@gmail.com:abcd1234efgh</code>\n\n"
        "⚠️ برای افزودن چند ایمیل، هر کدوم رو در خط جدید بفرست.\n"
        "🔍 ایمیل‌ها به صورت خودکار بررسی می‌شوند."
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_add_emails)

def process_add_emails(message):
    if not is_admin(message.from_user.id):
        return
    
    lines = message.text.strip().split('\n')
    emails = load_emails()
    blacklist = load_blacklist()
    added = 0
    failed = []
    verified = []
    blacklisted = []
    
    progress_msg = bot.reply_to(message, "<b>🔍 در حال بررسی ایمیل‌ها...</b>", parse_mode="HTML")
    
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            email = parts[0].strip()
            password = parts[1].strip()
            
            if email and password:
                if email in blacklist:
                    blacklisted.append(email)
                    failed.append(f"{email} (در لیست سیاه)")
                    continue
                
                is_valid = check_email_validity(email, password)
                
                if is_valid:
                    if email not in emails:
                        emails[email] = {
                            "password": password,
                            "added_date": str(datetime.now()),
                            "status": "active",
                            "sent_count": 0,
                            "verified": True,
                            "last_used": None,
                            "total_sent": 0,
                            "total_failed": 0
                        }
                        added += 1
                        verified.append(email)
                    else:
                        failed.append(f"{email} (تکراری)")
                else:
                    failed.append(f"{email} (نامعتبر/پسوورد اشتباه)")
            else:
                failed.append(f"{line} (فرمت نامعتبر)")
        else:
            failed.append(f"{line} (فرمت نامعتبر)")
    
    save_emails(emails)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    result_text = (
        f"<b>✅ نتیجه افزودن ایمیل‌ها</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["پذیرش"]}">✅</tg-emoji> <b>افزوده شد:</b> {added}\n'
        f'<tg-emoji emoji-id="{EMOJIS["رادار"]}">📡</tg-emoji> <b>تأیید شده:</b> {len(verified)}\n'
    )
    
    if blacklisted:
        result_text += f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">🚫</tg-emoji> <b>در لیست سیاه:</b> {len(blacklisted)}\n'
    
    if failed:
        result_text += f'<tg-emoji emoji-id="{EMOJIS["نپذیرفتن"]}">❌</tg-emoji> <b>ناموفق:</b> {len(failed)}\n'
        result_text += f"<b>جزئیات:</b>\n" + "\n".join(failed[:10])
    
    bot.edit_message_text(
        result_text,
        progress_msg.chat.id,
        progress_msg.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ بررسی سلامت همه ایمیل‌ها ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_check_emails")
def admin_check_emails(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    emails = load_emails()
    
    if not emails:
        bot.answer_callback_query(call.id, "❌ هیچ ایمیلی ثبت نشده!")
        return
    
    progress_msg = bot.edit_message_text(
        "<b>🔍 در حال بررسی سلامت ایمیل‌ها...</b>\n\n⏳ لطفاً صبر کنید...",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )
    
    valid = 0
    invalid = 0
    invalid_list = []
    
    for email, data in emails.items():
        is_valid = check_email_validity(email, data["password"])
        if is_valid:
            data["status"] = "active"
            data["verified"] = True
            valid += 1
        else:
            data["status"] = "inactive"
            data["verified"] = False
            invalid += 1
            invalid_list.append(email)
        time.sleep(0.5)
    
    save_emails(emails)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    text = (
        f"<b>✅ بررسی سلامت کامل شد!</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["پذیرش"]}">✅</tg-emoji> <b>ایمیل‌های سالم:</b> {valid}\n'
        f'<tg-emoji emoji-id="{EMOJIS["نپذیرفتن"]}">❌</tg-emoji> <b>ایمیل‌های نامعتبر:</b> {invalid}\n'
    )
    
    if invalid_list:
        text += f"\n<b>📋 لیست ایمیل‌های نامعتبر:</b>\n" + "\n".join(invalid_list[:10])
    
    bot.edit_message_text(
        text,
        progress_msg.chat.id,
        progress_msg.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ مدیریت اشتراک ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_subscription")
def admin_subscription(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    users = load_users()
    subscribed = len([u for u in users.values() if u.get("has_subscription", False)])
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_add = types.InlineKeyboardButton(
        text="➕ اعطای اشتراک",
        callback_data="admin_add_subscription",
        style="success",
        icon_custom_emoji_id=EMOJIS["پذیرش"]
    )
    
    btn_remove = types.InlineKeyboardButton(
        text="➖ لغو اشتراک",
        callback_data="admin_remove_subscription",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    
    btn_list = types.InlineKeyboardButton(
        text="📋 لیست اشتراک‌ها",
        callback_data="admin_subscription_list",
        style="primary",
        icon_custom_emoji_id=EMOJIS["گزارش"]
    )
    
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    markup.add(btn_add, btn_remove)
    markup.add(btn_list, btn_back)
    
    text = (
        "<b>🎁 مدیریت اشتراک</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>کل کاربران:</b> {len(users)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["جام"]}">🏆</tg-emoji> <b>دارای اشتراک:</b> {subscribed}\n\n'
        "<blockquote>"
        "🔹 اعطای اشتراک: دسترسی به ربات\n"
        "🔹 لغو اشتراک: قطع دسترسی\n"
        "</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_subscription")
def admin_add_subscription(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="admin_subscription",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>➕ اعطای اشتراک</b>\n\n"
        "لطفاً <b>آیدی عددی</b> کاربر را ارسال کن:\n\n"
        "مثال:\n"
        "<code>123456789</code>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_add_subscription)

def process_add_subscription(message):
    if not is_admin(message.from_user.id):
        return
    
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.reply_to(message, "❌ آیدی نامعتبر! لطفاً یک عدد ارسال کن.")
        return
    
    users = load_users()
    
    if user_id not in users:
        users[user_id] = {
            "username": "نامشخص",
            "first_name": "کاربر جدید",
            "join_date": str(datetime.now()),
            "has_subscription": False,
            "total_sent": 0,
            "total_failed": 0,
            "total_reports": 0,
            "last_activity": str(datetime.now()),
            "preferences": {
                "language": "fa",
                "timezone": "Asia/Tehran",
                "notifications": True
            }
        }
    
    users[user_id]["has_subscription"] = True
    save_users(users)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_subscription",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.reply_to(message, f"✅ اشتراک به کاربر {user_id} اعطا شد!", parse_mode="HTML", reply_markup=markup)
    
    try:
        bot.send_message(
            int(user_id),
            f"<b>🎉 تبریک!</b>\n\n"
            f'<tg-emoji emoji-id="{EMOJIS["جام"]}">🏆</tg-emoji> <b>اشتراک شما فعال شد!</b>\n\n'
            "<blockquote>اکنون می‌توانید از تمام امکانات ربات استفاده کنید.</blockquote>",
            parse_mode="HTML"
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_subscription")
def admin_remove_subscription(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="admin_subscription",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>➖ لغو اشتراک</b>\n\n"
        "لطفاً <b>آیدی عددی</b> کاربر را ارسال کن:\n\n"
        "مثال:\n"
        "<code>123456789</code>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_remove_subscription)

def process_remove_subscription(message):
    if not is_admin(message.from_user.id):
        return
    
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.reply_to(message, "❌ آیدی نامعتبر!")
        return
    
    users = load_users()
    
    if user_id not in users:
        bot.reply_to(message, "❌ کاربر پیدا نشد!")
        return
    
    users[user_id]["has_subscription"] = False
    save_users(users)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_subscription",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.reply_to(message, f"✅ اشتراک کاربر {user_id} لغو شد!", parse_mode="HTML", reply_markup=markup)

# ============ لیست اشتراک‌ها ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_subscription_list")
def admin_subscription_list(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    users = load_users()
    subscribed = {uid: data for uid, data in users.items() if data.get("has_subscription", False)}
    
    if not subscribed:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_back = types.InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="admin_subscription",
            style="primary",
            icon_custom_emoji_id=EMOJIS["چشم"]
        )
        markup.add(btn_back)
        
        bot.edit_message_text(
            "<b>📋 هیچ کاربری اشتراک ندارد!</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        return
    
    text = "<b>📋 لیست کاربران دارای اشتراک:</b>\n\n"
    for uid, data in list(subscribed.items())[:20]:
        text += f"🆔 <code>{uid}</code> - {data.get('first_name', 'نامشخص')}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_subscription",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ لیست ایمیل‌ها ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_emails_list")
def admin_emails_list(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    emails = load_emails()
    
    if not emails:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_back = types.InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="admin_back",
            style="primary",
            icon_custom_emoji_id=EMOJIS["چشم"]
        )
        markup.add(btn_back)
        
        bot.edit_message_text(
            "<b>📋 هیچ ایمیلی ثبت نشده!</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        return
    
    text = "<b>📋 لیست ایمیل‌های ثبت شده:</b>\n\n"
    for email, data in list(emails.items())[:20]:
        status = "✅ فعال" if data.get("status") == "active" else "❌ غیرفعال"
        text += f"📧 {email}\n   وضعیت: {status}\n   ارسال: {data.get('sent_count', 0)}\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ لیست کاربران ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_users_list")
def admin_users_list(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    users = load_users()
    
    if not users:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_back = types.InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="admin_back",
            style="primary",
            icon_custom_emoji_id=EMOJIS["چشم"]
        )
        markup.add(btn_back)
        
        bot.edit_message_text(
            "<b>📋 هیچ کاربری ثبت نشده!</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        return
    
    text = "<b>👥 لیست کاربران:</b>\n\n"
    for uid, data in list(users.items())[:20]:
        status = "✅" if data.get("has_subscription", False) else "❌"
        text += f"🆔 <code>{uid}</code> - {data.get('first_name', 'نامشخص')} {status}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ گزارشات ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_reports")
def admin_reports(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    reports = load_reports()
    
    if not reports:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_back = types.InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="admin_back",
            style="primary",
            icon_custom_emoji_id=EMOJIS["چشم"]
        )
        markup.add(btn_back)
        
        bot.edit_message_text(
            "<b>📋 هیچ گزارشی وجود ندارد!</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        return
    
    text = "<b>📊 آخرین گزارشات:</b>\n\n"
    for rep_id, data in list(reports.items())[-10:]:
        status = "✅" if data.get("status") == "completed" else "⏳"
        text += f"🆔 {rep_id}\n   مقصد: {data.get('target', 'نامشخص')}\n   ارسال: {data.get('sent', 0)}/{data.get('total', 0)} {status}\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ آمار کامل ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    users = load_users()
    emails = load_emails()
    reports = load_reports()
    blacklist = load_blacklist()
    
    total_users = len(users)
    subscribed = len([u for u in users.values() if u.get("has_subscription", False)])
    total_emails = len(emails)
    active_emails = len([e for e in emails.values() if e.get("status") == "active"])
    total_reports = len(reports)
    total_sent = sum(r.get("sent", 0) for r in reports.values())
    total_failed = sum(r.get("failed", 0) for r in reports.values())
    total_blacklisted = len(blacklist)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    text = (
        "<b>📊 آمار کامل</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>کل کاربران:</b> {total_users}\n'
        f'<tg-emoji emoji-id="{EMOJIS["جام"]}">🏆</tg-emoji> <b>دارای اشتراک:</b> {subscribed}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌ها:</b> {total_emails} (فعال: {active_emails})\n'
        f'<tg-emoji emoji-id="{EMOJIS["متن"]}">📝</tg-emoji> <b>کل گزارشات:</b> {total_reports}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گنج"]}">💰</tg-emoji> <b>کل ارسال:</b> {total_sent}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">❌</tg-emoji> <b>کل ناموفق:</b> {total_failed}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">🚫</tg-emoji> <b>لیست سیاه:</b> {total_blacklisted}\n\n'
        "<blockquote>آمار کامل ربات</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ حذف ایمیل ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_delete_email")
def admin_delete_email(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="admin_back",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>🗑️ حذف ایمیل</b>\n\n"
        "لطفاً آدرس ایمیل مورد نظر برای حذف را وارد کنید:\n\n"
        "مثال:\n"
        "<code>example@gmail.com</code>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_delete_email)

def process_delete_email(message):
    if not is_admin(message.from_user.id):
        return
    
    email = message.text.strip()
    emails = load_emails()
    
    if email not in emails:
        bot.reply_to(message, "❌ ایمیل پیدا نشد!")
        return
    
    del emails[email]
    save_emails(emails)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.reply_to(message, f"✅ ایمیل {email} با موفقیت حذف شد!", parse_mode="HTML", reply_markup=markup)

# ============ پاک کردن گزارشات ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_clear_reports")
def admin_clear_reports(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    save_reports({})
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        "<b>🧹 تمام گزارشات پاک شدند!</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ لیست سیاه ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_blacklist")
def admin_blacklist(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    blacklist = load_blacklist()
    
    if not blacklist:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_back = types.InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="admin_back",
            style="primary",
            icon_custom_emoji_id=EMOJIS["چشم"]
        )
        markup.add(btn_back)
        
        bot.edit_message_text(
            "<b>📋 لیست سیاه خالی است!</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        return
    
    text = "<b>🚫 لیست سیاه:</b>\n\n"
    for email, data in list(blacklist.items())[:20]:
        text += f"📧 {email}\n   دلیل: {data.get('reason', 'نامشخص')}\n   تاریخ: {data.get('date', 'نامشخص')}\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ افزودن به لیست سیاه ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_blacklist")
def admin_add_blacklist(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="admin_back",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>🚫 افزودن به لیست سیاه</b>\n\n"
        "لطفاً آدرس ایمیل و دلیل را وارد کنید:\n"
        "<code>ایمیل:دلیل</code>\n\n"
        "مثال:\n"
        "<code>spam@gmail.com:ارسال اسپم</code>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_add_blacklist)

def process_add_blacklist(message):
    if not is_admin(message.from_user.id):
        return
    
    if ':' not in message.text:
        bot.reply_to(message, "❌ فرمت نامعتبر! فرمت: ایمیل:دلیل")
        return
    
    email, reason = message.text.split(':', 1)
    email = email.strip()
    reason = reason.strip()
    
    blacklist = load_blacklist()
    blacklist[email] = {
        "reason": reason,
        "date": str(datetime.now())
    }
    save_blacklist(blacklist)
    
    emails = load_emails()
    if email in emails:
        del emails[email]
        save_emails(emails)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.reply_to(
        message,
        f"✅ ایمیل {email} با موفقیت به لیست سیاه اضافه شد!\nدلیل: {reason}",
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ ریست دیتابیس ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_reset")
def admin_reset(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_confirm = types.InlineKeyboardButton(
        text="✅ تأیید ریست",
        callback_data="admin_reset_confirm",
        style="danger",
        icon_custom_emoji_id=EMOJIS["خطر"]
    )
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_confirm, btn_cancel)
    
    text = (
        "<b>⚠️ هشدار!</b>\n\n"
        "آیا از ریست کردن دیتابیس اطمینان دارید؟\n"
        "همه داده‌ها پاک خواهند شد!"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_reset_confirm")
def admin_reset_confirm(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    # پاک کردن همه دیتابیس‌ها
    files = [USERS_FILE, EMAILS_FILE, TEMP_FILE, REPORTS_FILE, BLACKLIST_FILE]
    for file in files:
        if os.path.exists(file):
            os.remove(file)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_back",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        "<b>✅ تمام دیتابیس‌ها با موفقیت ریست شدند!</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ خروجی دیتابیس ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_export")
def admin_export(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    data = {
        "users": load_users(),
        "emails": load_emails(),
        "reports": load_reports(),
        "blacklist": load_blacklist(),
        "export_date": str(datetime.now())
    }
    
    export_file = f"backup_{int(time.time())}.json"
    with open(export_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    with open(export_file, 'rb') as f:
        bot.send_document(
            call.message.chat.id,
            f,
            caption=f"<b>📤 خروجی دیتابیس</b>\n\n"
                   f'<tg-emoji emoji-id="{EMOJIS["گنج"]}">💰</tg-emoji> <b>تاریخ:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            parse_mode="HTML"
        )
    
    os.remove(export_file)
    bot.answer_callback_query(call.id, "✅ خروجی با موفقیت ارسال شد!")

# ============ ارسال همگانی ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="admin_back",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>📢 ارسال همگانی</b>\n\n"
        "لطفاً پیام خود را ارسال کن:\n\n"
        "⚠️ پیام به <b>همه کاربران</b> ارسال خواهد شد!\n"
        "💡 می‌توانی از <b>HTML</b> و <b>ایموجی پرمیوم</b> استفاده کنی."
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_broadcast)

def process_broadcast(message):
    if not is_admin(message.from_user.id):
        return
    
    broadcast_text = message.text or message.caption or ""
    
    if not broadcast_text:
        bot.reply_to(message, "❌ پیام خالی است!")
        return
    
    users = load_users()
    total_users = len(users)
    success = 0
    failed = 0
    
    progress_msg = bot.reply_to(message, f"<b>📢 در حال ارسال به {total_users} کاربر...</b>", parse_mode="HTML")
    
    for user_id in users.keys():
        try:
            bot.send_message(
                int(user_id),
                f"<b>📢 پیام همگانی</b>\n\n{broadcast_text}",
                parse_mode="HTML"
            )
            success += 1
            time.sleep(0.05)
        except:
            failed += 1
    
    result_text = (
        f"<b>✅ ارسال همگانی کامل شد!</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>کل کاربران:</b> {total_users}\n'
        f'<tg-emoji emoji-id="{EMOJIS["پذیرش"]}">✅</tg-emoji> <b>ارسال شد:</b> {success}\n'
        f'<tg-emoji emoji-id="{EMOJIS["نپذیرفتن"]}">❌</tg-emoji> <b>ناموفق:</b> {failed}'
    )
    
    bot.edit_message_text(result_text, progress_msg.chat.id, progress_msg.message_id, parse_mode="HTML")

# ============ منوی حمله ============
@bot.callback_query_handler(func=lambda call: call.data == "attack_menu")
def attack_menu(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    emails = load_emails()
    active_emails = [e for e in emails.values() if e.get("status") == "active"]
    
    if not active_emails:
        bot.answer_callback_query(
            call.id,
            "❌ هیچ ایمیل فعالی ثبت نشده است! با مدیریت تماس بگیرید.",
            show_alert=True
        )
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for email in DEFAULT_EMAILS:
        btn = types.InlineKeyboardButton(
            text=f"📧 {email}",
            callback_data=f"target_{email}",
            style="primary",
            icon_custom_emoji_id=EMOJIS["گزارش"]
        )
        markup.add(btn)
    
    btn_custom = types.InlineKeyboardButton(
        text="✏️ مقصد دلخواه",
        callback_data="target_custom",
        style="success",
        icon_custom_emoji_id=EMOJIS["متن"]
    )
    
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="back_to_panel",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    markup.add(btn_custom, btn_back)
    
    text = (
        "<b>🎯 انتخاب مقصد</b>\n\n"
        "لطفاً مقصد مورد نظر را انتخاب کنید:\n\n"
        "<blockquote>"
        "📧 <b>abuse@telegram.org</b> - گزارش تخلف\n"
        "📧 <b>recover@telegram.org</b> - بازیابی حساب\n"
        "📧 <b>dmca@telegram.org</b> - نقض کپی‌رایت\n"
        "📧 <b>security@telegram.org</b> - مشکلات امنیتی\n"
        "📧 <b>spam@telegram.org</b> - گزارش اسپم\n"
        "</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("target_"))
def select_target(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    target = call.data.replace("target_", "")
    
    temp = load_temp()
    temp[str(call.from_user.id)] = {"target": target}
    save_temp(temp)
    
    show_email_selection(call)

@bot.callback_query_handler(func=lambda call: call.data == "target_custom")
def target_custom(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="attack_menu",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>✏️ مقصد دلخواه</b>\n\n"
        "لطفاً آدرس ایمیل مقصد را وارد کنید:\n\n"
        "مثال:\n"
        "<code>example@gmail.com</code>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_custom_target)

def process_custom_target(message):
    if not has_access(message.from_user.id):
        return
    
    target = message.text.strip()
    
    if '@' not in target or '.' not in target:
        bot.reply_to(message, "❌ ایمیل نامعتبر! لطفاً دوباره تلاش کن.")
        return
    
    temp = load_temp()
    temp[str(message.from_user.id)] = {"target": target}
    save_temp(temp)
    
    show_email_selection_message(message)

def show_email_selection(call):
    emails = load_emails()
    active_emails = [email for email, data in emails.items() if data.get("status") == "active"]
    
    if not active_emails:
        bot.answer_callback_query(call.id, "❌ هیچ ایمیل فعالی وجود ندارد!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for i, email in enumerate(active_emails, 1):
        btn = types.InlineKeyboardButton(
            text=f"{i}. {email[:15]}...",
            callback_data=f"use_email_{i}",
            style="primary",
            icon_custom_emoji_id=EMOJIS["سکه"]
        )
        markup.add(btn)
    
    btn_all = types.InlineKeyboardButton(
        text="📧 همه ایمیل‌ها",
        callback_data="use_email_all",
        style="danger",
        icon_custom_emoji_id=EMOJIS["آژیر"]
    )
    
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="attack_menu",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    markup.add(btn_all, btn_back)
    
    temp = load_temp()
    temp[str(call.from_user.id)]["emails"] = active_emails
    save_temp(temp)
    
    text = (
        f"<b>📧 انتخاب ایمیل</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>مقصد:</b> {temp[str(call.from_user.id)].get("target", "نامشخص")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌های فعال:</b> {len(active_emails)}\n\n'
        "لطفاً با <b>شماره</b> ایمیل مورد نظر را انتخاب کنید:"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

def show_email_selection_message(message):
    emails = load_emails()
    active_emails = [email for email, data in emails.items() if data.get("status") == "active"]
    
    if not active_emails:
        bot.reply_to(message, "❌ هیچ ایمیل فعالی وجود ندارد!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for i, email in enumerate(active_emails, 1):
        btn = types.InlineKeyboardButton(
            text=f"{i}. {email[:15]}...",
            callback_data=f"use_email_{i}",
            style="primary",
            icon_custom_emoji_id=EMOJIS["سکه"]
        )
        markup.add(btn)
    
    btn_all = types.InlineKeyboardButton(
        text="📧 همه ایمیل‌ها",
        callback_data="use_email_all",
        style="danger",
        icon_custom_emoji_id=EMOJIS["آژیر"]
    )
    
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="attack_menu",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    markup.add(btn_all, btn_back)
    
    temp = load_temp()
    temp[str(message.from_user.id)]["emails"] = active_emails
    save_temp(temp)
    
    text = (
        f"<b>📧 انتخاب ایمیل</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>مقصد:</b> {temp[str(message.from_user.id)].get("target", "نامشخص")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌های فعال:</b> {len(active_emails)}\n\n'
        "لطفاً با <b>شماره</b> ایمیل مورد نظر را انتخاب کنید:"
    )
    
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_email_"))
def select_email(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    temp = load_temp()
    user_temp = temp.get(str(call.from_user.id), {})
    email_list = user_temp.get("emails", [])
    
    if call.data == "use_email_all":
        selected_emails = email_list
    else:
        index = int(call.data.replace("use_email_", "")) - 1
        if index >= len(email_list):
            bot.answer_callback_query(call.id, "❌ ایمیل پیدا نشد!")
            return
        selected_emails = [email_list[index]]
    
    user_temp["selected_emails"] = selected_emails
    save_temp(temp)
    
    ask_subject(call)

def ask_subject(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="attack_menu",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    temp = load_temp()
    user_temp = temp.get(str(call.from_user.id), {})
    
    text = (
        f"<b>✏️ موضوع ایمیل</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>مقصد:</b> {user_temp.get("target", "نامشخص")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌های انتخاب شده:</b> {len(user_temp.get("selected_emails", []))}\n\n'
        "لطفاً <b>موضوع</b> ایمیل را وارد کنید:"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_subject)

def process_subject(message):
    if not has_access(message.from_user.id):
        return
    
    subject = message.text.strip().replace('\n', ' ').replace('\r', '')
    
    if not subject:
        bot.reply_to(message, "❌ موضوع نمی‌تواند خالی باشد!")
        return
    
    temp = load_temp()
    temp[str(message.from_user.id)]["subject"] = subject
    save_temp(temp)
    
    ask_description(message)

def ask_description(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="attack_menu",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    temp = load_temp()
    user_temp = temp.get(str(message.from_user.id), {})
    
    text = (
        f"<b>✏️ توضیحات ایمیل</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>مقصد:</b> {user_temp.get("target", "نامشخص")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["متن"]}">📝</tg-emoji> <b>موضوع:</b> {user_temp.get("subject", "نامشخص")}\n\n'
        "لطفاً <b>توضیحات</b> ایمیل را وارد کنید:"
    )
    
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(message, process_description)

def process_description(message):
    if not has_access(message.from_user.id):
        return
    
    description = message.text.strip()
    
    if not description:
        bot.reply_to(message, "❌ توضیحات نمی‌تواند خالی باشد!")
        return
    
    temp = load_temp()
    temp[str(message.from_user.id)]["description"] = description
    save_temp(temp)
    
    ask_report_count_message(message)

def ask_report_count_message(message):
    temp = load_temp()
    user_temp = temp.get(str(message.from_user.id), {})
    selected_emails = user_temp.get("selected_emails", [])
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    for count in [5, 10, 15, 20, 25]:
        btn = types.InlineKeyboardButton(
            text=str(count),
            callback_data=f"report_count_{count}",
            style="primary",
            icon_custom_emoji_id=EMOJIS["سکه"]
        )
        markup.add(btn)
    
    btn_custom = types.InlineKeyboardButton(
        text="✏️ تعداد دلخواه",
        callback_data="report_count_custom",
        style="success",
        icon_custom_emoji_id=EMOJIS["متن"]
    )
    
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="attack_menu",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    markup.add(btn_custom, btn_back)
    
    text = (
        f"<b>📊 تعداد گزارش</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>مقصد:</b> {user_temp.get("target", "نامشخص")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌ها:</b> {len(selected_emails)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["متن"]}">📝</tg-emoji> <b>موضوع:</b> {user_temp.get("subject", "نامشخص")[:30]}...\n\n'
        "لطفاً تعداد گزارش برای هر ایمیل را انتخاب کنید:\n"
        "(حداکثر ۲۵ گزارش برای هر ایمیل)"
    )
    
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("report_count_"))
def set_report_count(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    count = int(call.data.replace("report_count_", ""))
    
    temp = load_temp()
    temp[str(call.from_user.id)]["count"] = count
    save_temp(temp)
    
    confirm_attack(call)

@bot.callback_query_handler(func=lambda call: call.data == "report_count_custom")
def report_count_custom(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="attack_menu",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    markup.add(btn_cancel)
    
    text = (
        "<b>✏️ تعداد دلخواه</b>\n\n"
        "لطفاً تعداد گزارش برای هر ایمیل را وارد کنید:\n"
        "(حداکثر ۲۵)"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(call.message, process_custom_count)

def process_custom_count(message):
    if not has_access(message.from_user.id):
        return
    
    try:
        count = int(message.text.strip())
        if count < 1 or count > 25:
            bot.reply_to(message, "❌ تعداد باید بین ۱ تا ۲۵ باشد!")
            return
        
        temp = load_temp()
        temp[str(message.from_user.id)]["count"] = count
        save_temp(temp)
        
        confirm_attack_message(message)
    except:
        bot.reply_to(message, "❌ لطفاً یک عدد معتبر وارد کنید!")

def confirm_attack(call):
    temp = load_temp()
    user_temp = temp.get(str(call.from_user.id), {})
    target = user_temp.get("target", "نامشخص")
    emails = user_temp.get("selected_emails", [])
    count = user_temp.get("count", 0)
    subject = user_temp.get("subject", "بدون موضوع")
    description = user_temp.get("description", "بدون توضیحات")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_start = types.InlineKeyboardButton(
        text="🚀 شروع حمله",
        callback_data="start_attack",
        style="danger",
        icon_custom_emoji_id=EMOJIS["آژیر"]
    )
    
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="attack_menu",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    
    markup.add(btn_start, btn_cancel)
    
    text = (
        "<b>🔥 تأیید نهایی</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>مقصد:</b> {target}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌ها:</b> {len(emails)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["متن"]}">📝</tg-emoji> <b>موضوع:</b> {subject[:50]}\n'
        f'<tg-emoji emoji-id="{EMOJIS["سکه"]}">🪙</tg-emoji> <b>تعداد هر ایمیل:</b> {count}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گنج"]}">💰</tg-emoji> <b>کل گزارشات:</b> {len(emails) * count}\n\n'
        f'<b>📝 توضیحات:</b>\n{description[:100]}...\n\n'
        "<blockquote>⚠️ با شروع، گزارش‌ها ارسال می‌شوند!</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

def confirm_attack_message(message):
    temp = load_temp()
    user_temp = temp.get(str(message.from_user.id), {})
    target = user_temp.get("target", "نامشخص")
    emails = user_temp.get("selected_emails", [])
    count = user_temp.get("count", 0)
    subject = user_temp.get("subject", "بدون موضوع")
    description = user_temp.get("description", "بدون توضیحات")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_start = types.InlineKeyboardButton(
        text="🚀 شروع حمله",
        callback_data="start_attack",
        style="danger",
        icon_custom_emoji_id=EMOJIS["آژیر"]
    )
    
    btn_cancel = types.InlineKeyboardButton(
        text="❌ انصراف",
        callback_data="attack_menu",
        style="danger",
        icon_custom_emoji_id=EMOJIS["نپذیرفتن"]
    )
    
    markup.add(btn_start, btn_cancel)
    
    text = (
        "<b>🔥 تأیید نهایی</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>مقصد:</b> {target}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>ایمیل‌ها:</b> {len(emails)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["متن"]}">📝</tg-emoji> <b>موضوع:</b> {subject[:50]}\n'
        f'<tg-emoji emoji-id="{EMOJIS["سکه"]}">🪙</tg-emoji> <b>تعداد هر ایمیل:</b> {count}\n'
        f'<tg-emoji emoji-id="{EMOJIS["گنج"]}">💰</tg-emoji> <b>کل گزارشات:</b> {len(emails) * count}\n\n'
        f'<b>📝 توضیحات:</b>\n{description[:100]}...\n\n'
        "<blockquote>⚠️ با شروع، گزارش‌ها ارسال می‌شوند!</blockquote>"
    )
    
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

# ============ شروع حمله ============
@bot.callback_query_handler(func=lambda call: call.data == "start_attack")
def start_attack(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    temp = load_temp()
    user_temp = temp.get(str(call.from_user.id), {})
    target = user_temp.get("target")
    emails = user_temp.get("selected_emails", [])
    count = user_temp.get("count", 0)
    subject = user_temp.get("subject", "گزارش تخلف")
    description = user_temp.get("description", "")
    
    if not target or not emails or count == 0:
        bot.answer_callback_query(call.id, "❌ اطلاعات ناقص است!")
        return
    
    bot.answer_callback_query(call.id, "🚀 حمله شروع شد!")
    
    progress_msg = bot.send_message(
        call.message.chat.id,
        "<b>🚀 شروع حمله...</b>\n\n⏳ در حال آماده‌سازی...",
        parse_mode="HTML"
    )
    
    threading.Thread(
        target=send_emails,
        args=(call.message.chat.id, progress_msg.message_id, target, emails, count, str(call.from_user.id), subject, description)
    ).start()

# ============ دکمه‌های عمومی ============
@bot.callback_query_handler(func=lambda call: call.data == "back_to_panel")
def back_to_panel(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_panel(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "contact_support")
def contact_support(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="back_to_start",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    text = (
        "<b>📞 تماس با پشتیبانی</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>آیدی شما:</b> <code>{call.from_user.id}</code>\n\n'
        "<blockquote>"
        "برای دریافت اشتراک، با مدیریت تماس بگیرید.\n"
        "🆔 <b>آیدی مدیر:</b> @admin_username\n"
        "</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def back_to_start(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if has_access(call.from_user.id):
        user_panel(call.message)
    else:
        no_access_panel(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "user_profile")
def user_profile(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    user_id = str(call.from_user.id)
    users = load_users()
    user_data = users.get(user_id, {})
    reports = load_reports()
    user_reports = [r for r in reports.values() if r.get("user_id") == user_id]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="back_to_panel",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    text = (
        f"<b>👤 حساب کاربری</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>نام:</b> {user_data.get("first_name", "نامشخص")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["چشم۲"]}">👀</tg-emoji> <b>یوزرنیم:</b> @{user_data.get("username", "ندارد")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["کیف"]}">👛</tg-emoji> <b>آیدی:</b> <code>{call.from_user.id}</code>\n'
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>تعداد گزارشات:</b> {len(user_reports)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["سکه"]}">🪙</tg-emoji> <b>ارسال شده:</b> {user_data.get("total_sent", 0)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">❌</tg-emoji> <b>ناموفق:</b> {user_data.get("total_failed", 0)}\n'
        f'<tg-emoji emoji-id="{EMOJIS["جام"]}">🏆</tg-emoji> <b>وضعیت:</b> فعال ✅\n\n'
        "<blockquote>اطلاعات حساب کاربری شما</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_help")
def user_help(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="back_to_panel",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    text = (
        "<b>❓ راهنمای ربات</b>\n\n"
        "1️⃣ <b>حمله به مقصد:</b>\n"
        "   • مقصد را انتخاب کنید\n"
        "   • ایمیل فرستنده را انتخاب کنید\n"
        "   • موضوع و توضیحات را وارد کنید\n"
        "   • تعداد گزارش را مشخص کنید\n\n"
        "2️⃣ <b>مقاصد موجود:</b>\n"
        "   • abuse@telegram.org\n"
        "   • recover@telegram.org\n"
        "   • dmca@telegram.org\n"
        "   • security@telegram.org\n"
        "   • spam@telegram.org\n\n"
        "3️⃣ <b>تعداد گزارش:</b>\n"
        "   • حداکثر ۲۵ گزارش برای هر ایمیل\n\n"
        "4️⃣ <b>پنل مدیریت:</b>\n"
        "   • /admin - دسترسی به پنل مدیریت\n\n"
        "<blockquote>برای شروع روی <b>حمله به مقصد</b> کلیک کنید!</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_reports")
def user_reports(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    user_id = str(call.from_user.id)
    reports = load_reports()
    user_reports = {rid: data for rid, data in reports.items() if data.get("user_id") == user_id}
    
    if not user_reports:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_back = types.InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_panel",
            style="primary",
            icon_custom_emoji_id=EMOJIS["چشم"]
        )
        markup.add(btn_back)
        
        bot.edit_message_text(
            "<b>📋 شما هیچ گزارشی ندارید!</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        return
    
    text = "<b>📊 گزارشات شما:</b>\n\n"
    for rid, data in list(user_reports.items())[-10:]:
        status = "✅" if data.get("status") == "completed" else "⏳"
        text += f"🆔 {rid}\n   مقصد: {data.get('target', 'نامشخص')}\n   ارسال: {data.get('sent', 0)}/{data.get('total', 0)} {status}\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="back_to_panel",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_stats")
def user_stats(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    user_id = str(call.from_user.id)
    users = load_users()
    user_data = users.get(user_id, {})
    reports = load_reports()
    user_reports = [r for r in reports.values() if r.get("user_id") == user_id]
    
    total_sent = user_data.get("total_sent", 0)
    total_failed = user_data.get("total_failed", 0)
    total_reports = len(user_reports)
    success_rate = (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="back_to_panel",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    markup.add(btn_back)
    
    text = (
        f"<b>📈 آمار شما</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["گزارش"]}">📄</tg-emoji> <b>کل گزارشات:</b> {total_reports}\n'
        f'<tg-emoji emoji-id="{EMOJIS["سکه"]}">🪙</tg-emoji> <b>ارسال شده:</b> {total_sent}\n'
        f'<tg-emoji emoji-id="{EMOJIS["خطا"]}">❌</tg-emoji> <b>ناموفق:</b> {total_failed}\n'
        f'<tg-emoji emoji-id="{EMOJIS["جام"]}">🏆</tg-emoji> <b>نرخ موفقیت:</b> {success_rate:.1f}%\n\n'
        "<blockquote>آمار عملکرد شما</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_settings")
def user_settings(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    user_id = str(call.from_user.id)
    users = load_users()
    user_data = users.get(user_id, {})
    prefs = user_data.get("preferences", {})
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    btn_lang = types.InlineKeyboardButton(
        text=f"🌐 زبان: {prefs.get('language', 'fa')}",
        callback_data="user_settings_lang",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    btn_notif = types.InlineKeyboardButton(
        text=f"🔔 اعلان‌ها: {'فعال' if prefs.get('notifications', True) else 'غیرفعال'}",
        callback_data="user_settings_notif",
        style="primary",
        icon_custom_emoji_id=EMOJIS["آژیر"]
    )
    
    btn_back = types.InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="back_to_panel",
        style="primary",
        icon_custom_emoji_id=EMOJIS["چشم"]
    )
    
    markup.add(btn_lang, btn_notif, btn_back)
    
    text = (
        f"<b>⚙️ تنظیمات</b>\n\n"
        f'<tg-emoji emoji-id="{EMOJIS["چشم"]}">👁️</tg-emoji> <b>زبان:</b> {prefs.get("language", "fa")}\n'
        f'<tg-emoji emoji-id="{EMOJIS["آژیر"]}">🚨</tg-emoji> <b>اعلان‌ها:</b> {"فعال" if prefs.get("notifications", True) else "غیرفعال"}\n\n'
        "<blockquote>تنظیمات کاربری</blockquote>"
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_settings_lang")
def user_settings_lang(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    user_id = str(call.from_user.id)
    users = load_users()
    prefs = users[user_id].get("preferences", {})
    current = prefs.get("language", "fa")
    new_lang = "en" if current == "fa" else "fa"
    
    prefs["language"] = new_lang
    users[user_id]["preferences"] = prefs
    save_users(users)
    
    bot.answer_callback_query(call.id, f"✅ زبان به {new_lang} تغییر کرد!")
    user_settings(call)

@bot.callback_query_handler(func=lambda call: call.data == "user_settings_notif")
def user_settings_notif(call):
    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
        return
    
    user_id = str(call.from_user.id)
    users = load_users()
    prefs = users[user_id].get("preferences", {})
    current = prefs.get("notifications", True)
    new_val = not current
    
    prefs["notifications"] = new_val
    users[user_id]["preferences"] = prefs
    save_users(users)
    
    bot.answer_callback_query(call.id, f"✅ اعلان‌ها: {'فعال' if new_val else 'غیرفعال'}")
    user_settings(call)

# ============ اجرا ============
print("=" * 80)
print("🤖 ربات ایمیل سندر نسخه کامل و عظیم روشن شد!")
print("=" * 80)
print(f"👑 آیدی ادمین: {ADMIN_ID}")
print("=" * 80)
print("✅ امکانات فعال:")
print("  📌 سیستم اشتراک کامل")
print("  📌 پنل مدیریت (۱۴ دکمه فعال)")
print("  📌 افزودن ایمیل با بررسی سلامت")
print("  📌 حذف ایمیل")
print("  📌 پاک کردن گزارشات")
print("  📌 لیست سیاه")
print("  📌 ریست دیتابیس")
print("  📌 خروجی دیتابیس")
print("  📌 ۵ مقصد پیشفرض + مقصد دلخواه")
print("  📌 انتخاب ایمیل با شماره")
print("  📌 دریافت موضوع و توضیحات")
print("  📌 انتخاب تعداد گزارش (۱-۲۵)")
print("  📌 نمایش پیشرفت با درصد")
print("  📌 نمایش لاگ لحظه‌ای")
print("  📌 ذخیره گزارشات کامل")
print("  📌 ارسال همگانی")
print("  📌 آمار کاربران")
print("  📌 تنظیمات کاربری")
print("  📌 ارسال فقط موضوع و توضیحات")
print("=" * 80)
print("🔄 ربات در حال اجرا...")

# Railway: clear any webhook before starting long polling.
# A second live process using the same BOT_TOKEN can still cause Telegram 409;
# Railway should have only one active replica/process for this bot token.
try:
    bot.delete_webhook(drop_pending_updates=False)
    logger.info("Telegram webhook cleared; starting polling")
except Exception:
    logger.exception("Could not clear Telegram webhook")

# Keep the original bot architecture and all existing handlers intact.
# Retry temporary polling/network failures instead of terminating the process.
while True:
    try:
        bot.infinity_polling(
            skip_pending=True,
            allowed_updates=["message", "callback_query"]
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        break
    except Exception:
        logger.exception("Polling stopped; retrying in 10 seconds")
        time.sleep(10)