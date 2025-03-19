import json
import logging
from django.core.management.base import BaseCommand
from books.models import Book, Publisher
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Updates information for existing O\'Reilly books, including page count'

    def handle(self, *args, **options):
        self.stdout.write('Starting update of existing O\'Reilly books information...')

        publishers = Publisher.objects.filter(name__contains="O'Reilly")
        if not publishers:
            self.stdout.write(self.style.ERROR('No publishers found with name O\'Reilly'))
            return

        books = Book.objects.filter(publisher__in=publishers)
        total_books = books.count()

        if total_books == 0:
            self.stdout.write(self.style.WARNING('No O\'Reilly books found'))
            return

        self.stdout.write(f'Found {total_books} O\'Reilly books')

        try:
            with open('oreilly_api_response.json', 'r', encoding='utf-8') as f:
                api_data = json.load(f)

            if not api_data or 'data' not in api_data or 'products' not in api_data['data']:
                self.stdout.write(self.style.ERROR('No book data found in API response file'))
                return

            books_data = {}
            for product in api_data['data']['products']:
                if product.get('type') != 'book':
                    continue

                isbn = None
                url = product.get('url', '')
                if url:
                    matches = re.findall(r'/(\d{13})/', url)
                    if matches:
                        isbn = matches[0]

                if not isbn:
                    continue

                books_data[isbn] = {
                    'title': product.get('title', ''),
                    'authors': ', '.join(product.get('authors', [])),
                    'description': product.get('description', ''),
                    'cover_url': product.get('cover_image', ''),
                    'page_count': int(product.get('custom_attributes', {}).get('page_count', 0))
                }

            updated_count = 0
            for book in books:
                if book.isbn in books_data:
                    book_data = books_data[book.isbn]

                    changed = False

                    if book.page_count != book_data['page_count'] and book_data['page_count'] > 0:
                        book.page_count = book_data['page_count']
                        changed = True

                    if changed:
                        book.save()
                        self.stdout.write(f'Updated book "{book.title}": {book.page_count} pages')
                        updated_count += 1

            self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} of {total_books} books'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating books: {e}'))
