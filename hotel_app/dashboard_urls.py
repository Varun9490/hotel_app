from django.urls import path
from django.urls import path
from . import dashboard_views
from . import views  # Import views for guest registration and voucher features

app_name = 'dashboard'   # ✅ Required for namespacing

urlpatterns = [
    path('', dashboard_views.dashboard_main, name='main'),
    path('users/', dashboard_views.dashboard_users, name='users'),
    path('departments/', dashboard_views.dashboard_departments, name='departments'),
    path('groups/', dashboard_views.dashboard_groups, name='groups'),
    path('locations/', dashboard_views.dashboard_locations, name='locations'),
    path('request-types/', dashboard_views.dashboard_request_types, name='request_types'),
    path('checklists/', dashboard_views.dashboard_checklists, name='checklists'),
    path('complaints/', dashboard_views.complaints, name='complaints'),
    path('breakfast-vouchers/', dashboard_views.breakfast_vouchers, name='breakfast_vouchers'),
    path('reviews/', dashboard_views.reviews, name='reviews'),
    # CRUD endpoints
    path('users/create/', dashboard_views.user_create, name='user_create'),
    path('users/<int:user_id>/update/', dashboard_views.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', dashboard_views.user_delete, name='user_delete'),
    path('departments/create/', dashboard_views.department_create, name='department_create'),
    path('departments/<int:dept_id>/update/', dashboard_views.department_update, name='department_update'),
    path('departments/<int:dept_id>/delete/', dashboard_views.department_delete, name='department_delete'),
    path('groups/create/', dashboard_views.group_create, name='group_create'),
    path('groups/<int:group_id>/update/', dashboard_views.group_update, name='group_update'),
    path('groups/<int:group_id>/delete/', dashboard_views.group_delete, name='group_delete'),
    path('locations/create/', dashboard_views.location_create, name='location_create'),
    path('locations/<int:loc_id>/update/', dashboard_views.location_update, name='location_update'),
    path('locations/<int:loc_id>/delete/', dashboard_views.location_delete, name='location_delete'),
    path('request-types/create/', dashboard_views.request_type_create, name='request_type_create'),
    path('request-types/<int:rt_id>/update/', dashboard_views.request_type_update, name='request_type_update'),
    path('request-types/<int:rt_id>/delete/', dashboard_views.request_type_delete, name='request_type_delete'),
    path('checklists/create/', dashboard_views.checklist_create, name='checklist_create'),
    path('checklists/<int:cl_id>/update/', dashboard_views.checklist_update, name='checklist_update'),
    path('checklists/<int:cl_id>/delete/', dashboard_views.checklist_delete, name='checklist_delete'),
    path('complaints/create/', dashboard_views.complaint_create, name='complaint_create'),
    path('complaints/<int:complaint_id>/update/', dashboard_views.complaint_update, name='complaint_update'),
    path('complaints/<int:complaint_id>/delete/', dashboard_views.complaint_delete, name='complaint_delete'),
    path('vouchers/create/', dashboard_views.voucher_create, name='voucher_create'),
    path('vouchers/<int:voucher_id>/update/', dashboard_views.voucher_update, name='voucher_update'),
    path('vouchers/<int:voucher_id>/delete/', dashboard_views.voucher_delete, name='voucher_delete'),
    path('reviews/create/', dashboard_views.review_create, name='review_create'),
    path('reviews/<int:review_id>/update/', dashboard_views.review_update, name='review_update'),
    path('reviews/<int:review_id>/delete/', dashboard_views.review_delete, name='review_delete'),
    
    # New Voucher System URLs
    path('register-guest/', views.register_guest, name='register_guest'),
    path('scan-voucher/', views.scan_voucher_page, name='scan_voucher'),
    path('voucher-analytics/', dashboard_views.voucher_analytics, name='voucher_analytics'),
    path('guests/', dashboard_views.dashboard_guests, name='guests'),
    path('guests/<int:guest_id>/', dashboard_views.guest_detail, name='guest_detail'),
    path('vouchers/', dashboard_views.dashboard_vouchers, name='vouchers'),
    path('vouchers/<int:voucher_id>/', dashboard_views.voucher_detail, name='voucher_detail'),
    
    # Guest QR Codes Management
    path('guest-qr-codes/', dashboard_views.guest_qr_codes, name='guest_qr_codes'),
    path('guest-qr-codes/<int:guest_id>/regenerate/', dashboard_views.regenerate_guest_qr, name='regenerate_guest_qr'),
    path('guest-qr-codes/<int:guest_id>/share-whatsapp/', dashboard_views.share_guest_qr_whatsapp, name='share_guest_qr_whatsapp'),
    path('guest-qr-codes/<int:guest_id>/whatsapp-message/', dashboard_views.get_guest_whatsapp_message, name='get_guest_whatsapp_message'),
    
    # Voucher QR Code Management
    path('vouchers/<int:voucher_id>/regenerate-qr/', dashboard_views.regenerate_voucher_qr, name='regenerate_voucher_qr'),
    path('vouchers/<int:voucher_id>/share-whatsapp/', dashboard_views.share_voucher_whatsapp, name='share_voucher_whatsapp'),
]
