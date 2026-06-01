# documents/admin.py
from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_popular_category','is_show_category')
    list_filter = ('is_popular_category',)
    list_editable = ('is_popular_category','is_show_category',)
    prepopulated_fields = {"slug": ("name",)}
