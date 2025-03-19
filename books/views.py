from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Publisher, Book
from .serializers import PublisherSerializer, BookSerializer
from .tasks import update_books_for_publisher
from django.db import models
from django.db.models import Count


class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

    @action(detail=True, methods=['post'])
    def update_books(self, request, pk=None):
        publisher = self.get_object()
        task = update_books_for_publisher.delay(publisher.id)
        return Response({'status': 'Task started', 'task_id': str(task.id)})


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('-publication_date')
    serializer_class = BookSerializer


class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def get_queryset(self):
        queryset = Book.objects.all().order_by('-publication_date')

        publisher_id = self.request.GET.get('publisher')
        if publisher_id:
            queryset = queryset.filter(publisher_id=publisher_id)

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['publishers'] = Publisher.objects.annotate(book_count=Count('books'))

        publisher_id = self.request.GET.get('publisher')
        if publisher_id:
            selected_publisher = Publisher.objects.filter(id=publisher_id).first()
            context['selected_publisher'] = selected_publisher

        search_query = self.request.GET.get('q')
        if search_query:
            context['search_query'] = search_query

        return context


class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'


class OreillyBooksView(ListView):
    model = Book
    template_name = 'books/oreilly_books.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        try:
            oreilly = Publisher.objects.get(name="O'Reilly Media")
            queryset = Book.objects.filter(publisher=oreilly).order_by('-publication_date')

            search_query = self.request.GET.get('q')
            if search_query:
                queryset = queryset.filter(
                    models.Q(title__icontains=search_query) |
                    models.Q(author__icontains=search_query) |
                    models.Q(description__icontains=search_query)
                )

            return queryset
        except Publisher.DoesNotExist:
            return Book.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['publishers'] = Publisher.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        try:
            context['oreilly'] = Publisher.objects.get(name="O'Reilly Media")
        except Publisher.DoesNotExist:
            pass
        return context


class PublisherListView(ListView):
    model = Publisher
    template_name = 'books/publisher_list.html'
    context_object_name = 'publishers'

    def get_queryset(self):
        return Publisher.objects.annotate(book_count=Count('books')).order_by('name')


class OreillySummaryView(ListView):
    template_name = 'books/oreilly_summary.html'
    context_object_name = 'books'

    def get_queryset(self):
        return Book.objects.filter(publisher__name__contains="O'Reilly").order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['publishers'] = Publisher.objects.filter(name__contains="O'Reilly")
        return context
