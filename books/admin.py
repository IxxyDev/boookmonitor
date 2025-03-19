from django.contrib import admin
from .models import Publisher, Book


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publisher', 'publication_date', 'created_at')
    list_filter = ('publisher', 'publication_date')
    search_fields = ('title', 'author', 'description')
    date_hierarchy = 'publication_date'
    readonly_fields = ('created_at',)
    list_per_page = 20
