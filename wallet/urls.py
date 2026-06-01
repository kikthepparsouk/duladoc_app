from django.urls import path
from . import views

# urlpatterns = [
#     # ─── ลูกค้า ───────────────────────────────────────────
#     path('wallet/dashboard', views.dashboard, name='dashboard'),
#     path('wallet/topup/', views.topup_request_view, name='topup_request'),
#     path('documents/', views.document_list, name='document_list'),
#     path('documents/<int:doc_id>/buy/', views.buy_document, name='buy_document'),
#     path('documents/<int:doc_id>/download/', views.download_document, name='download_document'),

#     # ─── Admin ────────────────────────────────────────────
#     path('staff/topups/', views.admin_topup_list, name='admin_topup_list'),
#     path('staff/topups/<int:pk>/', views.admin_topup_detail, name='admin_topup_detail'),
#     path('staff/topups/<int:pk>/action/', views.admin_topup_approve, name='admin_topup_approve'),
    
#     # ─── Seller ───────────────────────────────────────────
#     path('seller/',              views.seller_dashboard,     name='seller_dashboard'),
 
#     # ─── Admin ────────────────────────────────────────────
#     path('staff/revenue/',views.admin_revenue_dashboard, name='admin_revenue'),
# ]


urlpatterns = [
    # ─── ลูกค้า ───────────────────────────────────────────────
    path('wallet1/',                      views.dashboard,              name='dashboard'),
    path('wallet/topup/',                views.topup_request_view,     name='topup_request'),

    # ✅ URL เดียวจัดการทั้งซื้อ + ดาวน์โหลด
    path('wallet/buy/<int:doc_id>/',     views.buy_and_download,       name='buy_and_download'),
    
    path('wallet/withdraw/',                  views.withdraw_request_view,  name='withdraw_request'),   # ← ใหม่
    path('staff/withdraw/',                   views.admin_withdraw_list,    name='admin_withdraw_list'),     # ← ใหม่
    path('staff/withdraw/<int:pk>/action/',   views.admin_withdraw_approve, name='admin_withdraw_approve'),  # ← ใหม่


    # ✅ API ตรวจสอบสถานะก่อน Download (ใช้ใน JS)
    path('wallet/check/<int:doc_id>/',   views.check_download_status,  name='check_download_status'),

    # ─── Seller ───────────────────────────────────────────────
    path('seller/',                      views.seller_dashboard,       name='seller_dashboard'),
    
    path('my-documents/', views.My_documrnt, name='my-documents'),
    # path('documents/<int:doc_id>/update/', views.update_document, name='update_document'),
    path('my-documents/update/<int:doc_id>/', views.update_document, name='update_document'),
    path('my-documents/delete/<int:doc_id>/', views.delete_document, name='delete_document'),

    # ─── Admin ────────────────────────────────────────────────
    path('staff/topups/',                views.admin_topup_list,       name='admin_topup_list'),
    path('staff/topups/<int:pk>/',       views.admin_topup_detail,     name='admin_topup_detail'),
    path('staff/topups/<int:pk>/action/', views.admin_topup_approve,   name='admin_topup_approve'),
    path('staff/topups/<int:pk>/slip/',    views.admin_topup_slip,      name='admin_topup_slip'),
    path('staff/revenue/',               views.admin_revenue_dashboard, name='admin_revenue'),
]


