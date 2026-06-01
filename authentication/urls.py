# from django.urls import path
# from . import views
# from django.contrib.auth.views import LogoutView

# # app_name = "authentication"
# urlpatterns = [
#     path('login/', views.login_view, name="login_view"),
#     path('register/', views.register_user, name="register_user"),
#     path("logout/", views.logout, name="logout"),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name="login_view"),
    path('register/', views.register_user, name="register_user"),
    path('logout/', views.logout, name="logout"),
    path('activate/<str:token>/', views.activate_account, name="activate_account"),  # ✅ เพิ่มตรงนี้
]