from django.db import models
from django.utils import timezone


class Publisher(models.Model):
    """Модель для хранения информации об издательствах"""
    name = models.CharField(max_length=100, verbose_name="Название издательства")
    description = models.TextField(blank=True, verbose_name="Описание издательства")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    logo_url = models.URLField(blank=True, verbose_name="URL логотипа")

    class Meta:
        verbose_name = "Издательство"
        verbose_name_plural = "Издательства"
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """Модель для хранения информации о книгах"""
    title = models.CharField(max_length=255, verbose_name="Название книги")
    author = models.CharField(max_length=255, verbose_name="Автор")
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books", verbose_name="Издательство")
    description = models.TextField(blank=True, verbose_name="Описание книги")
    cover_url = models.URLField(blank=True, verbose_name="URL обложки")
    book_url = models.URLField(verbose_name="URL книги на сайте издательства")
    publication_date = models.DateField(verbose_name="Дата публикации")
    isbn = models.CharField(max_length=20, blank=True, verbose_name="ISBN")
    page_count = models.PositiveIntegerField(default=0, blank=True, verbose_name="Количество страниц")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата добавления в систему")

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ['-publication_date']
        indexes = [
            models.Index(fields=['-publication_date']),
            models.Index(fields=['publisher', '-publication_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.author}"
