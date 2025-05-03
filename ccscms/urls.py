from django.urls import path
from .views import (
    AuthView, logout_view, admin_dashboard,
    client_lpage, get_dashboard_data, EventListView, EventCreateView, 
    EventUpdateView, EventDeleteView, get_event_form_data,
    EventRestoreView, EventPermanentDeleteView,
    manage_labels, manage_types, manage_audiences,
    ajax_labels, ajax_types, ajax_audiences,
    ajax_create_category, ajax_update_category, ajax_delete_category, 
    categories_management, post_list, post_create, post_update, 
    post_delete, post_detail, post_form_data,  announcement_list, announcement_create, announcement_update,
    announcement_detail_admin, announcement_delete, announcement_restore,
    announcement_permanent_delete, announcement_form_data, achievement_list, achievement_form_data, achievement_detail,
    achievement_create, achievement_update, achievement_delete,
    achievement_image_delete, client_views, logout_view,  accomplishment_list, accomplishment_create, accomplishment_update,
    accomplishment_delete, accomplishment_detail, accomplishment_form_data,
    accomplishment_image_delete, account_list, account_create, account_update,
    account_delete, account_detail, account_form_data,
)

urlpatterns = [
    # Public routes
    path('', client_views.landing_page, name='landing_page'),
    path('auth/', AuthView.as_view(), name='auth'),
    path('logout/', logout_view, name='logout'),
    path('', client_views.landing_page, name='landing_page'),
    path('posts/', client_views.post_list, name='posts_list'),
    path('posts/<int:pk>/', client_views.post_detail, name='posts_detail'),
    path('announcements/', client_views.announcement_list, name='announcements_list'),
    path('announcements/<int:pk>/', client_views.announcement_detail, name='announcement_detail'),
    path('events/', client_views.events_list, name='events_list'),
    path('events/<int:event_id>/', client_views.event_detail, name='event_detail'),
    path('achievements/<int:pk>/', client_views.achievement_detail, name='achievement_detail'),
    path('officers/', client_views.officers_list, name='officers_list'),
    path('about/', client_views.about_page, name='about_page'),
    path('contact/', client_views.contact_page, name='contact_page'),
    path('contact/', client_views.contact_page, name='feedback'),#testing

    
    # Admin routes
    path('cscadmin/', admin_dashboard, name='admin_dashboard'),
    path('cscadmin/dashboard/data/', get_dashboard_data, name='dashboard_data'),
    
    # Admin - Page templates (for AJAX loading)
    path('cscadmin/dashboard/', admin_dashboard, name='dashboard_template'),
    path('cscadmin/posts/', admin_dashboard, name='posts_template'),
    path('cscadmin/events/', admin_dashboard, name='events_template'),
    path('cscadmin/announcements/', admin_dashboard, name='announcements_template'),
    path('cscadmin/complaints/', admin_dashboard, name='complaints_template'),
    path('cscadmin/achievements/', admin_dashboard, name='achievements_template'),
    path('cscadmin/accomplishments/', admin_dashboard, name='accomplishments_template'),
    path('cscadmin/volunteers/', admin_dashboard, name='volunteers_template'),
    path('cscadmin/settings/', admin_dashboard, name='settings_template'),
    
    # Admin - Event Management (AJAX endpoints)
    path('cscadmin/events/list/', EventListView.as_view(), name='event_list_data'),
    path('cscadmin/events/create/', EventCreateView.as_view(), name='event_create'),
    path('cscadmin/events/<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('cscadmin/events/<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),
    path('cscadmin/events/form/', admin_dashboard, name='event_form_template'),
    path('cscadmin/events/form-data/', get_event_form_data, name='event_form_data'),
    path('events/<int:pk>/restore/', EventRestoreView.as_view(), name='event_restore'),
    path('events/<int:pk>/permanent-delete/', EventPermanentDeleteView.as_view(), name='event_permanent_delete'),
    
    # Categories Management
    path('cscadmin/categories/', categories_management, name='categories_management'),   
    path('cscadmin/categories/labels/', manage_labels, name='manage_labels'),
    path('cscadmin/categories/types/', manage_types, name='manage_types'),
    path('cscadmin/categories/audiences/', manage_audiences, name='manage_audiences'),
    
    # AJAX endpoints for categories
    path('ajax/categories/labels/', ajax_labels, name='ajax_labels'),
    path('ajax/categories/types/', ajax_types, name='ajax_types'),
    path('ajax/categories/audiences/', ajax_audiences, name='ajax_audiences'),
    path('ajax/categories/create/', ajax_create_category, name='ajax_create_category'),
    path('ajax/categories/update/', ajax_update_category, name='ajax_update_category'),
    path('ajax/categories/delete/', ajax_delete_category, name='ajax_delete_category'),
    
      # Post management URLs
    path('cscadmin/posts/', post_list, name='post_list'),
    path('cscadmin/posts/create/', post_create, name='post_create'),
    path('cscadmin/posts/<int:pk>/update/', post_update, name='post_update'),
    path('cscadmin/posts/<int:pk>/delete/', post_delete, name='post_delete'),
    path('cscadmin/posts/<int:pk>/', post_detail, name='post_detail'),
    path('cscadmin/posts/form-data/', post_form_data, name='post_form_data'),
    path('cscadmin/posts/<int:pk>/detail/', post_detail, name='post_detail'),
    
    # Announcement management URLs
    path('cscadmin/announcements/list/', announcement_list, name='announcement_list'),
    path('cscadmin/announcements/create/', announcement_create, name='announcement_create'),
    path('cscadmin/announcements/<int:pk>/update/', announcement_update, name='announcement_update'),
    path('cscadmin/announcements/<int:pk>/detail/', announcement_detail_admin, name='announcement_detail_admin'),
    path('cscadmin/announcements/<int:pk>/delete/', announcement_delete, name='announcement_delete'),
    path('cscadmin/announcements/<int:pk>/restore/', announcement_restore, name='announcement_restore'),
    path('cscadmin/announcements/<int:pk>/permanent-delete/', announcement_permanent_delete, name='announcement_permanent_delete'),
    path('cscadmin/announcements/form-data/', announcement_form_data, name='announcement_form_data'),
    
    # Achievement URLs
    path('cscadmin/achievements/list/', achievement_list, name='achievement_list'),
    path('cscadmin/achievements/form-data/', achievement_form_data, name='achievement_form_data'),
    path('cscadmin/achievements/<int:pk>/detail/', achievement_detail, name='achievement_detail'),
    path('cscadmin/achievements/create/', achievement_create, name='achievement_create'),
    path('cscadmin/achievements/<int:pk>/update/', achievement_update, name='achievement_update'),
    path('cscadmin/achievements/<int:pk>/delete/', achievement_delete, name='achievement_delete'),
    path('cscadmin/achievement-images/<int:pk>/delete/', achievement_image_delete, name='achievement_image_delete'),
    
    #accomplishments URLs
    path('cscadmin/accomplishments/list/', accomplishment_list, name='accomplishment_list'),
    path('cscadmin/accomplishments/create/', accomplishment_create, name='accomplishment_create'),
    path('cscadmin/accomplishments/<int:pk>/update/', accomplishment_update, name='accomplishment_update'),
    path('cscadmin/accomplishments/<int:pk>/delete/', accomplishment_delete, name='accomplishment_delete'),
    path('cscadmin/accomplishments/<int:pk>/detail/', accomplishment_detail, name='accomplishment_detail'),
    path('cscadmin/accomplishments/form-data/', accomplishment_form_data, name='accomplishment_form_data'),
    path('cscadmin/accomplishment-images/<int:pk>/delete/', accomplishment_image_delete, name='accomplishment_image_delete'),
    
    #account
    path('cscadmin/accounts/list/', account_list, name='account_list'),
    path('cscadmin/accounts/create/', account_create, name='account_create'),
    path('cscadmin/accounts/<int:pk>/update/', account_update, name='account_update'),
    path('cscadmin/accounts/<int:pk>/delete/', account_delete, name='account_delete'),
    path('cscadmin/accounts/<int:pk>/detail/', account_detail, name='account_detail'),
    path('cscadmin/accounts/form-data/', account_form_data, name='account_form_data'),
    # Legacy client page (redirects to landing page)
    path('client/lpage/', client_lpage, name='client_lpage'),
]