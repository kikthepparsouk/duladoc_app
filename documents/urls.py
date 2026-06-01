from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.homepage, name="home"),
    path('category/document/<int:id>/', views.doc_by_category, name='doc_by_category'),
    path('document/upload/', views.upload_document, name='upload_document'),
    # URL สำหรับ iframe preview PDF
    path('preview/<int:pk>/', views.preview_document, name='preview_document'),

    # URL สำหรับหน้า detail ที่มี iframe แสดง PDF
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    
    path('ajax/load-subcategories/', views.load_subcategories, name='ajax_load_subcategories'),
    
    path('all_documents/', views.all_documents, name='all_documents'),
    path('all_jobs_documents/', views.all_jobs_documents, name='all_jobs_documents'),
    
    
    
    # Create new job
    path('job/create/', views.WorkDocumentCreateView, name='workdocument_create'),
    path('contact/', views.Contact, name='contact'),
    
    path('dashboard/', views.wallet_home, name='wallet_home'),
    
    path('search/', views.search_documents, name='search_documents'),
    
    
    path('protected/documents/<path:path>', views.protected_document_file,  name='protected_document_file'),
    path('documents/<int:doc_id>/download-attached/', views.download_attached_file, name='download_attached_file'),
    
    


    
]
