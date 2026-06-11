from django.contrib import admin
from .models import Document, WorkDocument,CategoryJobDocument
from .models import NewsFlash
from django.core.exceptions import ValidationError
from .models import HeroSlider
from .models import Banner, SmallBanner
from .models import ContactMessage


# @admin.register(Document)
# class DocumentAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'title', 
#         'preview_count',
#         'downloads',
#         'seller', 
#         'category', 
#         'price', 
#         'is_active', 
#         'is_featured_book', 
#         'is_popular_book', 
#         'is_new_book', 
#         'created_at'
#     )
#     list_filter = ('is_active', )
#     list_editable = ('preview_count', 'downloads','is_active','is_featured_book', 'is_popular_book', 'is_new_book')
#     readonly_fields = ['preview_count', 'downloads']
#     search_fields = ('title', 'description', 'seller__username')
    
#     def save_model(self, request, obj, form, change):
#         if obj.file:
#             ext = obj.file.name.split('.')[-1].lower()
#             if ext not in ['pdf', 'doc', 'docx', 'ppt', 'txt', 'pptx', 'pot', 'potx','xls','xlsx', 'pps', 'ppsx']:
#                 raise ValidationError('Only PDF, DOC, DOCX, PPT, TXT, PPTX, POT, POTX, XLS, XLSX, PPS or PPSX files are allowed.')
#         super().save_model(request, obj, form, change)
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title', 
        'preview_count',
        'file',
        'downloads',
        'seller', 
        'category', 
        'price', 
        'is_active', 
        'is_featured_book', 
        'is_popular_book', 
        'is_new_book', 
        'created_at'
    )
    list_filter = ('is_active',)
    list_editable = ('is_active', 'is_featured_book', 'is_popular_book', 'is_new_book')  # ✅ removed preview_count & downloads
    readonly_fields = ['preview_count', 'downloads']
    search_fields = ('title', 'description', 'seller__username')

    # def save_model(self, request, obj, form, change):
    #     if obj.file:
    #         ext = obj.file.name.split('.')[-1].lower()
    #         if ext not in ['pdf', 'doc', 'docx', 'ppt', 'txt', 'pptx', 'pot', 'potx', 'xls', 'xlsx', 'pps', 'ppsx','pub']:
    #             raise ValidationError('Only PDF, DOC, DOCX, PPT, TXT, PPTX, POT, POTX, XLS, XLSX, PPS or PPSX files are allowed.')
    #     super().save_model(request, obj, form, change)
 

@admin.register(HeroSlider)
class HeroSliderAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    list_editable = ('is_active',)
    search_fields = ("title", "subtitle")




@admin.register(NewsFlash)
class NewsFlashAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    
    
    

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    
    
    
@admin.register(SmallBanner)
class SmallBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle_one', 'subtitle_two', 'is_active')
    

@admin.register(WorkDocument)
class WorkDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'category', 'job_type', 'budget', 'posted_date', 'deadline', 'contact_info')    


@admin.register(CategoryJobDocument)
class CategoryJobDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    
    
    


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = [
        'name',
        'email',
        'subject',
        'created_at'
    ]

    search_fields = [
        'name',
        'email',
        'subject'
    ]