from django.contrib import admin

from .models import UserArtwork, UserPreference


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    filter_horizontal = ('favorite_categories',)


@admin.register(UserArtwork)
class UserArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'style', 'created_at')
    list_filter = ('category', 'style')
    search_fields = ('title', 'owner__username')
