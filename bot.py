import os
import re
import csv
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from yt_dlp import YoutubeDL

TOKEN = "8688004896:AAGzUhvhy14w5HZMYRQm0DsVjy6nLmhT1s0"

USERS_FILE = "users.csv"


def load_users():
    users = {}

    if not os.path.exists(USERS_FILE):
        return users

    with open(USERS_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users[row["id"]] = row

    return users


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["id", "username", "full_name", "first_seen", "downloads"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users.values())


def register_user(user):
    users = load_users()
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {
            "id": user_id,
            "username": user.username or "",
            "full_name": user.full_name or "",
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "downloads": "0",
        }
    else:
        users[user_id]["username"] = user.username or ""
        users[user_id]["full_name"] = user.full_name or ""

    save_users(users)


def add_download(user):
    register_user(user)

    users = load_users()
    user_id = str(user.id)

    users[user_id]["downloads"] = str(int(users[user_id]["downloads"]) + 1)

    save_users(users)


def download_tiktok(url: str) -> Path:
    temp = Path(tempfile.mkdtemp())

    ydl_opts = {
        "outtmpl": str(temp / "%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "quiet": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))


async def download_async(url: str) -> Path:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: download_tiktok(url))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    await update.message.reply_text(
        "أرسل رابط الفيديو وسأحمّله لك بدون علامة مائية."
    )


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    total = len(users)

    text = f"إجمالي المشتركين: {total}\n\n"

    for user in users.values():
        name = user["full_name"] or "بدون اسم"
        username = f"@{user['username']}" if user["username"] else "بدون يوزر"
        first_seen = user["first_seen"]
        downloads = user["downloads"]

        text += f"الاسم: {name}\n"
        text += f"اليوزر: {username}\n"
        text += f"أول استخدام: {first_seen}\n"
        text += f"عدد التحميلات: {downloads}\n"
        text += "--------------------\n"

    await update.message.reply_text(text[:4000])


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    text = update.message.text
    match = re.search(r"(https?://[^\s]+tiktok[^\s]+)", text)

    if not match:
        await update.message.reply_text("⚠️ أرسل رابط تيك توك صحيح.")
        return

    url = match.group(1)
    msg = await update.message.reply_text("🔄 جاري التحميل...")

    try:
        await context.bot.send_chat_action(
            update.effective_chat.id,
            ChatAction.TYPING
        )

        video_path = await download_async(url)

        await msg.edit_text("📤 جاري الإرسال...")

        with open(video_path, "rb") as video:
            await update.message.reply_video(video)

        add_download(update.effective_user)

        await msg.delete()

        try:
            video_path.unlink()
        except:
            pass

    except Exception as e:
        await msg.edit_text(f"⚠️ حدث خطأ:\n{e}")


def main():
    if not TOKEN or TOKEN == "ضع_التوكن_هنا":
        raise ValueError("ضع التوكن الحقيقي داخل TOKEN")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("count", count))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚀 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
