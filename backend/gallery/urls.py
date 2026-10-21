from django.urls import path

from .views import (ArtworkDetailView, ArtworkListView, CategoryListView,
                    FavoriteDetailView, FavoriteListView)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('artworks/', ArtworkListView.as_view(), name='artwork-list'),
    path('artworks/<int:pk>/', ArtworkDetailView.as_view(), name='artwork-detail'),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/<int:artwork_id>/', FavoriteDetailView.as_view(), name='favorite-detail'),
]