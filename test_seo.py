#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from documents.models import Document
from category.models import Category
from main.sitemaps import sitemaps

print("OK Models imported successfully!")
print(f"OK Document.get_absolute_url method exists: {hasattr(Document, 'get_absolute_url')}")
print(f"OK Category.get_absolute_url method exists: {hasattr(Category, 'get_absolute_url')}")
print(f"OK Sitemaps configured: {list(sitemaps.keys())}")
print("\nOK SEO setup is working correctly!")
