"""
Service layer for the services module.
Handles all business logic for services, categories, variants, addons, and packages.
"""
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils.text import slugify

from services.models import (
    ServicesConfig,
    ServiceCategory,
    Service,
    ServiceVariant,
    ServiceAddon,
    ServicePackage,
    ServicePackageItem,
)


class ServiceService:
    """Service class for managing services and related entities."""

    # =========================================================================
    # Service CRUD
    # =========================================================================

    @staticmethod
    @transaction.atomic
    def create_service(
        name: str,
        price: Decimal = Decimal('0.00'),
        duration_minutes: int = 60,
        category_id: Optional[int] = None,
        description: str = '',
        short_description: str = '',
        pricing_type: str = 'fixed',
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        cost: Decimal = Decimal('0.00'),
        tax_rate: Optional[Decimal] = None,
        buffer_before: int = 0,
        buffer_after: int = 0,
        max_capacity: int = 1,
        is_bookable: bool = True,
        requires_confirmation: bool = False,
        allow_online_booking: bool = True,
        is_featured: bool = False,
        sku: Optional[str] = None,
        barcode: str = '',
        notes: str = '',
        icon: str = '',
        color: str = '',
        order: int = 0,
    ) -> Tuple[Optional[Service], Optional[str]]:
        """
        Create a new service.

        Returns:
            Tuple of (service, error_message)
        """
        # Validate name
        if not name or not name.strip():
            return None, "Service name is required"

        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Service.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Validate category
        category = None
        if category_id:
            try:
                category = ServiceCategory.objects.get(pk=category_id)
            except ServiceCategory.DoesNotExist:
                return None, "Category not found"

        # Validate price range for variable pricing
        if pricing_type == 'variable':
            if min_price and max_price and min_price > max_price:
                return None, "Minimum price cannot be greater than maximum price"

        # Get default values from config
        config = ServicesConfig.get_config()
        if duration_minutes == 60 and config.default_duration != 60:
            duration_minutes = config.default_duration

        try:
            service = Service.objects.create(
                name=name.strip(),
                slug=slug,
                description=description,
                short_description=short_description,
                category=category,
                pricing_type=pricing_type,
                price=price,
                min_price=min_price,
                max_price=max_price,
                cost=cost,
                tax_rate=tax_rate,
                duration_minutes=duration_minutes,
                buffer_before=buffer_before,
                buffer_after=buffer_after,
                max_capacity=max_capacity,
                is_bookable=is_bookable,
                requires_confirmation=requires_confirmation,
                allow_online_booking=allow_online_booking,
                is_featured=is_featured,
                sku=sku if sku else None,
                barcode=barcode,
                notes=notes,
                icon=icon,
                color=color,
                order=order,
            )
            return service, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    @transaction.atomic
    def update_service(
        service: Service,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Update an existing service.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Handle category update
            if 'category_id' in kwargs:
                category_id = kwargs.pop('category_id')
                if category_id:
                    try:
                        kwargs['category'] = ServiceCategory.objects.get(pk=category_id)
                    except ServiceCategory.DoesNotExist:
                        return False, "Category not found"
                else:
                    kwargs['category'] = None

            # Handle name change - update slug
            if 'name' in kwargs and kwargs['name'] != service.name:
                base_slug = slugify(kwargs['name'])
                slug = base_slug
                counter = 1
                while Service.objects.filter(slug=slug).exclude(pk=service.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                kwargs['slug'] = slug

            # Validate price range
            min_price = kwargs.get('min_price', service.min_price)
            max_price = kwargs.get('max_price', service.max_price)
            pricing_type = kwargs.get('pricing_type', service.pricing_type)
            if pricing_type == 'variable' and min_price and max_price:
                if min_price > max_price:
                    return False, "Minimum price cannot be greater than maximum price"

            for key, value in kwargs.items():
                if hasattr(service, key):
                    setattr(service, key, value)

            service.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_service(service: Service) -> Tuple[bool, Optional[str]]:
        """Delete a service."""
        try:
            service.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def toggle_service_active(service: Service) -> bool:
        """Toggle service active status."""
        service.is_active = not service.is_active
        service.save(update_fields=['is_active', 'updated_at'])
        return service.is_active

    @staticmethod
    @transaction.atomic
    def duplicate_service(service: Service, new_name: Optional[str] = None) -> Tuple[Optional[Service], Optional[str]]:
        """
        Duplicate a service with all its variants.

        Returns:
            Tuple of (new_service, error_message)
        """
        name = new_name or f"{service.name} (Copy)"

        new_service, error = ServiceService.create_service(
            name=name,
            price=service.price,
            duration_minutes=service.duration_minutes,
            category_id=service.category_id,
            description=service.description,
            short_description=service.short_description,
            pricing_type=service.pricing_type,
            min_price=service.min_price,
            max_price=service.max_price,
            cost=service.cost,
            tax_rate=service.tax_rate,
            buffer_before=service.buffer_before,
            buffer_after=service.buffer_after,
            max_capacity=service.max_capacity,
            is_bookable=service.is_bookable,
            requires_confirmation=service.requires_confirmation,
            allow_online_booking=service.allow_online_booking,
            is_featured=False,  # Don't copy featured status
            barcode='',
            notes=service.notes,
            icon=service.icon,
            color=service.color,
        )

        if error:
            return None, error

        # Duplicate variants
        for variant in service.variants.all():
            ServiceVariant.objects.create(
                service=new_service,
                name=variant.name,
                description=variant.description,
                price_adjustment=variant.price_adjustment,
                duration_adjustment=variant.duration_adjustment,
                order=variant.order,
                is_active=variant.is_active,
            )

        # Copy addon associations
        new_service.addons.set(service.addons.all())

        return new_service, None

    # =========================================================================
    # Category Management
    # =========================================================================

    @staticmethod
    @transaction.atomic
    def create_category(
        name: str,
        parent_id: Optional[int] = None,
        description: str = '',
        icon: str = '',
        color: str = '',
        order: int = 0,
    ) -> Tuple[Optional[ServiceCategory], Optional[str]]:
        """Create a new service category."""
        if not name or not name.strip():
            return None, "Category name is required"

        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while ServiceCategory.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Validate parent
        parent = None
        if parent_id:
            try:
                parent = ServiceCategory.objects.get(pk=parent_id)
            except ServiceCategory.DoesNotExist:
                return None, "Parent category not found"

        try:
            category = ServiceCategory.objects.create(
                name=name.strip(),
                slug=slug,
                description=description,
                parent=parent,
                icon=icon,
                color=color,
                order=order,
            )
            return category, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    @transaction.atomic
    def update_category(
        category: ServiceCategory,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update a category."""
        try:
            # Handle parent update
            if 'parent_id' in kwargs:
                parent_id = kwargs.pop('parent_id')
                if parent_id:
                    try:
                        parent = ServiceCategory.objects.get(pk=parent_id)
                        # Check for circular reference
                        if parent == category or parent in category.get_descendants():
                            return False, "Cannot set descendant as parent"
                        kwargs['parent'] = parent
                    except ServiceCategory.DoesNotExist:
                        return False, "Parent category not found"
                else:
                    kwargs['parent'] = None

            # Handle name change
            if 'name' in kwargs and kwargs['name'] != category.name:
                base_slug = slugify(kwargs['name'])
                slug = base_slug
                counter = 1
                while ServiceCategory.objects.filter(slug=slug).exclude(pk=category.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                kwargs['slug'] = slug

            for key, value in kwargs.items():
                if hasattr(category, key):
                    setattr(category, key, value)

            category.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_category(category: ServiceCategory, move_to_parent: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Delete a category.

        Args:
            category: Category to delete
            move_to_parent: If True, move services and children to parent category

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if move_to_parent:
                # Move services to parent category
                category.services.update(category=category.parent)
                # Move child categories to parent
                category.children.update(parent=category.parent)

            category.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_category_tree() -> List[Dict]:
        """Get categories as a tree structure."""
        def build_tree(parent=None):
            categories = ServiceCategory.objects.filter(parent=parent, is_active=True)
            result = []
            for cat in categories:
                node = {
                    'id': cat.id,
                    'name': cat.name,
                    'slug': cat.slug,
                    'icon': cat.icon,
                    'color': cat.color,
                    'service_count': cat.service_count,
                    'children': build_tree(cat),
                }
                result.append(node)
            return result

        return build_tree()

    # =========================================================================
    # Variant Management
    # =========================================================================

    @staticmethod
    def create_variant(
        service: Service,
        name: str,
        price_adjustment: Decimal = Decimal('0.00'),
        duration_adjustment: int = 0,
        description: str = '',
        order: int = 0,
    ) -> Tuple[Optional[ServiceVariant], Optional[str]]:
        """Create a service variant."""
        if not name or not name.strip():
            return None, "Variant name is required"

        # Check for duplicate name
        if service.variants.filter(name=name.strip()).exists():
            return None, "A variant with this name already exists"

        try:
            variant = ServiceVariant.objects.create(
                service=service,
                name=name.strip(),
                description=description,
                price_adjustment=price_adjustment,
                duration_adjustment=duration_adjustment,
                order=order,
            )
            return variant, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def update_variant(
        variant: ServiceVariant,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update a variant."""
        try:
            # Check for duplicate name
            if 'name' in kwargs:
                if variant.service.variants.filter(name=kwargs['name']).exclude(pk=variant.pk).exists():
                    return False, "A variant with this name already exists"

            for key, value in kwargs.items():
                if hasattr(variant, key):
                    setattr(variant, key, value)

            variant.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_variant(variant: ServiceVariant) -> Tuple[bool, Optional[str]]:
        """Delete a variant."""
        try:
            variant.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Addon Management
    # =========================================================================

    @staticmethod
    def create_addon(
        name: str,
        price: Decimal = Decimal('0.00'),
        duration_minutes: int = 0,
        description: str = '',
        service_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[ServiceAddon], Optional[str]]:
        """Create a service addon."""
        if not name or not name.strip():
            return None, "Addon name is required"

        try:
            addon = ServiceAddon.objects.create(
                name=name.strip(),
                description=description,
                price=price,
                duration_minutes=duration_minutes,
            )

            if service_ids:
                services = Service.objects.filter(pk__in=service_ids)
                addon.services.set(services)

            return addon, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def update_addon(
        addon: ServiceAddon,
        service_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update an addon."""
        try:
            for key, value in kwargs.items():
                if hasattr(addon, key):
                    setattr(addon, key, value)

            addon.save()

            if service_ids is not None:
                services = Service.objects.filter(pk__in=service_ids)
                addon.services.set(services)

            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_addon(addon: ServiceAddon) -> Tuple[bool, Optional[str]]:
        """Delete an addon."""
        try:
            addon.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Package Management
    # =========================================================================

    @staticmethod
    @transaction.atomic
    def create_package(
        name: str,
        service_items: List[Dict],  # [{'service_id': 1, 'quantity': 2}, ...]
        discount_type: str = 'percentage',
        discount_value: Decimal = Decimal('0.00'),
        fixed_price: Optional[Decimal] = None,
        description: str = '',
        validity_days: Optional[int] = None,
        max_uses: Optional[int] = None,
        is_featured: bool = False,
        order: int = 0,
    ) -> Tuple[Optional[ServicePackage], Optional[str]]:
        """Create a service package."""
        if not name or not name.strip():
            return None, "Package name is required"

        if not service_items:
            return None, "At least one service is required"

        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while ServicePackage.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        try:
            package = ServicePackage.objects.create(
                name=name.strip(),
                slug=slug,
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                fixed_price=fixed_price,
                validity_days=validity_days,
                max_uses=max_uses,
                is_featured=is_featured,
                order=order,
            )

            # Add services
            for idx, item in enumerate(service_items):
                service_id = item.get('service_id')
                quantity = item.get('quantity', 1)

                try:
                    service = Service.objects.get(pk=service_id)
                    ServicePackageItem.objects.create(
                        package=package,
                        service=service,
                        quantity=quantity,
                        order=idx,
                    )
                except Service.DoesNotExist:
                    pass  # Skip non-existent services

            return package, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    @transaction.atomic
    def update_package(
        package: ServicePackage,
        service_items: Optional[List[Dict]] = None,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update a package."""
        try:
            # Handle name change
            if 'name' in kwargs and kwargs['name'] != package.name:
                base_slug = slugify(kwargs['name'])
                slug = base_slug
                counter = 1
                while ServicePackage.objects.filter(slug=slug).exclude(pk=package.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                kwargs['slug'] = slug

            for key, value in kwargs.items():
                if hasattr(package, key):
                    setattr(package, key, value)

            package.save()

            # Update service items if provided
            if service_items is not None:
                package.items.all().delete()
                for idx, item in enumerate(service_items):
                    service_id = item.get('service_id')
                    quantity = item.get('quantity', 1)

                    try:
                        service = Service.objects.get(pk=service_id)
                        ServicePackageItem.objects.create(
                            package=package,
                            service=service,
                            quantity=quantity,
                            order=idx,
                        )
                    except Service.DoesNotExist:
                        pass

            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_package(package: ServicePackage) -> Tuple[bool, Optional[str]]:
        """Delete a package."""
        try:
            package.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Query Methods
    # =========================================================================

    @staticmethod
    def search_services(
        query: str = '',
        category_id: Optional[int] = None,
        is_bookable: Optional[bool] = None,
        is_active: Optional[bool] = True,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        ordering: str = 'name',
    ) -> List[Service]:
        """Search and filter services."""
        queryset = Service.objects.all()

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(sku__icontains=query) |
                Q(barcode__icontains=query)
            )

        if category_id:
            # Include subcategories
            try:
                category = ServiceCategory.objects.get(pk=category_id)
                descendant_ids = [c.id for c in category.get_descendants()]
                descendant_ids.append(category_id)
                queryset = queryset.filter(category_id__in=descendant_ids)
            except ServiceCategory.DoesNotExist:
                pass

        if is_bookable is not None:
            queryset = queryset.filter(is_bookable=is_bookable)

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        return queryset.order_by(ordering)

    @staticmethod
    def get_featured_services(limit: int = 10) -> List[Service]:
        """Get featured services."""
        return Service.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('order', 'name')[:limit]

    @staticmethod
    def get_bookable_services() -> List[Service]:
        """Get all bookable services."""
        return Service.objects.filter(
            is_bookable=True,
            is_active=True,
            allow_online_booking=True
        ).order_by('category__order', 'category__name', 'order', 'name')

    @staticmethod
    def get_services_by_category(category_id: int, include_children: bool = True) -> List[Service]:
        """Get services for a category."""
        if include_children:
            try:
                category = ServiceCategory.objects.get(pk=category_id)
                descendant_ids = [c.id for c in category.get_descendants()]
                descendant_ids.append(category_id)
                return Service.objects.filter(
                    category_id__in=descendant_ids,
                    is_active=True
                ).order_by('order', 'name')
            except ServiceCategory.DoesNotExist:
                return []
        return Service.objects.filter(category_id=category_id, is_active=True).order_by('order', 'name')

    # =========================================================================
    # Statistics
    # =========================================================================

    @staticmethod
    def get_service_stats() -> Dict[str, Any]:
        """Get service statistics."""
        services = Service.objects.all()
        active_services = services.filter(is_active=True)
        bookable_services = active_services.filter(is_bookable=True)

        # Price stats
        price_stats = active_services.aggregate(
            avg_price=Avg('price'),
            min_price_val=Min('price'),
            max_price_val=Max('price'),
            total_value=Sum('price'),
        )

        # Duration stats
        duration_stats = active_services.aggregate(
            avg_duration=Avg('duration_minutes'),
            min_duration=Min('duration_minutes'),
            max_duration=Max('duration_minutes'),
        )

        # Category breakdown
        categories_with_counts = ServiceCategory.objects.filter(
            is_active=True
        ).annotate(
            count=Count('services', filter=Q(services__is_active=True))
        ).values('id', 'name', 'count')

        return {
            'total_services': services.count(),
            'active_services': active_services.count(),
            'inactive_services': services.filter(is_active=False).count(),
            'bookable_services': bookable_services.count(),
            'featured_services': active_services.filter(is_featured=True).count(),
            'categories': ServiceCategory.objects.filter(is_active=True).count(),
            'packages': ServicePackage.objects.filter(is_active=True).count(),
            'addons': ServiceAddon.objects.filter(is_active=True).count(),
            'avg_price': price_stats['avg_price'] or Decimal('0'),
            'min_price': price_stats['min_price_val'] or Decimal('0'),
            'max_price': price_stats['max_price_val'] or Decimal('0'),
            'avg_duration': duration_stats['avg_duration'] or 0,
            'min_duration': duration_stats['min_duration'] or 0,
            'max_duration': duration_stats['max_duration'] or 0,
            'categories_breakdown': list(categories_with_counts),
        }

    @staticmethod
    def get_price_range() -> Dict[str, Decimal]:
        """Get price range of active services."""
        result = Service.objects.filter(is_active=True).aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
        )
        return {
            'min': result['min_price'] or Decimal('0'),
            'max': result['max_price'] or Decimal('0'),
        }
