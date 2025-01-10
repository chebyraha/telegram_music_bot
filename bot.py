import os
import yt_dlp
import asyncio
import requests
import base64

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Загрузка токена из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Максимальный размер файла для Telegram (в байтах)
TELEGRAM_FILE_SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB

# Хендлер на команду /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    welcome_text = (
        "👋 Привет! Я бот для скачивания музыки.\n\n"
        "📌 Отправь мне ссылку на страницу с треком, и я загружу для тебя аудиофайл.\n"
        "🎵 Поддерживаются ссылки с различных платформ.\n"
        "Если есть вопросы, просто напиши!\n\n"
        "👉 Для начала отправь ссылку."
    )
    await message.reply(welcome_text)

# Хендлер для обработки ссылок
@dp.message()
async def handle_message(message: Message):
    url = message.text
    user_id = message.from_user.id

    # Создание временной директории для пользователя
    if not os.path.exists(f'temp/{user_id}'):
        os.makedirs(f'temp/{user_id}')

    await message.reply("⏳ Загрузка началась...")
    try:
        # Проверяем, является ли ссылка на YouTube
        if "youtube.com" in url or "youtu.be" in url:
            file_path = await download_audio(url, user_id)
            await send_audio_file(file_path, message, user_id)
            return

        # Если ссылка не YouTube, используем парсер
        tracks = parse_tracks_from_page(url, user_id)
        if not tracks:
            await message.reply("❌ Не удалось найти аудиофайлы на странице.")
            return

        # Загружаем и отправляем все найденные треки
        for track in tracks:
            file_path = track['path']
            await send_audio_file(file_path, message, user_id)

    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# Функция парсинга треков с HTML-страницы
def parse_tracks_from_page(page_url, user_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        tracks = []
        for item in soup.find_all('li', class_='item'):
            play = item.find('li', class_='play')
            desc = item.find('div', class_='desc')

            if play and desc:
                encoded_url = play.get('data-url')

                # Просто используем encoded_url как обычную строку
                url = encoded_url

                artist = desc.find('span', class_='artist').text.strip()
                track = desc.find('span', class_='track').text.strip()
                track_name = f"{artist} - {track}"
                file_path = save_track(url, track_name, user_id)

                tracks.append({'url': url, 'path': file_path})
        return tracks
    except Exception as e:
        print(f"Ошибка при парсинге страницы: {e}")
        return []

# Функция сохранения трека
def save_track(download_url, track_name, user_id):
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        user_folder = f'temp/{user_id}'
        os.makedirs(user_folder, exist_ok=True)

        sanitized_name = ''.join(c for c in track_name if c.isalnum() or c in ' _-').strip()
        file_path = os.path.join(user_folder, f"{sanitized_name}.mp3")

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return file_path
    except Exception as e:
        print(f"Ошибка при загрузке трека {track_name}: {e}")
        return None

# Функция отправки аудиофайла
async def send_audio_file(file_path, message, user_id):
    try:
        file_size = os.path.getsize(file_path)
        if file_size > TELEGRAM_FILE_SIZE_LIMIT:
            await message.reply(
                f"❌ Файл слишком большой для отправки через Telegram ({file_size / 1024 / 1024:.2f} МБ)."
            )
            return

        audio_file = FSInputFile(file_path)
        await bot.send_audio(chat_id=message.chat.id, audio=audio_file)
        await message.reply("🎉 Готово! Вот твой трек. Если нужно ещё, просто отправь следующую ссылку!")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# Функция загрузки аудио с YouTube
async def download_audio(url, user_id):
    options = {
        'format': 'bestaudio/best',
        'outtmpl': f'temp/{user_id}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        output_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

    return output_path

# Основная точка входа
async def main():
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(handle_message)

    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
