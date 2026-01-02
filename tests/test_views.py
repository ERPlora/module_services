"""
E2E tests for services module views.
Tests all CRUD operations and user interactions.
"""
import pytest
from decimal import Decimal

from services.models import (
    ServicesConfig,
    ServiceCategory,
    Service,
    ServiceVariant,
    ServiceAddon,
    ServicePackage,
)
from services.services import ServiceService


# =============================================================================
# Service CRUD Tests
# =============================================================================

@pytest.mark.django_db
class TestServiceCRUD:
    """Test service CRUD operations."""

    def test_create_service_success(self, category):
        """Should create service via service layer."""
        service, error = ServiceService.create_service(
            name='Test Service',
            price=Decimal('50.00'),
            duration_minutes=60,
            category_id=category.id,
            description='Test description',
            is_bookable=True,
        )

        assert error is None
        assert service is not None
        assert service.name == 'Test Service'
        assert service.is_active is True

    def test_update_service(self, service):
        """Should update service."""
        success, error = ServiceService.update_service(
            service,
            name='Updated Service',
            price=Decimal('75.00'),
        )

        assert success is True
        service.refresh_from_db()
        assert service.name == 'Updated Service'
        assert service.price == Decimal('75.00')

    def test_delete_service(self, service):
        """Should delete service."""
        service_id = service.id
        success, error = ServiceService.delete_service(service)

        assert success is True
        assert not Service.objects.filter(id=service_id).exists()

    def test_toggle_service_status(self, service):
        """Should toggle service active status."""
        assert service.is_active is True

        is_active = ServiceService.toggle_service_active(service)
        assert is_active is False

        service.refresh_from_db()
        assert service.is_active is False

    def test_duplicate_service(self, service, service_variant):
        """Should duplicate service with variants."""
        new_service, error = ServiceService.duplicate_service(service)

        assert error is None
        assert new_service.id != service.id
        assert 'Copy' in new_service.name
        assert new_service.variants.count() == 1


# =============================================================================
# Category Management Tests
# =============================================================================

@pytest.mark.django_db
class TestCategoryManagement:
    """Test category management."""

    def test_create_category(self):
        """Should create category."""
        category, error = ServiceService.create_category(
            name='New Category',
            description='Test category',
            icon='folder-outline',
        )

        assert error is None
        assert category is not None
        assert category.name == 'New Category'

    def test_create_subcategory(self, category):
        """Should create subcategory."""
        subcategory, error = ServiceService.create_category(
            name='Subcategory',
            parent_id=category.id,
        )

        assert error is None
        assert subcategory.parent == category

    def test_update_category(self, category):
        """Should update category."""
        success, error = ServiceService.update_category(
            category,
            name='Updated Category',
            color='#FF0000',
        )

        assert success is True
        category.refresh_from_db()
        assert category.name == 'Updated Category'

    def test_delete_category(self, subcategory):
        """Should delete category."""
        cat_id = subcategory.id
        success, error = ServiceService.delete_category(subcategory)

        assert success is True
        assert not ServiceCategory.objects.filter(id=cat_id).exists()

    def test_get_category_tree(self, category, subcategory):
        """Should get category tree."""
        tree = ServiceService.get_category_tree()

        assert len(tree) >= 1
        parent = next((n for n in tree if n['id'] == category.id), None)
        assert parent is not None


# =============================================================================
# Variant Tests
# =============================================================================

@pytest.mark.django_db
class TestVariantManagement:
    """Test variant management."""

    def test_create_variant(self, service):
        """Should create variant."""
        variant, error = ServiceService.create_variant(
            service=service,
            name='Extra Long',
            price_adjustment=Decimal('15.00'),
            duration_adjustment=20,
        )

        assert error is None
        assert variant is not None
        assert variant.final_price == service.price + Decimal('15.00')

    def test_update_variant(self, service_variant):
        """Should update variant."""
        success, error = ServiceService.update_variant(
            service_variant,
            price_adjustment=Decimal('20.00'),
        )

        assert success is True
        service_variant.refresh_from_db()
        assert service_variant.price_adjustment == Decimal('20.00')

    def test_delete_variant(self, service_variant):
        """Should delete variant."""
        variant_id = service_variant.id
        success, error = ServiceService.delete_variant(service_variant)

        assert success is True
        assert not ServiceVariant.objects.filter(id=variant_id).exists()


# =============================================================================
# Addon Tests
# =============================================================================

@pytest.mark.django_db
class TestAddonManagement:
    """Test addon management."""

    def test_create_addon(self, service):
        """Should create addon."""
        addon, error = ServiceService.create_addon(
            name='New Addon',
            price=Decimal('10.00'),
            duration_minutes=15,
            service_ids=[service.id],
        )

        assert error is None
        assert addon is not None
        assert service in addon.services.all()

    def test_update_addon(self, service_addon):
        """Should update addon."""
        success, error = ServiceService.update_addon(
            service_addon,
            price=Decimal('20.00'),
        )

        assert success is True
        service_addon.refresh_from_db()
        assert service_addon.price == Decimal('20.00')

    def test_delete_addon(self, service_addon):
        """Should delete addon."""
        addon_id = service_addon.id
        success, error = ServiceService.delete_addon(service_addon)

        assert success is True
        assert not ServiceAddon.objects.filter(id=addon_id).exists()


# =============================================================================
# Package Tests
# =============================================================================

@pytest.mark.django_db
class TestPackageManagement:
    """Test package management."""

    def test_create_package(self, service, featured_service):
        """Should create package."""
        package, error = ServiceService.create_package(
            name='Test Package',
            service_items=[
                {'service_id': service.id, 'quantity': 1},
                {'service_id': featured_service.id, 'quantity': 1},
            ],
            discount_type='percentage',
            discount_value=Decimal('10.00'),
        )

        assert error is None
        assert package is not None
        assert package.items.count() == 2

    def test_package_pricing(self, service_package, service, featured_service):
        """Should calculate package pricing correctly."""
        original = service.price + featured_service.price
        discount = original * Decimal('0.10')
        expected = original - discount

        assert service_package.original_price == original
        assert service_package.final_price == expected
        assert service_package.savings == discount

    def test_update_package(self, service_package):
        """Should update package."""
        success, error = ServiceService.update_package(
            service_package,
            discount_value=Decimal('20.00'),
        )

        assert success is True
        service_package.refresh_from_db()
        assert service_package.discount_value == Decimal('20.00')

    def test_delete_package(self, service_package):
        """Should delete package."""
        package_id = service_package.id
        success, error = ServiceService.delete_package(service_package)

        assert success is True
        assert not ServicePackage.objects.filter(id=package_id).exists()


# =============================================================================
# Search and Filter Tests
# =============================================================================

@pytest.mark.django_db
class TestSearchAndFilter:
    """Test search and filter functionality."""

    def test_search_by_name(self, service, featured_service):
        """Should search services by name."""
        results = ServiceService.search_services(query='Haircut')

        assert service in results
        assert featured_service not in results

    def test_filter_by_category(self, service, category):
        """Should filter by category."""
        results = ServiceService.search_services(category_id=category.id)

        assert service in results

    def test_filter_by_active_status(self, service, inactive_service):
        """Should filter by active status."""
        active = ServiceService.search_services(is_active=True)
        inactive = ServiceService.search_services(is_active=False)

        assert service in active
        assert inactive_service in inactive
        assert inactive_service not in active

    def test_filter_by_price_range(self, service, featured_service):
        """Should filter by price range."""
        results = ServiceService.search_services(
            min_price=Decimal('50.00'),
            max_price=Decimal('100.00'),
        )

        assert featured_service in results
        assert service not in results

    def test_get_featured_services(self, service, featured_service):
        """Should get featured services only."""
        results = ServiceService.get_featured_services()

        assert featured_service in results
        assert service not in results

    def test_get_bookable_services(self, service):
        """Should get bookable services."""
        results = ServiceService.get_bookable_services()

        assert service in results


# =============================================================================
# Statistics Tests
# =============================================================================

@pytest.mark.django_db
class TestStatistics:
    """Test statistics functionality."""

    def test_get_service_stats(self, service, featured_service, inactive_service, category):
        """Should get comprehensive statistics."""
        stats = ServiceService.get_service_stats()

        assert stats['total_services'] >= 3
        assert stats['active_services'] >= 2
        assert stats['inactive_services'] >= 1
        assert stats['featured_services'] >= 1
        assert stats['categories'] >= 1
        assert 'avg_price' in stats
        assert 'avg_duration' in stats

    def test_get_price_range(self, service, featured_service):
        """Should get price range."""
        price_range = ServiceService.get_price_range()

        assert price_range['min'] <= price_range['max']


# =============================================================================
# Settings Tests
# =============================================================================

@pytest.mark.django_db
class TestSettings:
    """Test settings management."""

    def test_get_config(self):
        """Should get config singleton."""
        config = ServicesConfig.get_config()
        assert config.pk == 1

    def test_update_settings(self, config):
        """Should update settings."""
        config.default_duration = 45
        config.default_tax_rate = Decimal('10.00')
        config.save()

        config.refresh_from_db()
        assert config.default_duration == 45
        assert config.default_tax_rate == Decimal('10.00')

    def test_toggle_boolean_setting(self, config):
        """Should toggle boolean settings."""
        original = config.show_prices
        config.show_prices = not original
        config.save()

        config.refresh_from_db()
        assert config.show_prices != original


# =============================================================================
# Integration Tests - Full Lifecycle
# =============================================================================

@pytest.mark.django_db
class TestFullLifecycle:
    """Integration tests for complete workflows."""

    def test_service_full_lifecycle(self, category):
        """Test complete service from creation to deletion."""
        # 1. Create category
        cat, _ = ServiceService.create_category(
            name='Test Category',
            description='For lifecycle test',
        )

        # 2. Create service
        service, _ = ServiceService.create_service(
            name='Lifecycle Service',
            price=Decimal('50.00'),
            duration_minutes=60,
            category_id=cat.id,
            is_bookable=True,
        )
        assert service is not None

        # 3. Add variant
        variant, _ = ServiceService.create_variant(
            service=service,
            name='Premium',
            price_adjustment=Decimal('25.00'),
            duration_adjustment=30,
        )
        assert variant is not None
        assert variant.final_price == Decimal('75.00')

        # 4. Create addon
        addon, _ = ServiceService.create_addon(
            name='Extra Treatment',
            price=Decimal('15.00'),
            duration_minutes=15,
            service_ids=[service.id],
        )
        assert addon is not None

        # 5. Update service
        success, _ = ServiceService.update_service(
            service,
            is_featured=True,
        )
        assert success is True
        service.refresh_from_db()
        assert service.is_featured is True

        # 6. Toggle active
        is_active = ServiceService.toggle_service_active(service)
        assert is_active is False

        # 7. Duplicate
        duplicate, _ = ServiceService.duplicate_service(service)
        assert duplicate is not None
        assert duplicate.variants.count() == 1

        # 8. Delete original
        success, _ = ServiceService.delete_service(service)
        assert success is True

    def test_package_with_multiple_services(self, category):
        """Test package creation with multiple services."""
        # Create services
        s1, _ = ServiceService.create_service(
            name='Service 1',
            price=Decimal('30.00'),
            duration_minutes=30,
            category_id=category.id,
        )
        s2, _ = ServiceService.create_service(
            name='Service 2',
            price=Decimal('50.00'),
            duration_minutes=45,
            category_id=category.id,
        )
        s3, _ = ServiceService.create_service(
            name='Service 3',
            price=Decimal('20.00'),
            duration_minutes=20,
            category_id=category.id,
        )

        # Create package
        package, _ = ServiceService.create_package(
            name='Complete Package',
            service_items=[
                {'service_id': s1.id, 'quantity': 1},
                {'service_id': s2.id, 'quantity': 2},
                {'service_id': s3.id, 'quantity': 1},
            ],
            discount_type='percentage',
            discount_value=Decimal('15.00'),
        )

        # Verify pricing
        # Original: 30 + (50*2) + 20 = 150
        # Discount: 150 * 0.15 = 22.50
        # Final: 150 - 22.50 = 127.50
        assert package.original_price == Decimal('150.00')
        assert package.final_price == Decimal('127.50')
        assert package.savings == Decimal('22.50')
        assert package.savings_percentage == Decimal('15.00')

        # Verify duration
        # 30 + (45*2) + 20 = 140
        assert package.total_duration == 140

    def test_category_hierarchy(self):
        """Test category hierarchy operations."""
        # Create hierarchy
        parent, _ = ServiceService.create_category(name='Parent')
        child1, _ = ServiceService.create_category(name='Child 1', parent_id=parent.id)
        child2, _ = ServiceService.create_category(name='Child 2', parent_id=parent.id)
        grandchild, _ = ServiceService.create_category(name='Grandchild', parent_id=child1.id)

        # Verify tree
        tree = ServiceService.get_category_tree()
        parent_node = next((n for n in tree if n['id'] == parent.id), None)

        assert parent_node is not None
        assert len(parent_node['children']) == 2

        # Verify ancestors
        ancestors = grandchild.get_ancestors()
        assert parent in ancestors
        assert child1 in ancestors

        # Verify descendants
        descendants = parent.get_descendants()
        assert child1 in descendants
        assert child2 in descendants
        assert grandchild in descendants
