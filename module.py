"""
Services Module Configuration

Service management for salons, spas and service businesses.
"""
from django.utils.translation import gettext_lazy as _

MODULE_ID = "services"
MODULE_NAME = _("Services")
MODULE_ICON = "briefcase-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "pos"

MODULE_INDUSTRIES = ["beauty", "healthcare", "fitness", "consulting"]

MENU = {
    "label": _("Services"),
    "icon": "briefcase-outline",
    "order": 25,
    "show": True,
}

NAVIGATION = [
    {"id": "dashboard", "label": _("Overview"), "icon": "grid-outline", "view": ""},
    {"id": "services", "label": _("Services"), "icon": "briefcase-outline", "view": "services"},
    {"id": "categories", "label": _("Categories"), "icon": "folder-outline", "view": "categories"},
    {"id": "settings", "label": _("Settings"), "icon": "settings-outline", "view": "settings"},
]

DEPENDENCIES = []

SETTINGS = {
    "default_duration": 60,
    "show_duration": True,
    "allow_multiple_services": True,
}

PERMISSIONS = [
    ("view_service", _("Can view services")),
    ("add_service", _("Can add services")),
    ("change_service", _("Can change services")),
    ("delete_service", _("Can delete services")),
    ("view_category", _("Can view categories")),
    ("manage_category", _("Can manage categories")),
    ("view_settings", _("Can view settings")),
    ("change_settings", _("Can change settings")),
]

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "view_service", "add_service", "change_service", "delete_service",
        "view_category", "manage_category", "view_settings",
    ],
    "employee": ["view_service", "view_category"],
}
