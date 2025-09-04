# hotel_app/urls_api.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hotel_app import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()

# 1. Authentication & User Management
router.register(r'users', views.UserViewSet, basename='user')

# 2. Department Management
router.register(r'departments', views.DepartmentViewSet, basename='department')

# 3. User Groups
router.register(r'user-groups', views.UserGroupViewSet, basename='usergroup')

# 4. Master Location
router.register(r'locations', views.LocationViewSet, basename='location')

# 5. Complaints (Service Requests)
router.register(r'complaints', views.ServiceRequestViewSet, basename='complaint')

# 6. Food Vouchers
router.register(r'vouchers', views.BreakfastVoucherViewSet, basename='voucher')

# 7. Guest Reviews
router.register(r'reviews', views.GuestCommentViewSet, basename='review')


urlpatterns = [
    # Router-based endpoints
    path('', include(router.urls)),

    # 1. Authentication
    # (use DRF SimpleJWT or your own custom view)
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    # 8. Dashboards
    path('dashboard/overview/', views.DashboardOverview.as_view(), name='dashboard-overview'),
    path('dashboard/complaints/', views.DashboardComplaints.as_view(), name='dashboard-complaints'),
    path('dashboard/reviews/', views.DashboardReviews.as_view(), name='dashboard-reviews'),
    path("issue-voucher/<int:guest_id>/", views.issue_voucher, name="issue_voucher"),
    path("scan-voucher/<uuid:code>/", views.scan_voucher, name="scan_voucher"),
    path("voucher-report/", views.voucher_report, name="voucher_report"),
]
