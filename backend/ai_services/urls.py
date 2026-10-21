from django.urls import path

from .export_views import download_artwork
from .image_views import AnalyzeImageView
from .summary_views import ArtworkSummaryView
from .views import ChatView, DashboardView, RecommendationView, SearchView

urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('ai/chat/', ChatView.as_view(), name='ai-chat'),
    path('ai/analyze-image/', AnalyzeImageView.as_view(), name='ai-analyze-image'),
    path('artworks/<int:pk>/summary/', ArtworkSummaryView.as_view(), name='artwork-summary'),
    path('artworks/<int:pk>/download/<slug:kind>/', download_artwork, name='artwork-download'),
    path('recommendations/', RecommendationView.as_view(), name='recommendations'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]