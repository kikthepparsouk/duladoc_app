from category.models import Category
from django.core.cache import cache

def categories_processor(request):
    # Try to get from cache first (1 hour TTL)
    cache_key_menu = 'categories_menu_cached'
    cache_key_all = 'categories_all_cached'
    
    categories_menu = cache.get(cache_key_menu)
    categories = cache.get(cache_key_all)
    
    if categories_menu is None:
        categories_menu = Category.objects.filter(
            parent__isnull=True
        ).prefetch_related('children__children')
        cache.set(cache_key_menu, categories_menu, 3600)
    
    if categories is None:
        categories = Category.objects.filter(parent__isnull=True)
        cache.set(cache_key_all, categories, 3600)
    
    return {
        'categories_menu': categories_menu,
        'categories': categories,
    }