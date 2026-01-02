from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Services List
    path('list/', views.service_list, name='list'),
    path('create/', views.service_create, name='create'),
    path('<int:pk>/', views.service_detail, name='detail'),
    path('<int:pk>/edit/', views.service_edit, name='edit'),
    path('<int:pk>/delete/', views.service_delete, name='delete'),
    path('<int:pk>/toggle/', views.service_toggle, name='toggle'),
    path('<int:pk>/duplicate/', views.service_duplicate, name='duplicate'),

    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Variants
    path('<int:service_pk>/variants/create/', views.variant_create, name='variant_create'),
    path('variants/<int:pk>/edit/', views.variant_edit, name='variant_edit'),
    path('variants/<int:pk>/delete/', views.variant_delete, name='variant_delete'),

    # Addons
    path('addons/', views.addon_list, name='addon_list'),
    path('addons/create/', views.addon_create, name='addon_create'),
    path('addons/<int:pk>/edit/', views.addon_edit, name='addon_edit'),
    path('addons/<int:pk>/delete/', views.addon_delete, name='addon_delete'),

    # Packages
    path('packages/', views.package_list, name='package_list'),
    path('packages/create/', views.package_create, name='package_create'),
    path('packages/<int:pk>/', views.package_detail, name='package_detail'),
    path('packages/<int:pk>/edit/', views.package_edit, name='package_edit'),
    path('packages/<int:pk>/delete/', views.package_delete, name='package_delete'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
    path('settings/toggle/', views.settings_toggle, name='settings_toggle'),

    # API endpoints
    path('api/search/', views.api_search, name='api_search'),
    path('api/services/', views.api_services_list, name='api_services'),
    path('api/services/<int:pk>/', views.api_service_detail, name='api_service_detail'),
]
