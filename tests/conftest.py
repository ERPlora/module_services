"""
Pytest configuration and fixtures for services module tests.
"""
import pytest
from decimal import Decimal
from django.utils.text import slugify


@pytest.fixture(autouse=True)
def disable_debug_toolbar(settings):
    """Disable debug toolbar for tests."""
    settings.DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda request: False}
    settings.DEBUG = False
    if hasattr(settings, 'INSTALLED_APPS'):
        settings.INSTALLED_APPS = [
            app for app in settings.INSTALLED_APPS if 'debug_toolbar' not in app
        ]
    if hasattr(settings, 'MIDDLEWARE'):
        settings.MIDDLEWARE = [
            m for m in settings.MIDDLEWARE if 'debug_toolbar' not in m
        ]


@pytest.fixture
def config(db):
    """Create default services configuration."""
    from services.models import ServicesConfig
    return ServicesConfig.get_config()


@pytest.fixture
def category(db):
    """Create a sample category."""
    from services.models import ServiceCategory
    return ServiceCategory.objects.create(
        name="Hair Services",
        slug="hair-services",
        description="All hair-related services",
        icon="cut-outline",
        color="#FF5733",
        order=1,
    )


@pytest.fixture
def subcategory(db, category):
    """Create a subcategory."""
    from services.models import ServiceCategory
    return ServiceCategory.objects.create(
        name="Coloring",
        slug="coloring",
        description="Hair coloring services",
        parent=category,
        order=1,
    )


@pytest.fixture
def service_data():
    """Sample service data."""
    return {
        'name': 'Haircut',
        'price': Decimal('25.00'),
        'duration_minutes': 45,
        'description': 'Professional haircut service',
        'short_description': 'Classic haircut',
        'cost': Decimal('5.00'),
        'is_bookable': True,
        'is_featured': False,
    }


@pytest.fixture
def service(db, category, service_data):
    """Create a sample service."""
    from services.models import Service
    return Service.objects.create(
        name=service_data['name'],
        slug=slugify(service_data['name']),
        description=service_data['description'],
        short_description=service_data['short_description'],
        category=category,
        price=service_data['price'],
        duration_minutes=service_data['duration_minutes'],
        cost=service_data['cost'],
        is_bookable=service_data['is_bookable'],
        is_featured=service_data['is_featured'],
    )


@pytest.fixture
def featured_service(db, category):
    """Create a featured service."""
    from services.models import Service
    return Service.objects.create(
        name="Premium Styling",
        slug="premium-styling",
        category=category,
        price=Decimal('75.00'),
        duration_minutes=90,
        is_featured=True,
    )


@pytest.fixture
def inactive_service(db, category):
    """Create an inactive service."""
    from services.models import Service
    return Service.objects.create(
        name="Discontinued Service",
        slug="discontinued-service",
        category=category,
        price=Decimal('50.00'),
        duration_minutes=60,
        is_active=False,
    )


@pytest.fixture
def service_variant(db, service):
    """Create a service variant."""
    from services.models import ServiceVariant
    return ServiceVariant.objects.create(
        service=service,
        name="Long Hair",
        description="For long hair",
        price_adjustment=Decimal('10.00'),
        duration_adjustment=15,
        order=1,
    )


@pytest.fixture
def service_addon(db, service):
    """Create a service addon."""
    from services.models import ServiceAddon
    addon = ServiceAddon.objects.create(
        name="Deep Conditioning",
        description="Intensive hair treatment",
        price=Decimal('15.00'),
        duration_minutes=20,
    )
    addon.services.add(service)
    return addon


@pytest.fixture
def service_package(db, service, featured_service):
    """Create a service package."""
    from services.models import ServicePackage, ServicePackageItem
    package = ServicePackage.objects.create(
        name="Complete Hair Package",
        slug="complete-hair-package",
        description="Everything you need",
        discount_type='percentage',
        discount_value=Decimal('10.00'),
        validity_days=30,
    )
    ServicePackageItem.objects.create(
        package=package,
        service=service,
        quantity=1,
        order=0,
    )
    ServicePackageItem.objects.create(
        package=package,
        service=featured_service,
        quantity=1,
        order=1,
    )
    return package


@pytest.fixture
def authenticated_session():
    """Create an authenticated session dictionary."""
    return {
        'local_user_id': 1,
        'is_authenticated': True,
    }


@pytest.fixture
def client_with_session(client, authenticated_session):
    """Create a Django test client with authenticated session."""
    session = client.session
    for key, value in authenticated_session.items():
        session[key] = value
    session.save()
    return client
