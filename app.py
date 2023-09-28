import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import random


# Функция для преобразования строки даты в объект datetime
def parse_date(date_string):
    month_map = {
        'января': '01',
        'февраля': '02',
        'марта': '03',
        'апреля': '04',
        'мая': '05',
        'июня': '06',
        'июля': '07',
        'августа': '08',
        'сентября': '09',
        'октября': '10',
        'ноября': '11',
        'декабря': '12'
    }
    try:
        day, month_word, year, time = date_string.split(' ')
        year = year.replace(',', '')
        month = month_map[month_word]
        formatted_date = f"{day}.{month}.{year} {time}"
        return datetime.strptime(formatted_date, '%d.%m.%Y %H:%M')
    except Exception as e:
        print(f"Не удалось разобрать дату: {date_string}, ошибка: {e}")
        return None


def get_existing_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_data(data, filename):
    sorted_data = sorted(data, key=lambda x: parse_date(x['DatePublished']))
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(sorted_data, file, ensure_ascii=False, indent=4)


def get_article_links(base_url, path):
    url = base_url + path
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('article')
        links = {base_url + a['href'] for article in articles for a in article.find_all('a') if a.has_attr('href')}
        # Отфильтровываем ссылки на страницы комментариев
        return {link for link in links if 'all.comments.html' not in link}
    except requests.RequestException as e:
        print(f"Ошибка при получении данных с {url}: {e}")
        return set()


def get_article_content(link):
    try:
        response = requests.get(link)
        response.raise_for_status()  # Проверка на ошибки
        soup = BeautifulSoup(response.content, 'html.parser')
        h1_content = soup.find('h1').get_text(strip=True) if soup.find('h1') else None
        if h1_content and "Страница не найдена" in h1_content:
            return None
        article_body = soup.find('section', itemprop="articleBody")
        p_content = [p.get_text(strip=True) for p in article_body.find_all('p')] if article_body else []
        date_published = soup.find('span', itemprop="datePublished").get_text(strip=True) if soup.find('span', itemprop="datePublished") else None

        return {
            "URL": link,
            "H1": h1_content,
            "Paragraphs": p_content,
            "DatePublished": date_published
        }
    except requests.RequestException as e:
        # Сокращенное сообщение об ошибке
        print(f"Ошибка при получении данных со страницы {link}: {e.response.status_code} {e.response.reason}")
        return None


def collect_data():
    base_url = 'https://www.fontanka.ru/'
    links = get_article_links(base_url, 'incidents/')

    existing_data = get_existing_data('collected_data_original.json')
    existing_urls = {entry["URL"] for entry in existing_data}

    new_entries = [get_article_content(link) for link in links if link not in existing_urls]
    new_entries = [entry for entry in new_entries if entry]  # Удаляем пустые или None записи

    added_count = len(new_entries)
    if added_count:
        existing_data.extend(new_entries)
        save_data(existing_data, 'collected_data_original.json')

        total_count = len(existing_data)
        print(f"Добавлено(а) {added_count} записей. Всего записей: {total_count}.")
    else:
        print("Нет новых записей.")


while True:
    collect_data()
    wait_time = 40 + random.randint(0, 60)  # Добавляем случайную задержку от 0 до 30 секунд
    print(f"Ждем добавление новых записей {wait_time} секунд...")
    time.sleep(wait_time)
