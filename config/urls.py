from django.contrib import admin
from django.urls import path, include
from hotel_app import views
from django.contrib.auth import views as auth_views
from hotel_app.views import logout_view  # custom logout view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomeView.as_view(), name='home'),

    # Voucher management
    path("vouchers/validate/", views.validate_voucher, name="validate_voucher"),

    # API
    path('api/', include('hotel_app.api_urls')),  # Updated API URL
    path('api-gui/', views.api_gui_view, name='api_gui'),  # New API GUI view

    # Screens
    path('master-user/', views.MasterUserView.as_view(), name='master_user'),
    path('master-location/', views.MasterLocationView.as_view(), name='master_location'),
    path('hotel-dashboard/', views.HotelDashboardView.as_view(), name='hotel_dashboard'),
    # path('breakfast-vouchers/', views.BreakfastVoucherView.as_view(), name='breakfast_vouchers'),
    path('api/bulk-delete-users/', views.bulk_delete_users, name='bulk_delete_users'),
    path('export-users/', views.export_users_csv, name='export_users'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),

    # Dashboard
    path('dashboard/', include('hotel_app.dashboard_urls', namespace='dashboard')),
    
]
