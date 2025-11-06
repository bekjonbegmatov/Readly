from django.contrib import admin
from .models import Article, Tag, Comment, Like


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    search_fields = ("title", "content")
    list_filter = ("created_at",)


admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(Like)