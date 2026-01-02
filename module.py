"""
Services Module Configuration

This file defines the module metadata and navigation for the Services module.
Service catalog management for appointment-based businesses (salons, spas, etc.).
Used by the @module_view decorator to automatically render navigation tabs.
"""
from django.utils.translation import gettext_lazy as _

# Module Identification
MODULE_ID = "services"
MODULE_NAME = _("Services")
MODULE_ICON = "construct-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "pos"  # Changed from "services" to valid category

# Target Industries (business verticals this module is designed for)
MODULE_INDUSTRIES = [
    "beauty",       # Beauty & wellness (peluquerías, spas)
    "healthcare",   # Healthcare (clinics, medical)
    "fitness",      # Fitness & sports (gyms)
    "consulting",   # Professional services (consulting)
]

# Sidebar Menu Configuration
MENU = {
    "label": _("Services"),
    "icon": "construct-outline",
    "order": 25,
    "show": True,
}

# Internal Navigation (Tabs)
NAVIGATION = [
    {
        "id": "dashboard",
        "label": _("Overview"),
        "icon": "grid-outline",
        "view": "",
    },
    {
        "id": "list",
        "label": _("Catalog"),
        "icon": "list-outline",
        "view": "list",
    },
    {
        "id": "categories",
        "label": _("Categories"),
        "icon": "folder-outline",
        "view": "categories",
    },
    {
        "id": "settings",
        "label": _("Settings"),
        "icon": "settings-outline",
        "view": "settings",
    },
]

# Module Dependencies
DEPENDENCIES = ["appointments>=1.0.0"]

# Default Settings
SETTINGS = {
    "default_duration_minutes": 60,
    "show_prices": True,
    "require_staff": True,
}

# Permissions
PERMISSIONS = [
    "services.view_service",
    "services.add_service",
    "services.change_service",
    "services.delete_service",
    "services.view_category",
    "services.add_category",
    "services.change_category",
    "services.delete_category",
]
