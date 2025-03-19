from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, PublisherViewSet, BookListView, PublisherListView, OreillySummaryView

app_name = 'books'

router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'publishers', PublisherViewSet)

urlpatterns = [
    path('api/', include(router.urls)),

    path('', BookListView.as_view(), name='book_list'),
    path('publishers/', PublisherListView.as_view(), name='publisher_list'),
    path('oreilly/', OreillySummaryView.as_view(), name='oreilly_summary'),
]