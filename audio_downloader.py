import requests
from bs4 import BeautifulSoup


def get_audio_urls(page_url):
    """
    Функция для получения всех ссылок на аудиофайлы со страницы.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        # Загружаем страницу
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()

        # Парсим страницу
        soup = BeautifulSoup(response.text, "html.parser")

        # Ищем все теги <li> с классом "play"
        audio_tags = soup.find_all("li", class_="play")

        # Список для хранения найденных аудиофайлов
        audio_urls = []

        for audio_tag in audio_tags:
            # Извлекаем ссылку из атрибута data-url
            audio_url = audio_tag.get("data-url")
            if audio_url:
                audio_urls.append(audio_url)

        # Если ссылки найдены, возвращаем список
        if audio_urls:
            return audio_urls
        else:
            print("❌ Ссылки на аудиофайлы не найдены.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при загрузке страницы: {e}")
        return None


# Тестовый вызов
if __name__ == "__main__":
    test_url = "https://muzofond.fm/collections/albums/linkin%20park%20zero"
    audio_urls = get_audio_urls(test_url)
    if audio_urls:
        print(f"✅ Найдены ссылки на аудиофайлы:")
        for url in audio_urls:
            print(url)
