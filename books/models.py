from django.db import models
from django.utils import timezone


class Publisher(models.Model):
    """Model for storing publisher information"""
    name = models.CharField(max_length=100, verbose_name="Publisher name")
    description = models.TextField(blank=True, verbose_name="Publisher description")
    website = models.URLField(blank=True, verbose_name="Website")
    logo_url = models.URLField(blank=True, verbose_name="Logo URL")

    class Meta:
        verbose_name = "Publisher"
        verbose_name_plural = "Publishers"
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """Model for storing book information"""
    title = models.CharField(max_length=255, verbose_name="Book title")
    author = models.CharField(max_length=255, verbose_name="Author")
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books", verbose_name="Publisher")
    description = models.TextField(blank=True, verbose_name="Book description")
    cover_url = models.URLField(blank=True, verbose_name="Cover URL")
    book_url = models.URLField(verbose_name="Book URL on publisher website")
    publication_date = models.DateField(verbose_name="Publication date")
    isbn = models.CharField(max_length=20, blank=True, verbose_name="ISBN")
    page_count = models.PositiveIntegerField(default=0, blank=True, verbose_name="Page count")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date added to system")

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['-publication_date']
        indexes = [
            models.Index(fields=['-publication_date']),
            models.Index(fields=['publisher', '-publication_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.author}"
