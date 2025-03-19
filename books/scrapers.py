import requests
from bs4 import BeautifulSoup
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from django.utils import timezone
from .models import Publisher, Book
import json
import re
import time
import feedparser
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


class BookScraper(ABC):
    def __init__(self, publisher):
        self.publisher = publisher
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    @abstractmethod
    def get_latest_books(self, limit=10):
        pass

    def save_books(self, books_data):
        new_books = []
        for book_data in books_data:
            try:
                existing_book = Book.objects.filter(book_url=book_data['book_url']).first()
                if not existing_book:
                    book = Book(
                        title=book_data['title'],
                        author=book_data['author'],
                        publisher=self.publisher,
                        description=book_data.get('description', ''),
                        cover_url=book_data.get('cover_url', ''),
                        book_url=book_data['book_url'],
                        publication_date=book_data['publication_date'],
                        isbn=book_data.get('isbn', ''),
                    )
                    book.save()
                    new_books.append(book)
                    logger.info(f"Saved new book: {book.title}")
            except Exception as e:
                logger.error(f"Error saving book {book_data.get('title', 'Unknown')}: {str(e)}")

        return new_books


class OreillyBookScraper:
    def __init__(self):
        self.publisher_name = "O'Reilly Media, Inc."
        self.publisher, _ = Publisher.objects.get_or_create(name=self.publisher_name)
        self.api_url = "https://www.oreilly.com/search/api/search/"
        self.params = {
            "q": "*",
            "type": "book",
            "publishers": "O'Reilly Media, Inc.",
            "order_by": "created_at",
            "rows": 100,
            "language": "en"
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.oreilly.com/search/",
            "Origin": "https://www.oreilly.com"
        }

    def extract_isbn_from_url(self, url):
        matches = re.findall(r'/(\d{13})/', url)
        if matches:
            return matches[0]
        return None

    def get_latest_books(self, limit=10):
        books = []

        try:
            response = requests.get(
                self.api_url,
                params=self.params,
                headers=self.headers,
                timeout=30
            )

            with open('oreilly_api_response.json', 'w', encoding='utf-8') as f:
                f.write(response.text)

            if response.status_code != 200:
                logger.warning(f"API returned status {response.status_code}")
                return self._try_rss_fallback(limit)

            data = response.json()

            if not data or 'data' not in data or 'products' not in data['data']:
                logger.warning("No book data found in API response")
                return self._try_rss_fallback(limit)

            current_date = datetime.now(timezone.utc).date()
            one_month_future = current_date.replace(month=current_date.month+1) if current_date.month < 12 else current_date.replace(year=current_date.year+1, month=1)
            three_months_past = current_date

            for _ in range(3):
                month = three_months_past.month - 1
                year = three_months_past.year
                if month == 0:
                    month = 12
                    year -= 1
                three_months_past = three_months_past.replace(year=year, month=month)

            logger.info(f"Looking for books published between {three_months_past} and {one_month_future}")

            processed_count = 0
            for product in data['data']['products']:
                processed_count += 1

                if product.get('type') != 'book':
                    continue

                publisher_details = product.get('custom_attributes', {}).get('publisher_details', [])
                publisher_names = [pub.get('name') for pub in publisher_details if pub.get('name')]

                if not publisher_names or self.publisher_name not in publisher_names:
                    continue

                page_count = product.get('custom_attributes', {}).get('page_count', 0)
                if not page_count or int(page_count) < 200:
                    logger.debug(f"Skipping book with low page count ({page_count}): {product.get('title')}")
                    continue

                pub_date_str = product.get('custom_attributes', {}).get('publication_date')
                pub_date = None
                if pub_date_str:
                    try:
                        pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()

                        if pub_date < three_months_past or pub_date > one_month_future:
                            logger.debug(f"Skipping book with publication date out of range ({pub_date}): {product.get('title')}")
                            continue

                        logger.info(f"Found suitable book: {product.get('title')}, pages: {page_count}, date: {pub_date}")

                    except ValueError:
                        logger.warning(f"Invalid date format: {pub_date_str}")
                        continue
                else:
                    continue

                isbn = self.extract_isbn_from_url(product.get('url', ''))

                book_data = {
                    'title': product.get('title', ''),
                    'authors': ', '.join(product.get('authors', [])),
                    'isbn': isbn,
                    'url': product.get('url', ''),
                    'image_url': product.get('cover_image', ''),
                    'publisher': self.publisher,
                    'publication_date': datetime.combine(pub_date, datetime.min.time()).replace(tzinfo=timezone.utc) if pub_date else django_timezone.now(),
                    'description': product.get('description', ''),
                    'page_count': page_count
                }

                books.append(book_data)

                if len(books) >= limit:
                    break

            logger.info(f"Processed {processed_count} books from API, found {len(books)} suitable books")

        except Exception as e:
            logger.error(f"Error getting O'Reilly books via API: {e}")
            return self._try_rss_fallback(limit)

        return books[:limit]

    def save_books(self, books_data):
        new_books = []

        for book_data in books_data:
            isbn = book_data.get('isbn')

            if not isbn:
                logger.warning(f"Skipping book without ISBN: {book_data.get('title')}")
                continue

            existing_book = Book.objects.filter(isbn=isbn).first()

            if not existing_book:
                try:
                    book = Book(
                        title=book_data.get('title', ''),
                        author=book_data.get('authors', ''),
                        isbn=isbn,
                        publisher=self.publisher,
                        book_url=book_data.get('url', ''),
                        cover_url=book_data.get('image_url', ''),
                        description=book_data.get('description', ''),
                        publication_date=book_data.get('publication_date') or django_timezone.now().date(),
                        page_count=int(book_data.get('page_count', 0))
                    )
                    book.save()

                    logger.info(f"Added new book: {book.title}")
                    new_books.append(book)

                except Exception as e:
                    logger.error(f"Error saving book {book_data.get('title')}: {e}")
            else:
                logger.debug(f"Book already exists: {existing_book.title}")

        return new_books

    def _try_rss_fallback(self, limit):
        logger.info("Trying to get O'Reilly books via RSS")
        books = []

        try:
            current_date = datetime.now(timezone.utc).date()
            one_month_future = current_date.replace(month=current_date.month+1) if current_date.month < 12 else current_date.replace(year=current_date.year+1, month=1)
            three_months_past = current_date

            for _ in range(3):
                month = three_months_past.month - 1
                year = three_months_past.year
                if month == 0:
                    month = 12
                    year -= 1
                three_months_past = three_months_past.replace(year=year, month=month)

            logger.info(f"Looking for books published between {three_months_past} and {one_month_future}")

            rss_url = "https://www.oreilly.com/content/feed/"
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:limit*2]:
                link = entry.get('link', '')
                isbn = self.extract_isbn_from_url(link)

                if not isbn:
                    continue

                pub_date = None
                if 'published_parsed' in entry:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).date()

                    if pub_date < three_months_past or pub_date > one_month_future:
                        continue

                book_data = {
                    'title': entry.get('title', ''),
                    'authors': entry.get('author', ''),
                    'isbn': isbn,
                    'url': link,
                    'image_url': '',
                    'publisher': self.publisher,
                    'publication_date': datetime.combine(pub_date, datetime.min.time()).replace(tzinfo=timezone.utc) if pub_date else django_timezone.now(),
                    'description': entry.get('summary', '')
                }

                books.append(book_data)

                if len(books) >= limit:
                    break

            logger.info(f"Found {len(books)} O'Reilly books via RSS")

        except Exception as e:
            logger.error(f"Error getting O'Reilly books via RSS: {e}")

        return books


class ManningBookScraper:
    def __init__(self):
        self.base_url = "https://www.manning.com/catalog/sort/sort-by-date"
        self.publisher, _ = Publisher.objects.get_or_create(name="Manning Publications")

    def extract_isbn_from_url(self, url):
        return None

    def get_latest_books(self, limit=10):
        books = []

        try:
            response = requests.get(self.base_url, timeout=30)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch Manning books. Status code: {response.status_code}")
                return books

            soup = BeautifulSoup(response.text, 'html.parser')

            book_elements = soup.select('.book-item')

            for book_element in book_elements[:limit]:
                title_element = book_element.select_one('.book-title')
                if not title_element:
                    continue

                title = title_element.text.strip()

                url_element = book_element.select_one('a')
                url = url_element.get('href', '') if url_element else ''
                if url and not url.startswith('http'):
                    url = f"https://www.manning.com{url}"

                image_element = book_element.select_one('img')
                image_url = image_element.get('src', '') if image_element else ''
                if image_url and not image_url.startswith('http'):
                    image_url = f"https://www.manning.com{image_url}"

                authors_element = book_element.select_one('.book-authors')
                authors = authors_element.text.strip() if authors_element else ''

                book_data = {
                    'title': title,
                    'authors': authors,
                    'isbn': None,
                    'url': url,
                    'image_url': image_url,
                    'publisher': self.publisher,
                    'publication_date': django_timezone.now(),
                    'description': ''
                }

                books.append(book_data)

            logger.info(f"Found {len(books)} Manning books")

        except Exception as e:
            logger.error(f"Error fetching Manning books: {e}")

        return books


class PacktBookScraper:
    def __init__(self):
        self.base_url = "https://www.packtpub.com/all-books/all"
        self.publisher, _ = Publisher.objects.get_or_create(name="Packt Publishing")

    def extract_isbn_from_url(self, url):
        matches = re.findall(r'/(\d{13})$', url)
        if matches:
            return matches[0]
        return None

    def get_latest_books(self, limit=10):
        books = []

        try:
            response = requests.get(self.base_url, timeout=30)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch Packt books. Status code: {response.status_code}")
                return books

            soup = BeautifulSoup(response.text, 'html.parser')

            book_elements = soup.select('.product-item')

            for book_element in book_elements[:limit]:
                title_element = book_element.select_one('.product-item-link')
                if not title_element:
                    continue

                title = title_element.text.strip()
                url = title_element.get('href', '')

                isbn = self.extract_isbn_from_url(url)

                image_element = book_element.select_one('img')
                image_url = image_element.get('src', '') if image_element else ''

                pub_date_element = book_element.select_one('.publication-date')
                pub_date = None
                if pub_date_element:
                    pub_date_str = pub_date_element.text.strip()
                    try:
                        pub_date = datetime.strptime(pub_date_str, '%B %Y').replace(tzinfo=timezone.utc)
                    except ValueError:
                        logger.warning(f"Invalid date format: {pub_date_str}")

                authors_element = book_element.select_one('.authors')
                authors = authors_element.text.strip() if authors_element else ''

                book_data = {
                    'title': title,
                    'authors': authors,
                    'isbn': isbn,
                    'url': url,
                    'image_url': image_url,
                    'publisher': self.publisher,
                    'publication_date': pub_date,
                    'description': ''
                }

                books.append(book_data)

            logger.info(f"Found {len(books)} Packt books")

        except Exception as e:
            logger.error(f"Error fetching Packt books: {e}")

        return books


def get_scraper_for_publisher(publisher):
    scrapers = {
        "O'Reilly Media": OreillyBookScraper,
        "Manning Publications": ManningBookScraper,
        "Packt Publishing": PacktBookScraper,
    }

    scraper_class = scrapers.get(publisher.name)
    if scraper_class:
        return scraper_class()
    else:
        logger.warning(f"Scraper for publisher '{publisher.name}' not found")
        return None