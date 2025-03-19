import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from books.models import Book, Publisher

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Removes books that do not meet criteria (publication date and page count)'

    def handle(self, *args, **options):
        self.stdout.write('Starting removal of outdated books...')

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

        self.stdout.write(f'Checking books with publication date outside range {three_months_past} - {one_month_future} or with page count < 200')

        publishers = Publisher.objects.filter(name__contains="O'Reilly")
        if not publishers:
            self.stdout.write(self.style.WARNING('No publishers found with name containing O\'Reilly'))
            return

        self.stdout.write(f'Found {publishers.count()} publishers with name containing O\'Reilly:')
        for publisher in publishers:
            self.stdout.write(f'  • ID: {publisher.id}, Name: {publisher.name}')

        oreilly_books = Book.objects.filter(publisher__in=publishers)
        total_books = oreilly_books.count()

        if total_books == 0:
            self.stdout.write(self.style.WARNING('No O\'Reilly books found'))
            return

        self.stdout.write(f'Found {total_books} O\'Reilly books')

        deleted_date_count = 0
        deleted_pages_count = 0
        books_to_delete = []

        for book in oreilly_books:
            pub_date = book.publication_date
            if isinstance(pub_date, datetime):
                pub_date = pub_date.date()
            delete_reason = None

            if pub_date < three_months_past or pub_date > one_month_future:
                delete_reason = f"publication date ({pub_date}) outside range {three_months_past} - {one_month_future}"
                deleted_date_count += 1
                books_to_delete.append((book, delete_reason))
                continue

            if book.page_count < 200:
                delete_reason = f"page count ({book.page_count}) less than 200"
                deleted_pages_count += 1
                books_to_delete.append((book, delete_reason))
                continue

        if books_to_delete:
            self.stdout.write(self.style.WARNING(f'Will delete {len(books_to_delete)} books:'))
            for book, reason in books_to_delete:
                self.stdout.write(f'  • {book.title} - {book.author} - reason: {reason}')

            confirmation = input('Are you sure you want to delete these books? (y/n): ')
            if confirmation.lower() != 'y':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

            for book, _ in books_to_delete:
                book_title = book.title
                book.delete()
                self.stdout.write(f'Deleted book: {book_title}')

            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {len(books_to_delete)} books'))
            self.stdout.write(f'  - Due to date mismatch: {deleted_date_count}')
            self.stdout.write(f'  - Due to low page count: {deleted_pages_count}')
        else:
            self.stdout.write(self.style.SUCCESS('All books meet the criteria, no deletion required.'))