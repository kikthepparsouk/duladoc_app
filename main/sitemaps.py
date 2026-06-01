"""
Sitemap configurations for SEO
https://docs.djangoproject.com/en/6.0/ref/contrib/sitemaps/
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from documents.models import Document
from category.models import Category


class StaticSitemap(Sitemap):
    """Static pages sitemap"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['home']

    def location(self, item):
        return reverse('home')


class DocumentSitemap(Sitemap):
    """Documents sitemap"""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Document.objects.filter(
            is_active=True
        ).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    """Categories sitemap"""
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Category.objects.filter(
            is_show_category=True
        ).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


# Sitemap dictionary for URL configuration
sitemaps = {
    'static': StaticSitemap,
    'documents': DocumentSitemap,
    'categories': CategorySitemap,
}
