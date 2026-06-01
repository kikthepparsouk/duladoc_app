"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
# from django.urls import path, include
# from django.conf.urls.static import static
# from django.conf import settings
# from documents import views as document_views

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('auth/', include('authentication.urls')),
#     path('ckeditor/', include('ckeditor_uploader.urls')),
#     path('media/documents/<path:path>', document_views.protected_document_file, name='protected_document_file'),
#     path('media/attached_files/<path:path>', document_views.protected_attached_file, name='protected_attached_file'),
#     path('category/', include('category.urls')),
#     path('', include('documents.urls')),
#     path('', include('wallet.urls')),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urls.py

# urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
import os
from documents import views as document_views
from main.sitemaps import sitemaps

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('accounts/', include('authentication.urls')),  # ✅ หรือเพิ่มอันนี้ด้วย เพื่อให้ใช้ /accounts/activate/ ได้
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('category/', include('category.urls')),
    path('', include('documents.urls')),
    path('', include('wallet.urls')),
    path('protected/doc/<path:path>',      document_views.protected_document_file,  name='protected_document_file'),
    path('protected/attached/<path:path>', document_views.protected_attached_file,  name='protected_attached_file'),
    
    # SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    MEDIA = settings.MEDIA_ROOT  # อาจเป็น string หรือ Path

    # ✅ ใช้ os.path.join แทน / operator — รองรับทั้ง string และ Path
    urlpatterns += static('/media/preview_images/',  document_root=os.path.join(MEDIA, 'preview_images'))
    urlpatterns += static('/media/previews/',         document_root=os.path.join(MEDIA, 'previews'))
    urlpatterns += static('/media/slips/',            document_root=os.path.join(MEDIA, 'slips'))
    urlpatterns += static('/media/wallet/',           document_root=os.path.join(MEDIA, 'wallet'))
    urlpatterns += static('/media/withdraw_slips/',   document_root=os.path.join(MEDIA, 'withdraw_slips'))
    urlpatterns += static('/media/doc_thumbnails/',   document_root=os.path.join(MEDIA, 'doc_thumbnails'))
    urlpatterns += static('/media/imgs/',             document_root=os.path.join(MEDIA, 'imgs'))
    urlpatterns += static('/media/category_photos/',  document_root=os.path.join(MEDIA, 'category_photos'))
    # ตรวจว่ามีบรรทัดเหล่านี้ไหม
    urlpatterns += static('/media/withdraw_qrcodes/', document_root=os.path.join(MEDIA, 'withdraw_qrcodes'))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)