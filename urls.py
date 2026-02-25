"""Services URL Configuration."""

from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),

    # Navigation tab aliases
    path('services/', views.service_list, name='services'),

    path('dashboard/', views.dashboard, name='dashboard'),

    # Services CRUD
    path('list/', views.service_list, name='list'),
    path('create/', views.service_create, name='create'),
    path('<uuid:pk>/', views.service_detail, name='detail'),
    path('<uuid:pk>/edit/', views.service_edit, name='edit'),
    path('<uuid:pk>/delete/', views.service_delete, name='delete'),
    path('<uuid:pk>/toggle/', views.service_toggle, name='toggle'),
    path('<uuid:pk>/duplicate/', views.service_duplicate, name='duplicate'),

    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<uuid:pk>/', views.category_detail, name='category_detail'),
    path('categories/<uuid:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<uuid:pk>/delete/', views.category_delete, name='category_delete'),

    # Variants
    path('<uuid:service_pk>/variants/add/', views.variant_add, name='variant_add'),
    path('variants/<uuid:pk>/edit/', views.variant_edit, name='variant_edit'),
    path('variants/<uuid:pk>/delete/', views.variant_delete, name='variant_delete'),

    # Addons
    path('addons/', views.addon_list, name='addon_list'),
    path('addons/add/', views.addon_add, name='addon_add'),
    path('addons/<uuid:pk>/edit/', views.addon_edit, name='addon_edit'),
    path('addons/<uuid:pk>/delete/', views.addon_delete, name='addon_delete'),

    # Packages
    path('packages/', views.package_list, name='package_list'),
    path('packages/add/', views.package_add, name='package_add'),
    path('packages/<uuid:pk>/', views.package_detail, name='package_detail'),
    path('packages/<uuid:pk>/edit/', views.package_edit, name='package_edit'),
    path('packages/<uuid:pk>/delete/', views.package_delete, name='package_delete'),

    # API
    path('api/search/', views.api_search, name='api_search'),
    path('api/services/', views.api_services_list, name='api_services'),
    path('api/services/<uuid:pk>/', views.api_service_detail, name='api_service_detail'),

    # Settings
    path('settings/', views.settings, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
    path('settings/toggle/', views.settings_toggle, name='settings_toggle'),
    path('settings/input/', views.settings_input, name='settings_input'),
    path('settings/reset/', views.settings_reset, name='settings_reset'),
]
