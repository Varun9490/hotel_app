from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import (
    UserViewSet, DepartmentViewSet, UserGroupViewSet,
    LocationViewSet, ComplaintViewSet, BreakfastVoucherViewSet, ReviewViewSet,
    DashboardViewSet, CustomAuthToken, GuestViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'user-groups', UserGroupViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'complaints', ComplaintViewSet)
router.register(r'vouchers', BreakfastVoucherViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'guests', GuestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomAuthToken.as_view()),

    # Voucher management
    path("issue-voucher/<int:guest_id>/", views.issue_voucher, name="issue_voucher"),
    path("issue-voucher/", views.issue_voucher_list, name="issue_voucher_list"),

    # API endpoint (POST only)
    path("scan-voucher/", views.scan_voucher, name="scan_voucher_api"),

    # Page for scanning UI
    path("scan-voucher-page/", views.scan_voucher_page, name="scan_voucher_page"),

    # Report page
    path("voucher-report/", views.voucher_report, name="voucher_report"),

    
]
