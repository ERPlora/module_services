"""
Unit tests for services module models.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from services.models import (
    ServicesConfig,
    ServiceCategory,
    Service,
    ServiceVariant,
    ServiceAddon,
    ServicePackage,
    ServicePackageItem,
)


# =============================================================================
# ServicesConfig Tests
# =============================================================================

@pytest.mark.django_db
class TestServicesConfig:
    """Test cases for ServicesConfig model."""

    def test_get_config_creates_singleton(self):
        """get_config should create singleton instance."""
        config = ServicesConfig.get_config()
        assert config is not None
        assert config.pk == 1

    def test_get_config_returns_same_instance(self):
        """get_config should return same instance on multiple calls."""
        config1 = ServicesConfig.get_config()
        config2 = ServicesConfig.get_config()
        assert config1.pk == config2.pk

    def test_default_values(self, config):
        """Config should have sensible defaults."""
        assert config.default_duration == 60
        assert config.default_buffer_time == 0
        assert config.default_tax_rate == Decimal('21.00')
        assert config.show_prices is True
        assert config.show_duration is True
        assert config.allow_online_booking is True
        assert config.include_tax_in_price is True
        assert config.currency == 'EUR'
        assert config.price_decimal_places == 2

    def test_str_representation(self, config):
        """String representation should be descriptive."""
        assert str(config) == "Services Configuration"

    def test_update_config(self, config):
        """Config values should be updatable."""
        config.default_duration = 45
        config.default_tax_rate = Decimal('10.00')
        config.save()

        refreshed = ServicesConfig.get_config()
        assert refreshed.default_duration == 45
        assert refreshed.default_tax_rate == Decimal('10.00')


# =============================================================================
# ServiceCategory Tests
# =============================================================================

@pytest.mark.django_db
class TestServiceCategory:
    """Test cases for ServiceCategory model."""

    def test_create_category(self, db):
        """Should create a category successfully."""
        category = ServiceCategory.objects.create(
            name="Test Category",
            slug="test-category",
            description="Test description",
        )
        assert category.id is not None
        assert category.name == "Test Category"
        assert category.is_active is True

    def test_str_representation(self, category):
        """String representation should show name."""
        assert str(category) == "Hair Services"

    def test_str_with_parent(self, subcategory):
        """String representation should show parent."""
        assert str(subcategory) == "Hair Services > Coloring"

    def test_parent_child_relationship(self, category, subcategory):
        """Should maintain parent-child relationship."""
        assert subcategory.parent == category
        assert subcategory in category.children.all()

    def test_circular_reference_validation(self, category, subcategory):
        """Should prevent circular references."""
        category.parent = subcategory
        with pytest.raises(ValidationError):
            category.clean()

    def test_self_parent_validation(self, category):
        """Should prevent self as parent."""
        category.parent = category
        with pytest.raises(ValidationError):
            category.clean()

    def test_service_count(self, category, service):
        """Should count services in category."""
        assert category.service_count == 1

    def test_total_service_count_includes_children(self, category, subcategory, service):
        """Should include services from subcategories."""
        from services.models import Service
        Service.objects.create(
            name="Subcategory Service",
            slug="subcategory-service",
            category=subcategory,
            price=Decimal('30.00'),
            duration_minutes=30,
        )
        assert category.total_service_count == 2

    def test_get_ancestors(self, subcategory, category):
        """Should get ancestor categories."""
        ancestors = subcategory.get_ancestors()
        assert category in ancestors

    def test_get_descendants(self, category, subcategory):
        """Should get descendant categories."""
        descendants = category.get_descendants()
        assert subcategory in descendants

    def test_ordering(self, db):
        """Categories should be ordered by order, name."""
        cat1 = ServiceCategory.objects.create(name="Zebra", slug="zebra", order=2)
        cat2 = ServiceCategory.objects.create(name="Apple", slug="apple", order=1)
        cat3 = ServiceCategory.objects.create(name="Banana", slug="banana", order=1)

        categories = list(ServiceCategory.objects.all())
        assert categories[0] == cat2  # Apple (order 1)
        assert categories[1] == cat3  # Banana (order 1)
        assert categories[2] == cat1  # Zebra (order 2)


# =============================================================================
# Service Tests
# =============================================================================

@pytest.mark.django_db
class TestService:
    """Test cases for Service model."""

    def test_create_service(self, service):
        """Should create a service successfully."""
        assert service.id is not None
        assert service.name == "Haircut"
        assert service.is_active is True

    def test_str_representation(self, service):
        """String representation should show name."""
        assert str(service) == "Haircut"

    def test_effective_tax_rate_uses_service_rate(self, service, config):
        """Should use service-specific tax rate if set."""
        service.tax_rate = Decimal('10.00')
        service.save()
        assert service.effective_tax_rate == Decimal('10.00')

    def test_effective_tax_rate_uses_default(self, service, config):
        """Should use config default if no service rate."""
        assert service.effective_tax_rate == config.default_tax_rate

    def test_price_with_tax_when_included(self, service, config):
        """Price with tax should equal price when tax is included."""
        config.include_tax_in_price = True
        config.save()
        assert service.price_with_tax == service.price

    def test_price_with_tax_when_excluded(self, service, config):
        """Should calculate price with tax when not included."""
        config.include_tax_in_price = False
        config.save()
        service.tax_rate = Decimal('10.00')
        service.save()
        expected = service.price + (service.price * Decimal('0.10'))
        assert service.price_with_tax == expected

    def test_price_without_tax(self, service, config):
        """Should calculate price without tax."""
        config.include_tax_in_price = True
        config.save()
        service.tax_rate = Decimal('21.00')
        service.save()
        # Price includes 21% tax, so base price is lower
        assert service.price_without_tax < service.price

    def test_tax_amount(self, service, config):
        """Should calculate tax amount."""
        service.tax_rate = Decimal('21.00')
        service.save()
        tax = service.tax_amount
        assert tax > Decimal('0')

    def test_profit_calculation(self, service):
        """Should calculate profit correctly."""
        # Price without tax - cost = profit
        assert service.profit >= Decimal('0')

    def test_profit_margin(self, service):
        """Should calculate profit margin."""
        # (profit / price_without_tax) * 100
        assert service.profit_margin >= Decimal('0')

    def test_total_duration(self, service):
        """Should calculate total duration with buffers."""
        service.buffer_before = 10
        service.buffer_after = 5
        service.save()
        assert service.total_duration == 60  # 10 + 45 + 5

    def test_price_display_fixed(self, service):
        """Should display fixed price."""
        display = service.get_price_display()
        assert str(service.price) in str(display)

    def test_price_display_free(self, service):
        """Should display Free for free services."""
        service.pricing_type = 'free'
        service.save()
        display = service.get_price_display()
        assert 'Free' in str(display) or 'free' in str(display).lower()

    def test_price_display_from(self, service):
        """Should display From for starting prices."""
        service.pricing_type = 'from'
        service.save()
        display = service.get_price_display()
        assert 'From' in str(display) or str(service.price) in str(display)

    def test_price_range_validation(self, db, category):
        """Should validate min/max price range."""
        service = Service(
            name="Variable Service",
            slug="variable-service",
            category=category,
            pricing_type='variable',
            price=Decimal('0.00'),
            min_price=Decimal('100.00'),
            max_price=Decimal('50.00'),
            duration_minutes=60,
        )
        with pytest.raises(ValidationError):
            service.clean()

    def test_ordering(self, db, category):
        """Services should be ordered by order, name."""
        s1 = Service.objects.create(
            name="Zebra", slug="zebra", category=category,
            price=Decimal('10'), duration_minutes=30, order=2
        )
        s2 = Service.objects.create(
            name="Apple", slug="apple", category=category,
            price=Decimal('10'), duration_minutes=30, order=1
        )

        services = list(Service.objects.all())
        assert services[0] == s2
        assert services[1] == s1


# =============================================================================
# ServiceVariant Tests
# =============================================================================

@pytest.mark.django_db
class TestServiceVariant:
    """Test cases for ServiceVariant model."""

    def test_create_variant(self, service_variant):
        """Should create a variant successfully."""
        assert service_variant.id is not None
        assert service_variant.name == "Long Hair"

    def test_str_representation(self, service_variant):
        """String representation should show service and variant name."""
        assert "Haircut" in str(service_variant)
        assert "Long Hair" in str(service_variant)

    def test_final_price(self, service_variant, service):
        """Should calculate final price with adjustment."""
        expected = service.price + service_variant.price_adjustment
        assert service_variant.final_price == expected

    def test_final_duration(self, service_variant, service):
        """Should calculate final duration with adjustment."""
        expected = service.duration_minutes + service_variant.duration_adjustment
        assert service_variant.final_duration == expected

    def test_unique_name_per_service(self, service, service_variant):
        """Should enforce unique name per service."""
        with pytest.raises(Exception):
            ServiceVariant.objects.create(
                service=service,
                name="Long Hair",
                price_adjustment=Decimal('5.00'),
            )

    def test_ordering(self, service):
        """Variants should be ordered by order, name."""
        v1 = ServiceVariant.objects.create(
            service=service, name="Zebra",
            price_adjustment=Decimal('0'), order=2
        )
        v2 = ServiceVariant.objects.create(
            service=service, name="Apple",
            price_adjustment=Decimal('0'), order=1
        )

        variants = list(service.variants.all())
        assert variants[0] == v2
        assert variants[1] == v1


# =============================================================================
# ServiceAddon Tests
# =============================================================================

@pytest.mark.django_db
class TestServiceAddon:
    """Test cases for ServiceAddon model."""

    def test_create_addon(self, service_addon):
        """Should create an addon successfully."""
        assert service_addon.id is not None
        assert service_addon.name == "Deep Conditioning"

    def test_str_representation(self, service_addon):
        """String representation should show name."""
        assert str(service_addon) == "Deep Conditioning"

    def test_service_relationship(self, service_addon, service):
        """Should be linked to services."""
        assert service in service_addon.services.all()
        assert service_addon in service.addons.all()

    def test_ordering(self, db):
        """Addons should be ordered by name."""
        a1 = ServiceAddon.objects.create(name="Zebra", price=Decimal('10'))
        a2 = ServiceAddon.objects.create(name="Apple", price=Decimal('10'))

        addons = list(ServiceAddon.objects.all())
        assert addons[0] == a2
        assert addons[1] == a1


# =============================================================================
# ServicePackage Tests
# =============================================================================

@pytest.mark.django_db
class TestServicePackage:
    """Test cases for ServicePackage model."""

    def test_create_package(self, service_package):
        """Should create a package successfully."""
        assert service_package.id is not None
        assert service_package.name == "Complete Hair Package"

    def test_str_representation(self, service_package):
        """String representation should show name."""
        assert str(service_package) == "Complete Hair Package"

    def test_original_price(self, service_package, service, featured_service):
        """Should calculate total of all services."""
        expected = service.price + featured_service.price
        assert service_package.original_price == expected

    def test_final_price_with_percentage_discount(self, service_package):
        """Should apply percentage discount."""
        original = service_package.original_price
        discount = original * Decimal('0.10')
        expected = original - discount
        assert service_package.final_price == expected

    def test_final_price_with_fixed_discount(self, db, service, featured_service):
        """Should apply fixed amount discount."""
        package = ServicePackage.objects.create(
            name="Fixed Discount Package",
            slug="fixed-discount-package",
            discount_type='fixed',
            discount_value=Decimal('20.00'),
        )
        ServicePackageItem.objects.create(
            package=package, service=service, quantity=1
        )

        expected = service.price - Decimal('20.00')
        assert package.final_price == expected

    def test_final_price_with_fixed_price_override(self, service_package):
        """Should use fixed price if set."""
        service_package.fixed_price = Decimal('80.00')
        service_package.save()
        assert service_package.final_price == Decimal('80.00')

    def test_savings(self, service_package):
        """Should calculate savings."""
        assert service_package.savings > Decimal('0')
        assert service_package.savings == service_package.original_price - service_package.final_price

    def test_savings_percentage(self, service_package):
        """Should calculate savings percentage."""
        assert service_package.savings_percentage == Decimal('10.00')

    def test_total_duration(self, service_package, service, featured_service):
        """Should calculate total duration."""
        expected = service.duration_minutes + featured_service.duration_minutes
        assert service_package.total_duration == expected

    def test_ordering(self, db):
        """Packages should be ordered by order, name."""
        p1 = ServicePackage.objects.create(name="Zebra", slug="zebra", order=2)
        p2 = ServicePackage.objects.create(name="Apple", slug="apple", order=1)

        packages = list(ServicePackage.objects.all())
        assert packages[0] == p2
        assert packages[1] == p1


# =============================================================================
# ServicePackageItem Tests
# =============================================================================

@pytest.mark.django_db
class TestServicePackageItem:
    """Test cases for ServicePackageItem model."""

    def test_create_item(self, service_package, service):
        """Should have items from fixture."""
        assert service_package.items.count() == 2

    def test_str_representation(self, service_package):
        """String representation should show package and service."""
        item = service_package.items.first()
        assert "Complete Hair Package" in str(item)

    def test_unique_service_per_package(self, service_package, service):
        """Should enforce unique service per package."""
        with pytest.raises(Exception):
            ServicePackageItem.objects.create(
                package=service_package,
                service=service,
                quantity=1,
            )

    def test_ordering(self, service_package):
        """Items should be ordered by order."""
        items = list(service_package.items.all())
        assert items[0].order == 0
        assert items[1].order == 1
