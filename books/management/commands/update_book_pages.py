import json
import logging
from django.core.management.base import BaseCommand
from books.models import Book, Publisher
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Updates page count information for O\'Reilly books'

    def handle(self, *args, **options):
        self.stdout.write('Starting update of page count information for O\'Reilly books...')

        publisher = Publisher.objects.filter(name__contains="O'Reilly").first()
        if not publisher:
            self.stdout.write(self.style.ERROR('O\'Reilly publisher not found'))
            return

        books = Book.objects.filter(publisher=publisher, page_count=0)
        total_books = books.count()

        if total_books == 0:
            self.stdout.write(self.style.SUCCESS('No O\'Reilly books without page count information'))
            return

        self.stdout.write(f'Found {total_books} O\'Reilly books without page count information')

        try:
            with open('oreilly_api_response.json', 'r', encoding='utf-8') as f:
                api_data = json.load(f)

            if not api_data or 'data' not in api_data or 'products' not in api_data['data']:
                self.stdout.write(self.style.ERROR('No book data found in API response file'))
                return

            page_count_data = {}
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

                page_count = product.get('custom_attributes', {}).get('page_count', 0)
                if page_count:
                    page_count_data[isbn] = int(page_count)

            updated_count = 0
            for book in books:
                if book.isbn in page_count_data:
                    book.page_count = page_count_data[book.isbn]
                    book.save(update_fields=['page_count'])
                    self.stdout.write(f'Updated book "{book.title}": {book.page_count} pages')
                    updated_count += 1

            self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} of {total_books} books'))

            if updated_count < total_books:
                self.stdout.write(f'Remaining books to update: {total_books - updated_count}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating books: {e}'))

        remaining_books = Book.objects.filter(publisher=publisher, page_count=0).count()
        if remaining_books > 0:
            self.stdout.write(self.style.WARNING(f'Remaining {remaining_books} books without page count information'))
            Book.objects.filter(publisher=publisher, page_count=0).update(page_count=200)
            self.stdout.write('Default value of 200 pages set for remaining books')
        else:
            self.stdout.write(self.style.SUCCESS('All books have page count information'))