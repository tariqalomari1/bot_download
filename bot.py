import os
import re
import asyncio
import tempfile
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from yt_dlp import YoutubeDL

# -----------------------------------------------------
# ⚠️ ضع التوكن داخل علامتي التنصيص بالأسفل
TOKEN = "8688004896:AAE2M_npZT95P0js8ti9h1FygViGlfRS7cU"
# -----------------------------------------------------

# --------- دالة تحميل فيديو من تيك توك ---------
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

# --------- أوامر البوت ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط الفيديو وسأحمّله لك بدون علامة مائية.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    match = re.search(r"(https?://[^\s]+tiktok[^\s]+)", text)

    if not match:
        await update.message.reply_text("⚠️ أرسل رابط تيك توك صحيح.")
        return

    url = match.group(1)
    msg = await update.message.reply_text("🔄 جاري التحميل…")

    try:
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        video_path = await download_async(url)

        await msg.edit_text("📤 جاري الإرسال…")

        with open(video_path, "rb") as f:
            await update.message.reply_video(f)

        await msg.edit_text("✔️ تم الإرسال بنجاح!")
        await msg.delete()
        # حذف الملف بعد الإرسال
        video_path.unlink()

    except Exception as e:
        await msg.edit_text(f"⚠️ حدث خطأ: {e}")

        await msg.delete()

# --------- تشغيل البوت ---------
def main():
    if not TOKEN or TOKEN == "ضع_التوكن_هنا":
        raise ValueError("⚠️ فضلاً ضع التوكن داخل المتغير TOKEN في أعلى الملف.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚀 البوت يعمل الآن…")
    app.run_polling()

if __name__ == "__main__":
    main()