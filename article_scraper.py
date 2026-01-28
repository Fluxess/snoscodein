#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import os
import re
from docx import Document


class ArticleScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = 'https://www.iimes.ru'
        self.login_url = self.base_url + '/wp-login.php'
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

    def login(self):
        try:
            self.session.get(self.login_url, timeout=10)
            
            login_data = {
                'log': self.username,
                'pwd': self.password,
                'wp-submit': 'Войти',
                'redirect_to': self.base_url,
                'testcookie': '1'
            }

            response = self.session.post(
                self.login_url,
                data=login_data,
                timeout=15,
                allow_redirects=True
            )
            
            return 'wp-login' not in response.url

        except Exception as e:
            print('Ошибка: ' + str(e))
            return False

    def is_article_url(self, url):
        # Статьи обычно имеют формат /?p=123 или /год/месяц/название/
        if '/?p=' in url:
            return True
        # Проверяем формат /2024/01/название/
        if re.search(r'/\d{4}/\d{2}/', url):
            return True
        return False

    def get_article_text(self, url):
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return [], ''

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Получаем заголовок статьи
            title = ''
            title_elem = soup.select_one('h1.entry-title') or soup.select_one('h1.post-title') or soup.select_one('article h1') or soup.select_one('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Ищем контент статьи
            content = soup.select_one('.entry-content') or soup.select_one('.post-content') or soup.select_one('article .content')
            
            if not content:
                return [], title

            # Удаляем лишние элементы внутри контента
            for tag in content.find_all(['script', 'style', 'nav', 'aside', 'form', 'iframe', 'header', 'footer']):
                tag.decompose()
            
            # Удаляем блоки с классами навигации, меню, виджетов
            for tag in content.find_all(class_=re.compile(r'nav|menu|widget|sidebar|share|social|related|comment', re.I)):
                tag.decompose()

            # Извлекаем только параграфы с текстом статьи
            paragraphs = []
            for elem in content.find_all('p'):
                text = elem.get_text(separator=' ')
                text = ' '.join(text.split())
                
                # Пропускаем короткие строки и служебный текст
                if len(text) < 50:
                    continue
                    
                # Пропускаем навигацию и служебные элементы
                skip = ['cookie', 'подписк', 'войти', 'регистр', 'читайте также', 'поделиться', 'комментар', 'теги:', 'категор', 'опубликован', 'автор:']
                if any(s in text.lower() for s in skip):
                    continue
                
                paragraphs.append(text)

            return paragraphs, title

        except Exception as e:
            print('Ошибка: ' + str(e))
            return [], ''

    def get_article_urls(self, max_pages=15):
        urls = []
        
        for page in range(1, max_pages + 1):
            try:
                if page == 1:
                    page_url = self.base_url
                else:
                    page_url = self.base_url + '/page/' + str(page) + '/'
                
                print('Страница ' + str(page) + '...')
                response = self.session.get(page_url, timeout=10)
                
                if response.status_code != 200:
                    break
                    
                soup = BeautifulSoup(response.text, 'html.parser')

                # Ищем ссылки только на статьи
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and self.is_article_url(href):
                        if href not in urls:
                            urls.append(href)
                
                time.sleep(0.5)

            except Exception:
                break

        print('Найдено статей: ' + str(len(urls)))
        return urls

    def save_to_word(self, paragraphs, title, filename):
        doc = Document()
        
        if title:
            doc.add_heading(title, 0)
        
        for para in paragraphs:
            doc.add_paragraph(para)
        
        doc.save(filename)

    def make_safe_filename(self, title):
        # Убираем недопустимые символы
        safe = title
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n', '\r', '\t']:
            safe = safe.replace(char, '')
        safe = safe.strip()
        # Ограничиваем длину
        if len(safe) > 100:
            safe = safe[:100]
        return safe if safe else 'article'

    def scrape_articles(self, max_articles=90):
        if not os.path.exists('articles'):
            os.makedirs('articles')

        urls = self.get_article_urls(max_pages=15)

        saved = 0
        for i, url in enumerate(urls, 1):
            if saved >= max_articles:
                break
                
            print('[' + str(i) + '] ' + url)

            paragraphs, title = self.get_article_text(url)
            
            # Сохраняем только если есть достаточно текста
            if paragraphs and len(paragraphs) >= 2:
                saved += 1
                
                # Имя файла = заголовок статьи
                safe_title = self.make_safe_filename(title)
                filename = 'articles/' + safe_title + '.docx'
                
                # Если файл уже есть, добавляем номер
                if os.path.exists(filename):
                    filename = 'articles/' + safe_title + '_' + str(saved) + '.docx'
                
                self.save_to_word(paragraphs, title, filename)
                print('    OK: ' + title[:60])
            else:
                print('    Пропущено (мало текста)')

            time.sleep(1)
        
        print('\n' + '=' * 40)
        print('Скачано статей: ' + str(saved))
        print('=' * 40)


if __name__ == '__main__':
    USERNAME = 'Valeev'
    PASSWORD = 'iimes864'

    print('IIMES Scraper')
    print('=' * 40)
    
    scraper = ArticleScraper(USERNAME, PASSWORD)

    print('Авторизация...')
    if scraper.login():
        print('OK\n')
        scraper.scrape_articles(max_articles=90)
        print('\nФайлы в папке articles/')
    else:
        print('Ошибка авторизации')
