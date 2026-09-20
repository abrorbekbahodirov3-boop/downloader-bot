import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Salom! YouTube, Instagram, TikTok link yubor - yuklab beraman.")

@dp.message()
async def download(message: types.Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("Iltimos link yuboring")
        return
    await message.answer("⏳ Yuklanmoqda...")
    try:
        ydl_opts = {'outtmpl': '%(title)s.%(ext)s', 'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        await message.answer_document(types.FSInputFile(filename))
        os.remove(filename)
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

async def handle(request):
    return web.Response(text="Bot ishlayapti!")

async def main():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
