import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmonitor.settings')

app = Celery('bookmonitor')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-all-books-daily': {
        'task': 'books.tasks.update_all_publishers_books',
        'schedule': crontab(hour=7, minute=30),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
