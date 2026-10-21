from django.contrib import admin

from .models import AIAnalysis, SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'category', 'used_ai', 'results_count', 'created_at')
    list_filter = ('used_ai',)


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'predicted_category', 'predicted_style', 'source', 'created_at')
    list_filter = ('source',)