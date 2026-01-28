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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def login(self):
        try:
            self.session.get(self.base_url, timeout=10)

            login_data = {
                'log': self.username,
                'pwd': self.password,
                'wp-submit': 'Войти',
                'redirect_to': self.base_url + '/',
                'testcookie': '1'
            }

            response = self.session.post(
                self.login_url,
                data=login_data,
                headers={'Referer': self.base_url},
                timeout=15,
                allow_redirects=True
            )

            return 'wp-login' not in response.url.lower()

        except Exception as e:
            print('Ошибка авторизации:', e)
            return False

    def get_article_text(self, url):
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return ''

            soup = BeautifulSoup(response.text, 'html.parser')

            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                tag.decompose()

            content = None
            for selector in ['.entry-content', '.post-content', '.article-content', 'article', 'main']:
                content = soup.select_one(selector)
                if content:
                    break

            if not content:
                return ''

            paragraphs = []
            for elem in content.find_all(['p', 'h2', 'h3', 'h4']):
                text = elem.get_text(separator=' ')
                text = ' '.join(text.split())
                if text and len(text) > 10:
                    paragraphs.append(text)

            return '\n\n'.join(paragraphs)

        except Exception as e:
            print('Ошибка:', e)
            return ''

    def get_article_urls(self):
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            urls = []
            for link in soup.select('article a, .post a, h2 a, h3 a'):
                href = link.get('href')
                if href and self.base_url in href and href not in urls:
                    urls.append(href)

            return urls[:20]

        except Exception:
            return []

    def scrape_articles(self, max_articles=10):
        if not os.path.exists('articles'):
            os.makedirs('articles')

        urls = self.get_article_urls()

        for i, url in enumerate(urls[:max_articles], 1):
            print('[' + str(i) + '] ' + url)

            text = self.get_article_text(url)
            if text:
                filename = 'articles/article_' + str(i) + '.txt'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                print('    Сохранено: ' + filename)

            time.sleep(1)


if __name__ == '__main__':
    USERNAME = 'Valeev'
    PASSWORD = 'iimes864'

    print('Запуск скрапера...')
    scraper = ArticleScraper(USERNAME, PASSWORD)

    print('Авторизация...')
    if scraper.login():
        print('Авторизация успешна!')
        print('Скачивание статей...')
        scraper.scrape_articles(max_articles=10)
        print('Готово!')
    else:
        print('Ошибка авторизации')
