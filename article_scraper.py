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
            # Получаем страницу логина для cookies
            print('Загрузка страницы входа...')
            login_page = self.session.get(self.login_url, timeout=10)
            print('Статус: ' + str(login_page.status_code))
            
            # Отправляем данные авторизации
            login_data = {
                'log': self.username,
                'pwd': self.password,
                'wp-submit': 'Войти',
                'redirect_to': self.base_url,
                'testcookie': '1'
            }

            print('Отправка данных...')
            response = self.session.post(
                self.login_url,
                data=login_data,
                timeout=15,
                allow_redirects=True
            )
            
            print('URL после входа: ' + response.url)
            print('Статус: ' + str(response.status_code))
            
            # Проверяем cookies
            cookies = self.session.cookies.get_dict()
            print('Cookies: ' + str(list(cookies.keys())))
            
            # Проверка успешности
            if 'wordpress_logged_in' in str(cookies):
                return True
            if 'wp-login' not in response.url:
                return True
            
            # Проверяем текст страницы на ошибки
            if 'Неверн' in response.text or 'ошибка' in response.text.lower():
                print('Сайт вернул ошибку авторизации')
                return False
                
            return True

        except Exception as e:
            print('Ошибка сети: ' + str(e))
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
            print('Ошибка: ' + str(e))
            return ''

    def get_article_urls(self):
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            urls = []
            for link in soup.select('article a, .post a, h2 a, h3 a, .entry-title a'):
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
        print('Найдено статей: ' + str(len(urls)))

        for i, url in enumerate(urls[:max_articles], 1):
            print('[' + str(i) + '] ' + url)

            text = self.get_article_text(url)
            if text:
                filename = 'articles/article_' + str(i) + '.txt'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                print('    Сохранено: ' + filename)
            else:
                print('    Текст не найден')

            time.sleep(1)


if __name__ == '__main__':
    USERNAME = 'Valeev'
    PASSWORD = 'iimes864'

    print('=' * 40)
    print('IIMES Article Scraper')
    print('=' * 40)
    
    scraper = ArticleScraper(USERNAME, PASSWORD)

    print('\nАвторизация...')
    if scraper.login():
        print('\nАвторизация успешна!')
        print('\nСкачивание статей...')
        scraper.scrape_articles(max_articles=10)
        print('\nГотово!')
    else:
        print('\nОшибка авторизации')
        print('Проверьте логин и пароль')
