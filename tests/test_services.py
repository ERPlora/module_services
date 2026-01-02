"""
Unit tests for services module service layer.
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
class TestServiceServiceCRUD:
    """Test service CRUD operations."""

    def test_create_service_success(self, category):
        """Should create service successfully."""
        service, error = ServiceService.create_service(
            name="New Service",
            price=Decimal('50.00'),
            duration_minutes=60,
            category_id=category.id,
            description="A new service",
        )

        assert error is None
        assert service is not None
        assert service.name == "New Service"
        assert service.slug == "new-service"
        assert service.price == Decimal('50.00')

    def test_create_service_generates_unique_slug(self, category):
        """Should generate unique slug on collision."""
        service1, _ = ServiceService.create_service(
            name="Haircut",
            price=Decimal('25.00'),
            duration_minutes=30,
        )
        service2, _ = ServiceService.create_service(
            name="Haircut",
            price=Decimal('30.00'),
            duration_minutes=45,
        )

        assert service1.slug == "haircut"
        assert service2.slug == "haircut-1"

    def test_create_service_empty_name_error(self):
        """Should return error for empty name."""
        service, error = ServiceService.create_service(
            name="",
            price=Decimal('25.00'),
            duration_minutes=30,
        )

        assert service is None
        assert "required" in error.lower()

    def test_create_service_invalid_category(self):
        """Should return error for invalid category."""
        service, error = ServiceService.create_service(
            name="Test Service",
            price=Decimal('25.00'),
            duration_minutes=30,
            category_id=9999,
        )

        assert service is None
        assert "not found" in error.lower()

    def test_create_service_invalid_price_range(self):
        """Should return error for invalid price range."""
        service, error = ServiceService.create_service(
            name="Variable Service",
            pricing_type='variable',
            min_price=Decimal('100.00'),
            max_price=Decimal('50.00'),
            duration_minutes=30,
        )

        assert service is None
        assert "minimum" in error.lower() or "cannot" in error.lower()

    def test_update_service_success(self, service):
        """Should update service successfully."""
        success, error = ServiceService.update_service(
            service,
            name="Updated Haircut",
            price=Decimal('30.00'),
        )

        assert success is True
        assert error is None
        service.refresh_from_db()
        assert service.name == "Updated Haircut"
        assert service.price == Decimal('30.00')

    def test_update_service_changes_slug(self, service):
        """Should update slug when name changes."""
        original_slug = service.slug
        success, _ = ServiceService.update_service(
            service,
            name="Completely Different Name",
        )

        assert success is True
        service.refresh_from_db()
        assert service.slug != original_slug
        assert service.slug == "completely-different-name"

    def test_delete_service(self, service):
        """Should delete service."""
        service_id = service.id
        success, error = ServiceService.delete_service(service)

        assert success is True
        assert error is None
        assert not Service.objects.filter(id=service_id).exists()

    def test_toggle_service_active(self, service):
        """Should toggle service active status."""
        assert service.is_active is True

        is_active = ServiceService.toggle_service_active(service)
        assert is_active is False

        is_active = ServiceService.toggle_service_active(service)
        assert is_active is True

    def test_duplicate_service(self, service, service_variant):
        """Should duplicate service with variants."""
        new_service, error = ServiceService.duplicate_service(service)

        assert error is None
        assert new_service is not None
        assert new_service.id != service.id
        assert "Copy" in new_service.name
        assert new_service.price == service.price
        assert new_service.variants.count() == service.variants.count()

    def test_duplicate_service_custom_name(self, service):
        """Should duplicate with custom name."""
        new_service, error = ServiceService.duplicate_service(
            service,
            new_name="Custom Name Service"
        )

        assert error is None
        assert new_service.name == "Custom Name Service"


# =============================================================================
# Category Management Tests
# =============================================================================

@pytest.mark.django_db
class TestCategoryManagement:
    """Test category management operations."""

    def test_create_category_success(self):
        """Should create category successfully."""
        category, error = ServiceService.create_category(
            name="New Category",
            description="Test description",
            icon="folder-outline",
        )

        assert error is None
        assert category is not None
        assert category.name == "New Category"
        assert category.slug == "new-category"

    def test_create_category_with_parent(self, category):
        """Should create subcategory."""
        subcategory, error = ServiceService.create_category(
            name="Subcategory",
            parent_id=category.id,
        )

        assert error is None
        assert subcategory.parent == category

    def test_create_category_invalid_parent(self):
        """Should return error for invalid parent."""
        category, error = ServiceService.create_category(
            name="Test",
            parent_id=9999,
        )

        assert category is None
        assert "not found" in error.lower()

    def test_update_category_success(self, category):
        """Should update category."""
        success, error = ServiceService.update_category(
            category,
            name="Updated Category",
            color="#FF0000",
        )

        assert success is True
        category.refresh_from_db()
        assert category.name == "Updated Category"
        assert category.color == "#FF0000"

    def test_update_category_circular_reference(self, category, subcategory):
        """Should prevent circular reference."""
        success, error = ServiceService.update_category(
            category,
            parent_id=subcategory.id,
        )

        assert success is False
        assert "descendant" in error.lower() or "circular" in error.lower()

    def test_delete_category_moves_services(self, category, service):
        """Should move services to parent on delete."""
        subcategory, _ = ServiceService.create_category(
            name="To Delete",
            parent_id=category.id,
        )
        service.category = subcategory
        service.save()

        success, error = ServiceService.delete_category(subcategory, move_to_parent=True)

        assert success is True
        service.refresh_from_db()
        assert service.category == category

    def test_get_category_tree(self, category, subcategory):
        """Should get category tree structure."""
        tree = ServiceService.get_category_tree()

        assert len(tree) >= 1
        parent_node = next((n for n in tree if n['id'] == category.id), None)
        assert parent_node is not None
        assert len(parent_node['children']) >= 1


# =============================================================================
# Variant Management Tests
# =============================================================================

@pytest.mark.django_db
class TestVariantManagement:
    """Test variant management operations."""

    def test_create_variant_success(self, service):
        """Should create variant successfully."""
        variant, error = ServiceService.create_variant(
            service=service,
            name="Extra Long",
            price_adjustment=Decimal('15.00'),
            duration_adjustment=20,
        )

        assert error is None
        assert variant is not None
        assert variant.name == "Extra Long"
        assert variant.final_price == service.price + Decimal('15.00')

    def test_create_variant_duplicate_name(self, service, service_variant):
        """Should return error for duplicate name."""
        variant, error = ServiceService.create_variant(
            service=service,
            name="Long Hair",  # Already exists
            price_adjustment=Decimal('5.00'),
        )

        assert variant is None
        assert "already exists" in error.lower()

    def test_update_variant(self, service_variant):
        """Should update variant."""
        success, error = ServiceService.update_variant(
            service_variant,
            name="Updated Variant",
            price_adjustment=Decimal('20.00'),
        )

        assert success is True
        service_variant.refresh_from_db()
        assert service_variant.name == "Updated Variant"
        assert service_variant.price_adjustment == Decimal('20.00')

    def test_delete_variant(self, service_variant):
        """Should delete variant."""
        variant_id = service_variant.id
        success, error = ServiceService.delete_variant(service_variant)

        assert success is True
        assert not ServiceVariant.objects.filter(id=variant_id).exists()


# =============================================================================
# Addon Management Tests
# =============================================================================

@pytest.mark.django_db
class TestAddonManagement:
    """Test addon management operations."""

    def test_create_addon_success(self, service):
        """Should create addon successfully."""
        addon, error = ServiceService.create_addon(
            name="New Addon",
            price=Decimal('10.00'),
            duration_minutes=15,
            service_ids=[service.id],
        )

        assert error is None
        assert addon is not None
        assert addon.name == "New Addon"
        assert service in addon.services.all()

    def test_create_addon_empty_name(self):
        """Should return error for empty name."""
        addon, error = ServiceService.create_addon(
            name="",
            price=Decimal('10.00'),
        )

        assert addon is None
        assert "required" in error.lower()

    def test_update_addon(self, service_addon, featured_service):
        """Should update addon."""
        success, error = ServiceService.update_addon(
            service_addon,
            name="Updated Addon",
            service_ids=[featured_service.id],
        )

        assert success is True
        service_addon.refresh_from_db()
        assert service_addon.name == "Updated Addon"
        assert featured_service in service_addon.services.all()

    def test_delete_addon(self, service_addon):
        """Should delete addon."""
        addon_id = service_addon.id
        success, error = ServiceService.delete_addon(service_addon)

        assert success is True
        assert not ServiceAddon.objects.filter(id=addon_id).exists()


# =============================================================================
# Package Management Tests
# =============================================================================

@pytest.mark.django_db
class TestPackageManagement:
    """Test package management operations."""

    def test_create_package_success(self, service, featured_service):
        """Should create package successfully."""
        package, error = ServiceService.create_package(
            name="New Package",
            service_items=[
                {'service_id': service.id, 'quantity': 1},
                {'service_id': featured_service.id, 'quantity': 2},
            ],
            discount_type='percentage',
            discount_value=Decimal('15.00'),
        )

        assert error is None
        assert package is not None
        assert package.name == "New Package"
        assert package.items.count() == 2

    def test_create_package_empty_name(self, service):
        """Should return error for empty name."""
        package, error = ServiceService.create_package(
            name="",
            service_items=[{'service_id': service.id, 'quantity': 1}],
        )

        assert package is None
        assert "required" in error.lower()

    def test_create_package_no_services(self):
        """Should return error for empty services."""
        package, error = ServiceService.create_package(
            name="Empty Package",
            service_items=[],
        )

        assert package is None
        assert "service" in error.lower()

    def test_update_package(self, service_package, service):
        """Should update package."""
        success, error = ServiceService.update_package(
            service_package,
            name="Updated Package",
            discount_value=Decimal('20.00'),
        )

        assert success is True
        service_package.refresh_from_db()
        assert service_package.name == "Updated Package"
        assert service_package.discount_value == Decimal('20.00')

    def test_update_package_items(self, service_package, service):
        """Should update package items."""
        success, error = ServiceService.update_package(
            service_package,
            service_items=[
                {'service_id': service.id, 'quantity': 3},
            ],
        )

        assert success is True
        assert service_package.items.count() == 1
        assert service_package.items.first().quantity == 3

    def test_delete_package(self, service_package):
        """Should delete package."""
        package_id = service_package.id
        success, error = ServiceService.delete_package(service_package)

        assert success is True
        assert not ServicePackage.objects.filter(id=package_id).exists()


# =============================================================================
# Query Methods Tests
# =============================================================================

@pytest.mark.django_db
class TestQueryMethods:
    """Test query methods."""

    def test_search_services_by_name(self, service, featured_service):
        """Should search services by name."""
        results = ServiceService.search_services(query="Haircut")

        assert len(results) >= 1
        assert service in results

    def test_search_services_by_category(self, service, category):
        """Should filter by category."""
        results = ServiceService.search_services(category_id=category.id)

        assert service in results

    def test_search_services_inactive(self, service, inactive_service):
        """Should filter by active status."""
        active_results = ServiceService.search_services(is_active=True)
        inactive_results = ServiceService.search_services(is_active=False)

        assert service in active_results
        assert inactive_service not in active_results
        assert inactive_service in inactive_results

    def test_search_services_bookable(self, service, featured_service):
        """Should filter by bookable status."""
        results = ServiceService.search_services(is_bookable=True)

        assert service in results

    def test_search_services_price_range(self, service, featured_service):
        """Should filter by price range."""
        results = ServiceService.search_services(
            min_price=Decimal('50.00'),
            max_price=Decimal('100.00'),
        )

        assert featured_service in results
        assert service not in results

    def test_get_featured_services(self, service, featured_service):
        """Should get featured services."""
        results = ServiceService.get_featured_services()

        assert featured_service in results
        assert service not in results

    def test_get_bookable_services(self, service, featured_service):
        """Should get bookable services."""
        results = ServiceService.get_bookable_services()

        assert service in results

    def test_get_services_by_category(self, service, category, subcategory):
        """Should get services by category including children."""
        from services.models import Service as ServiceModel
        sub_service = ServiceModel.objects.create(
            name="Sub Service",
            slug="sub-service",
            category=subcategory,
            price=Decimal('30.00'),
            duration_minutes=30,
        )

        results = ServiceService.get_services_by_category(
            category.id,
            include_children=True
        )

        assert service in results
        assert sub_service in results


# =============================================================================
# Statistics Tests
# =============================================================================

@pytest.mark.django_db
class TestStatistics:
    """Test statistics methods."""

    def test_get_service_stats(self, service, featured_service, inactive_service, category, service_package):
        """Should get service statistics."""
        stats = ServiceService.get_service_stats()

        assert 'total_services' in stats
        assert 'active_services' in stats
        assert 'inactive_services' in stats
        assert 'bookable_services' in stats
        assert 'featured_services' in stats
        assert 'categories' in stats
        assert 'packages' in stats
        assert 'avg_price' in stats
        assert 'min_price' in stats
        assert 'max_price' in stats
        assert 'avg_duration' in stats

        assert stats['total_services'] >= 3
        assert stats['active_services'] >= 2
        assert stats['inactive_services'] >= 1
        assert stats['featured_services'] >= 1

    def test_get_price_range(self, service, featured_service):
        """Should get price range."""
        price_range = ServiceService.get_price_range()

        assert 'min' in price_range
        assert 'max' in price_range
        assert price_range['min'] <= price_range['max']
        assert price_range['min'] == service.price or price_range['min'] == featured_service.price
