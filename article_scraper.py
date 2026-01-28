#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import os


class ArticleScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = 'https://www.iimes.ru'
        self.login_url = self.base_url + '/wp-login.php'
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        })

    def login(self):
        try:
            print('Загрузка страницы входа...')
            login_page = self.session.get(self.login_url, timeout=10)
            
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
            
            cookies = self.session.cookies.get_dict()
            
            if 'wordpress_logged_in' in str(cookies):
                return True
            if 'wp-login' not in response.url:
                return True
                
            return True

        except Exception as e:
            print('Ошибка сети: ' + str(e))
            return False

    def get_article_text(self, url):
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return ''

            # Сохраняем HTML первой статьи для анализа
            if not os.path.exists('debug.html'):
                with open('debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print('    HTML сохранен в debug.html')

            soup = BeautifulSoup(response.text, 'html.parser')

            # Удаляем ненужные элементы
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'aside', 'form', 'iframe']):
                tag.decompose()

            # Пробуем разные селекторы
            content = None
            selectors = [
                '.entry-content',
                '.post-content', 
                '.article-content',
                '.content',
                '.single-content',
                '.post-body',
                '.article-body',
                '.text',
                '.post',
                'article',
                '.entry',
                'main',
                '#content',
                '.page-content'
            ]
            
            for selector in selectors:
                content = soup.select_one(selector)
                if content:
                    # Проверяем что есть текст
                    text_check = content.get_text(strip=True)
                    if len(text_check) > 100:
                        print('    Найден контент: ' + selector)
                        break
                    content = None

            # Если не нашли по селекторам - берем body
            if not content:
                content = soup.find('body')
                if content:
                    print('    Используем body')

            if not content:
                return ''

            # Извлекаем параграфы
            paragraphs = []
            for elem in content.find_all(['p']):
                text = elem.get_text(separator=' ')
                text = ' '.join(text.split())
                # Фильтруем короткие и служебные тексты
                if text and len(text) > 50:
                    # Пропускаем меню, кнопки и т.д.
                    skip_words = ['cookie', 'подписк', 'войти', 'регистр', 'пароль', 'copyright']
                    if not any(w in text.lower() for w in skip_words):
                        paragraphs.append(text)

            return '\n\n'.join(paragraphs)

        except Exception as e:
            print('Ошибка: ' + str(e))
            return ''

    def get_article_urls(self):
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            urls = []
            # Ищем все ссылки на статьи
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if not href:
                    continue
                # Фильтруем только статьи
                if self.base_url in href or href.startswith('/'):
                    if href.startswith('/'):
                        href = self.base_url + href
                    # Пропускаем служебные страницы
                    skip = ['wp-login', 'wp-admin', 'feed', 'category', 'tag', 'author', '#', '.jpg', '.png', '.pdf']
                    if not any(s in href.lower() for s in skip):
                        if href not in urls and href != self.base_url and href != self.base_url + '/':
                            urls.append(href)

            print('Найдено ссылок: ' + str(len(urls)))
            return urls[:20]

        except Exception as e:
            print('Ошибка: ' + str(e))
            return []

    def scrape_articles(self, max_articles=10):
        if not os.path.exists('articles'):
            os.makedirs('articles')

        urls = self.get_article_urls()

        saved = 0
        for i, url in enumerate(urls[:max_articles], 1):
            print('[' + str(i) + '] ' + url)

            text = self.get_article_text(url)
            if text and len(text) > 200:
                saved += 1
                filename = 'articles/article_' + str(saved) + '.txt'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                print('    Сохранено: ' + filename + ' (' + str(len(text)) + ' символов)')
            else:
                print('    Мало текста или не найден')

            time.sleep(1)
        
        print('\nСохранено статей: ' + str(saved))


if __name__ == '__main__':
    USERNAME = 'Valeev'
    PASSWORD = 'iimes864'

    print('=' * 40)
    print('IIMES Article Scraper')
    print('=' * 40)
    
    scraper = ArticleScraper(USERNAME, PASSWORD)

    print('\nАвторизация...')
    if scraper.login():
        print('OK')
        print('\nСкачивание статей...')
        scraper.scrape_articles(max_articles=10)
        print('\nГотово!')
        print('Проверь папку articles/')
    else:
        print('Ошибка авторизации')
