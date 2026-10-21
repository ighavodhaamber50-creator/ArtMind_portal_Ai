from django.contrib import admin
from django.utils.html import format_html

from .models import Artist, Artwork, Category, Favorite, RecentlyViewed


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # slug fills itself in as you type the name


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality')
    search_fields = ('name',)


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'title', 'artist', 'category', 'style', 'medium', 'view_count')
    list_filter = ('category', 'style', 'medium', 'surface')
    search_fields = ('title', 'artist__name', 'description')
    readonly_fields = ('view_count', 'created_at')

    @admin.display(description='Image')
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;">', obj.image.url)
        return '-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'artwork', 'created_at')


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ('user', 'artwork', 'viewed_at')