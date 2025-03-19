from rest_framework import serializers
from .models import Publisher, Book


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for Publisher model"""
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description', 'website', 'logo_url']


class BookSerializer(serializers.ModelSerializer):
    """Serializer for Book model"""
    publisher_name = serializers.ReadOnlyField(source='publisher.name')

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'publisher', 'publisher_name',
            'description', 'cover_url', 'book_url', 'publication_date',
            'isbn', 'created_at'
        ]