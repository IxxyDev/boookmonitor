from django.core.management.base import BaseCommand
from books.models import Publisher
from books.scrapers import get_scraper_for_publisher
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update O\'Reilly Media books'

    def handle(self, *args, **options):
        try:
            publisher = Publisher.objects.get(name="O'Reilly Media")

            scraper = get_scraper_for_publisher(publisher)

            if scraper:
                self.stdout.write(self.style.SUCCESS(f'Starting update of {publisher.name} books...'))
                books_data = scraper.get_latest_books(limit=20)

                if books_data:
                    new_books = scraper.save_books(books_data)
                    self.stdout.write(self.style.SUCCESS(f'Added {len(new_books)} new {publisher.name} books'))

                    if new_books:
                        self.stdout.write('New books:')
                        for book in new_books:
                            self.stdout.write(f'  • {book.title} - {book.author}')
                    else:
                        self.stdout.write(self.style.WARNING('No new books found'))
                else:
                    self.stdout.write(self.style.WARNING('No book data found for update'))
            else:
                self.stdout.write(self.style.ERROR(f'Scraper for publisher {publisher.name} not found'))

        except Publisher.DoesNotExist:
            self.stdout.write(self.style.ERROR("Publisher O'Reilly Media not found in database"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))