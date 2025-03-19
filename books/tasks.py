import logging
from celery import shared_task
from .models import Publisher
from .scrapers import get_scraper_for_publisher

logger = logging.getLogger(__name__)


@shared_task
def update_books_for_publisher(publisher_id):
    try:
        publisher = Publisher.objects.get(id=publisher_id)
        scraper = get_scraper_for_publisher(publisher)

        if scraper:
            books_data = scraper.get_latest_books(limit=20)
            new_books = scraper.save_books(books_data)
            logger.info(f"Added {len(new_books)} new books from {publisher.name}")
            return len(new_books)
        else:
            logger.warning(f"Scraper for publisher {publisher.name} not found")
            return 0
    except Publisher.DoesNotExist:
        logger.error(f"Publisher with ID {publisher_id} not found")
        return 0
    except Exception as e:
        logger.error(f"Error updating books: {str(e)}")
        return 0


@shared_task
def update_all_publishers_books():
    publishers = Publisher.objects.all()
    total_new_books = 0

    for publisher in publishers:
        result = update_books_for_publisher.delay(publisher.id)

    logger.info(f"Book update started for {len(publishers)} publishers")
    return total_new_books