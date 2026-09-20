import os
import asyncio
import logging
import tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env not set")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

YDL_OPTS_VIDEO = {
    'format': 'best[height<=720][ext=mp4]/best',
    'outtmpl': '%(id)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
}

YDL_OPTS_AUDIO = {
    'format': 'bestaudio/best',
    'outtmpl': '%(id)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
}

def get_platform(url: str):
    url = url.lower()
    if 'instagram.com' in url: return 'Instagram'
    if 'tiktok.com' in url: return 'TikTok'
    if 'youtube.com' in url or 'youtu.be' in url: return 'YouTube'
    return None

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    text = (
        "👋 Salom! Men yuklovchi botman\n\n"
        "🔗 Instagram / TikTok / YouTube link tashlang, yuklab beraman.\n\n"
        "⚠️ Iltimos, faqat o'zingizga tegishli yoki yuklashga ruxsatingiz bor kontentni yuklang. Mualliflik huquqini hurmat qiling.\n\n"
        "Buyruqlar:\n"
        "/start - boshlash\n"
        "/help - yordam"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Qoidalar", callback_data="rules")]
    ])
    await message.answer(text, reply_markup=kb)

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer("Qanday ishlatiladi:\n1. Instagram Reels, TikTok yoki YouTube linkini yuboring\n2. Men tekshirib, yuklab beraman\n3. YouTube uchun video yoki audio tanlash tugmalari chiqadi\n\nAgar link shaxsiy (private) bo'lsa, yuklab bo'lmaydi.")

@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    if call.data == "rules":
        await call.message.answer("©️ Mualliflik qoidasi: Faqat o'zingiz yaratgan yoki ruxsat berilgan videolarni yuklang.")
    await call.answer()

@dp.message()
async def download_handler(message: types.Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("Iltimos, to'g'ri link yuboring (https://...)")
        return
    platform = get_platform(url)
    if not platform:
        await message.answer("❌ Bu linkni tushunmadim. Faqat Instagram, TikTok, YouTube linklarini yuboring.")
        return
    await message.answer(f"⏳ {platform} dan yuklanmoqda... Iltimos kuting.")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = YDL_OPTS_VIDEO.copy()
            opts['outtmpl'] = os.path.join(tmpdir, '%(id)s.%(ext)s')
            if platform == "YouTube":
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎬 Video (720p)", callback_data=f"yt_video|{url}"),
                     InlineKeyboardButton(text="🎵 Audio MP3", callback_data=f"yt_audio|{url}")]
                ])
                await message.answer("YouTube uchun format tanlang:", reply_markup=kb)
                return
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
                import glob
                files = glob.glob(os.path.join(tmpdir, "*"))
                if not files:
                    raise Exception("Fayl topilmadi")
                file_path = files[0]
                if os.path.getsize(file_path) > 48*1024*1024:
                    await message.answer("⚠️ Fayl juda katta (50MB dan oshdi).")
                    return
                if file_path.endswith(('.mp4','.mov','.mkv','.webm')):
                    await bot.send_video(message.chat.id, types.FSInputFile(file_path), caption=f"✅ {platform} dan yuklandi")
                elif file_path.endswith(('.jpg','.jpeg','.png','.webp')):
                    await bot.send_photo(message.chat.id, types.FSInputFile(file_path), caption=f"✅ {platform} dan yuklandi")
                else:
                    await bot.send_document(message.chat.id, types.FSInputFile(file_path))
    except Exception as e:
        logging.exception(e)
        await message.answer(f"❌ Yuklab bo'lmadi: {str(e)[:300]}")

@dp.callback_query(lambda c: c.data.startswith("yt_"))
async def yt_choice(call: types.CallbackQuery):
    try:
        action, url = call.data.split("|",1)
        await call.message.edit_text("⏳ YouTube yuklanmoqda...")
        with tempfile.TemporaryDirectory() as tmpdir:
            if action == "yt_video":
                opts = YDL_OPTS_VIDEO.copy()
            else:
                opts = YDL_OPTS_AUDIO.copy()
            opts['outtmpl'] = os.path.join(tmpdir, '%(id)s.%(ext)s')
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                import glob
                files = glob.glob(os.path.join(tmpdir, "*"))
                fp = files[0]
                if action == "yt_video":
                    await bot.send_video(call.message.chat.id, types.FSInputFile(fp))
                else:
                    await bot.send_audio(call.message.chat.id, types.FSInputFile(fp))
    except Exception as e:
        await call.message.answer(f"Xatolik: {e}")
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
