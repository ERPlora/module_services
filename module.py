from django.utils.translation import gettext_lazy as _

MODULE_ID = 'services'
MODULE_NAME = _('Services')
MODULE_VERSION = '1.0.0'

MENU = {
    'label': _('Services'),
    'icon': 'briefcase-outline',
    'order': 30,
}

NAVIGATION = [
    {'id': 'dashboard', 'label': _('Overview'), 'icon': 'grid-outline', 'view': ''},
    {'id': 'services', 'label': _('Services'), 'icon': 'briefcase-outline', 'view': 'list'},
    {'id': 'categories', 'label': _('Categories'), 'icon': 'folder-outline', 'view': 'categories'},
    {'id': 'packages', 'label': _('Packages'), 'icon': 'gift-outline', 'view': 'packages'},
    {'id': 'settings', 'label': _('Settings'), 'icon': 'settings-outline', 'view': 'settings'},
]

PERMISSIONS = [
    'services.view_service',
    'services.add_service',
    'services.change_service',
    'services.delete_service',
    'services.view_category',
    'services.add_category',
    'services.change_category',
    'services.delete_category',
    'services.view_package',
    'services.add_package',
    'services.change_package',
    'services.delete_package',
    'services.manage_settings',
]
