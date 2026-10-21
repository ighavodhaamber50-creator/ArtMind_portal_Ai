from django.urls import path

from .artwork_views import MyArtworkDetailView, MyArtworksView, download_my_artwork
from .views import CsrfView, LoginView, LogoutView, MeView, RegisterView

urlpatterns = [
    path('auth/csrf/', CsrfView.as_view(), name='auth-csrf'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('my-artworks/', MyArtworksView.as_view(), name='my-artworks'),
    path('my-artworks/<int:pk>/', MyArtworkDetailView.as_view(), name='my-artwork-detail'),
    path('my-artworks/<int:pk>/download/<slug:kind>/', download_my_artwork, name='my-artwork-download'),
]