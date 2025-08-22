import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus
import time
import logging

logger = logging.getLogger(__name__)

class GeniusScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_song(self, query):
        """Поиск песни на Genius.com"""
        try:
            logger.info(f"Searching for: {query}")
            
            # Пробуем поиск через API
            result, error = self._search_via_api(query)
            if result:
                return result, error
            
            # Если API не сработал, пробуем HTML поиск
            result, error = self._search_via_html(query)
            if result:
                return result, error
            
            # Пробуем прямой поиск для известных песен
            result, error = self._search_direct(query)
            if result:
                return result, error
            
            return None, "Песня не найдена. Попробуйте другой запрос."
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None, f"Ошибка при поиске: {str(e)}"
    
    def _search_via_api(self, query):
        """Поиск через API Genius"""
        try:
            search_url = f"https://genius.com/api/search/multi?per_page=5&q={quote_plus(query)}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'sections' in data['response']:
                    for section in data['response']['sections']:
                        if section.get('type') == 'song':
                            for hit in section.get('hits', []):
                                if 'result' in hit and 'url' in hit['result']:
                                    song_url = hit['result']['url']
                                    return self.get_lyrics(song_url)
            return None, None
            
        except Exception as e:
            logger.error(f"API search error: {e}")
            return None, None
    
    def _search_via_html(self, query):
        """Поиск через HTML страницу"""
        try:
            search_url = f"https://genius.com/search?q={quote_plus(query)}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Ищем ссылки на песни
                song_links = []
                
                # Поиск в мини-карточках
                mini_cards = soup.find_all('div', class_=re.compile(r'mini_card|song_card'))
                for card in mini_cards:
                    link = card.find('a', href=re.compile(r'/songs/'))
                    if link and link.get('href'):
                        song_links.append(link['href'])
                
                # Поиск по всем ссылкам
                all_links = soup.find_all('a', href=re.compile(r'/songs/'))
                for link in all_links:
                    href = link.get('href')
                    if href and href not in song_links:
                        song_links.append(href)
                
                if song_links:
                    song_url = "https://genius.com" + song_links[0]
                    return self.get_lyrics(song_url)
            
            return None, None
            
        except Exception as e:
            logger.error(f"HTML search error: {e}")
            return None, None
    
    def _search_direct(self, query):
        """Прямой поиск по известным песням"""
        query_lower = query.lower()
        
        # Русские песни
        russian_songs = [
            ("марафеты", "/Dabbackwood-marathons-lyrics"),
            ("баратриум", "/Anacondaz-barathrum-lyrics"),
            ("анкаондоз баратриум", "/Anacondaz-barathrum-lyrics"),
            ("дэббэквуд марафеты", "/Dabbackwood-marathons-lyrics"),
        ]
        
        # Английские песни
        english_songs = [
            ("bohemian rhapsody queen", "/Queen-bohemian-rhapsody-lyrics"),
            ("let it be beatles", "/The-Beatles-let-it-be-lyrics"),
            ("hotel california eagles", "/Eagles-hotel-california-lyrics"),
        ]
        
        all_songs = russian_songs + english_songs
        
        for pattern, path in all_songs:
            if pattern in query_lower:
                song_url = "https://genius.com" + path
                # Проверяем, существует ли страница
                response = self.session.get(song_url, timeout=5)
                if response.status_code == 200:
                    return self.get_lyrics(song_url)
        
        return None, None
    
    def get_lyrics(self, song_url):
        """Извлечение текста песни"""
        try:
            response = self.session.get(song_url, timeout=10)
            
            if response.status_code != 200:
                return None, f"Страница не найдена (код {response.status_code})"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Заголовок песни
            title_element = soup.find('h1') or soup.find('title')
            title = title_element.get_text().strip() if title_element else "Неизвестная песня"
            
            # Извлекаем текст
            lyrics = self._extract_lyrics(soup)
            
            if not lyrics:
                return None, "Текст песни не найден на странице"
            
            # Очищаем текст
            lyrics = re.sub(r'\n\s*\n\s*\n+', '\n\n', lyrics)
            lyrics = lyrics.strip()
            
            return {
                'title': title,
                'lyrics': lyrics,
                'url': song_url
            }, None
            
        except Exception as e:
            logger.error(f"Lyrics extraction error: {e}")
            return None, f"Ошибка при извлечении текста: {str(e)}"
    
    def _extract_lyrics(self, soup):
        """Извлечение текста различными способами"""
        # Способ 1: современный формат
        lyrics_containers = soup.find_all('div', {'data-lyrics-container': 'true'})
        if lyrics_containers:
            texts = []
            for container in lyrics_containers:
                html = str(container)
                text = re.sub(r'<br\s*/?>', '\n', html)
                text = re.sub(r'</p>', '\n\n', text)
                text = re.sub(r'<[^>]+>', '', text)
                texts.append(text)
            return '\n'.join(texts)
        
        # Способ 2: классический lyrics контейнер
        lyrics_div = soup.find('div', class_=re.compile(r'lyrics|Lyrics__Container'))
        if lyrics_div:
            return lyrics_div.get_text(separator='\n', strip=False)
        
        # Способ 3: поиск по всем div с текстом
        for div in soup.find_all('div'):
            text = div.get_text(separator='\n', strip=False)
            if len(text) > 200 and any(word in text.lower() for word in 
                                     ['verse', 'chorus', 'bridge', 'куплет', 'припев']):
                return text
        
        return None