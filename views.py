"""
Views for the services module.
Handles all HTTP requests for services, categories, variants, addons, and packages.
"""
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q
from decimal import Decimal

from apps.accounts.decorators import login_required
from apps.modules_runtime.decorators import module_view

from .models import (
    ServicesConfig,
    ServiceCategory,
    Service,
    ServiceVariant,
    ServiceAddon,
    ServicePackage,
)
from .services import ServiceService


# =============================================================================
# Dashboard
# =============================================================================

@login_required
@module_view("services", "dashboard")
def dashboard(request):
    """Services dashboard with statistics and overview."""
    stats = ServiceService.get_service_stats()
    recent_services = Service.objects.filter(is_active=True).order_by('-created_at')[:5]
    featured_services = ServiceService.get_featured_services(limit=5)

    return {
        'stats': stats,
        'recent_services': recent_services,
        'featured_services': featured_services,
    }


# =============================================================================
# Service CRUD
# =============================================================================

@login_required
@module_view("services", "list")
def service_list(request):
    """List all services with search and filters."""
    search = request.GET.get('search', '')
    category_id = request.GET.get('category')
    status = request.GET.get('status', 'active')

    is_active = None
    if status == 'active':
        is_active = True
    elif status == 'inactive':
        is_active = False

    services = ServiceService.search_services(
        query=search,
        category_id=int(category_id) if category_id else None,
        is_active=is_active,
    )

    categories = ServiceCategory.objects.filter(is_active=True).order_by('order', 'name')

    return {
        'services': services,
        'categories': categories,
        'search': search,
        'selected_category': category_id,
        'status': status,
    }


@login_required
def service_create(request):
    """Create a new service."""
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            # Convert numeric fields
            price = Decimal(data.get('price', '0'))
            duration = int(data.get('duration_minutes', 60))
            category_id = data.get('category_id') or data.get('category')
            if category_id:
                category_id = int(category_id)
            else:
                category_id = None

            service, error = ServiceService.create_service(
                name=data.get('name', ''),
                price=price,
                duration_minutes=duration,
                category_id=category_id,
                description=data.get('description', ''),
                short_description=data.get('short_description', ''),
                pricing_type=data.get('pricing_type', 'fixed'),
                cost=Decimal(data.get('cost', '0')),
                tax_rate=Decimal(data.get('tax_rate')) if data.get('tax_rate') else None,
                buffer_before=int(data.get('buffer_before', 0)),
                buffer_after=int(data.get('buffer_after', 0)),
                max_capacity=int(data.get('max_capacity', 1)),
                is_bookable=data.get('is_bookable', 'true') in ['true', True, '1', 1],
                requires_confirmation=data.get('requires_confirmation', 'false') in ['true', True, '1', 1],
                allow_online_booking=data.get('allow_online_booking', 'true') in ['true', True, '1', 1],
                is_featured=data.get('is_featured', 'false') in ['true', True, '1', 1],
                sku=data.get('sku'),
                barcode=data.get('barcode', ''),
                notes=data.get('notes', ''),
                icon=data.get('icon', ''),
                color=data.get('color', ''),
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True, 'id': service.id, 'slug': service.slug})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # GET - show form
    categories = ServiceCategory.objects.filter(is_active=True).order_by('order', 'name')
    config = ServicesConfig.get_config()

    return render(request, 'services/service_form.html', {
        'mode': 'create',
        'categories': categories,
        'config': config,
    })


@login_required
def service_detail(request, pk):
    """Service detail view."""
    service = get_object_or_404(Service, pk=pk)
    variants = service.variants.filter(is_active=True).order_by('order')
    addons = service.addons.filter(is_active=True)
    packages = service.packages.filter(is_active=True)

    return render(request, 'services/service_detail.html', {
        'service': service,
        'variants': variants,
        'addons': addons,
        'packages': packages,
    })


@login_required
def service_edit(request, pk):
    """Edit a service."""
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            # Build update kwargs
            kwargs = {}

            if 'name' in data:
                kwargs['name'] = data['name']
            if 'description' in data:
                kwargs['description'] = data['description']
            if 'short_description' in data:
                kwargs['short_description'] = data['short_description']
            if 'price' in data:
                kwargs['price'] = Decimal(data['price'])
            if 'duration_minutes' in data:
                kwargs['duration_minutes'] = int(data['duration_minutes'])
            if 'category_id' in data or 'category' in data:
                cat_id = data.get('category_id') or data.get('category')
                kwargs['category_id'] = int(cat_id) if cat_id else None
            if 'pricing_type' in data:
                kwargs['pricing_type'] = data['pricing_type']
            if 'cost' in data:
                kwargs['cost'] = Decimal(data['cost'])
            if 'tax_rate' in data:
                kwargs['tax_rate'] = Decimal(data['tax_rate']) if data['tax_rate'] else None
            if 'buffer_before' in data:
                kwargs['buffer_before'] = int(data['buffer_before'])
            if 'buffer_after' in data:
                kwargs['buffer_after'] = int(data['buffer_after'])
            if 'max_capacity' in data:
                kwargs['max_capacity'] = int(data['max_capacity'])
            if 'is_bookable' in data:
                kwargs['is_bookable'] = data['is_bookable'] in ['true', True, '1', 1]
            if 'requires_confirmation' in data:
                kwargs['requires_confirmation'] = data['requires_confirmation'] in ['true', True, '1', 1]
            if 'allow_online_booking' in data:
                kwargs['allow_online_booking'] = data['allow_online_booking'] in ['true', True, '1', 1]
            if 'is_featured' in data:
                kwargs['is_featured'] = data['is_featured'] in ['true', True, '1', 1]
            if 'is_active' in data:
                kwargs['is_active'] = data['is_active'] in ['true', True, '1', 1]
            if 'sku' in data:
                kwargs['sku'] = data['sku'] if data['sku'] else None
            if 'barcode' in data:
                kwargs['barcode'] = data['barcode']
            if 'notes' in data:
                kwargs['notes'] = data['notes']
            if 'icon' in data:
                kwargs['icon'] = data['icon']
            if 'color' in data:
                kwargs['color'] = data['color']

            success, error = ServiceService.update_service(service, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # GET - show form
    categories = ServiceCategory.objects.filter(is_active=True).order_by('order', 'name')
    config = ServicesConfig.get_config()

    return render(request, 'services/service_form.html', {
        'mode': 'edit',
        'service': service,
        'categories': categories,
        'config': config,
    })


@login_required
@require_POST
def service_delete(request, pk):
    """Delete a service."""
    service = get_object_or_404(Service, pk=pk)
    success, error = ServiceService.delete_service(service)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


@login_required
@require_POST
def service_toggle(request, pk):
    """Toggle service active status."""
    service = get_object_or_404(Service, pk=pk)
    is_active = ServiceService.toggle_service_active(service)

    return JsonResponse({'success': True, 'is_active': is_active})


@login_required
@require_POST
def service_duplicate(request, pk):
    """Duplicate a service."""
    service = get_object_or_404(Service, pk=pk)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    new_name = data.get('name')
    new_service, error = ServiceService.duplicate_service(service, new_name)

    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({
        'success': True,
        'id': new_service.id,
        'slug': new_service.slug,
        'name': new_service.name,
    })


# =============================================================================
# Categories
# =============================================================================

@login_required
@module_view("services", "categories")
def category_list(request):
    """List all categories."""
    search = request.GET.get('search', '')

    categories = ServiceCategory.objects.all().order_by('order', 'name')

    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    category_tree = ServiceService.get_category_tree()

    return {
        'categories': categories,
        'category_tree': category_tree,
        'search': search,
    }


@login_required
def category_create(request):
    """Create a new category."""
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            parent_id = data.get('parent_id') or data.get('parent')
            if parent_id:
                parent_id = int(parent_id)
            else:
                parent_id = None

            category, error = ServiceService.create_category(
                name=data.get('name', ''),
                parent_id=parent_id,
                description=data.get('description', ''),
                icon=data.get('icon', ''),
                color=data.get('color', ''),
                order=int(data.get('order', 0)),
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({
                'success': True,
                'id': category.id,
                'slug': category.slug,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # GET - show form
    parent_categories = ServiceCategory.objects.filter(
        is_active=True,
        parent__isnull=True
    ).order_by('order', 'name')

    return render(request, 'services/category_form.html', {
        'mode': 'create',
        'parent_categories': parent_categories,
    })


@login_required
def category_detail(request, pk):
    """Category detail view."""
    category = get_object_or_404(ServiceCategory, pk=pk)
    services = category.services.filter(is_active=True).order_by('order', 'name')
    children = category.children.filter(is_active=True).order_by('order', 'name')

    return render(request, 'services/category_detail.html', {
        'category': category,
        'services': services,
        'children': children,
    })


@login_required
def category_edit(request, pk):
    """Edit a category."""
    category = get_object_or_404(ServiceCategory, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            kwargs = {}

            if 'name' in data:
                kwargs['name'] = data['name']
            if 'description' in data:
                kwargs['description'] = data['description']
            if 'parent_id' in data or 'parent' in data:
                parent_id = data.get('parent_id') or data.get('parent')
                kwargs['parent_id'] = int(parent_id) if parent_id else None
            if 'icon' in data:
                kwargs['icon'] = data['icon']
            if 'color' in data:
                kwargs['color'] = data['color']
            if 'order' in data:
                kwargs['order'] = int(data['order'])
            if 'is_active' in data:
                kwargs['is_active'] = data['is_active'] in ['true', True, '1', 1]

            success, error = ServiceService.update_category(category, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # GET - show form
    parent_categories = ServiceCategory.objects.filter(
        is_active=True
    ).exclude(
        pk=pk
    ).exclude(
        pk__in=[c.id for c in category.get_descendants()]
    ).order_by('order', 'name')

    return render(request, 'services/category_form.html', {
        'mode': 'edit',
        'category': category,
        'parent_categories': parent_categories,
    })


@login_required
@require_POST
def category_delete(request, pk):
    """Delete a category."""
    category = get_object_or_404(ServiceCategory, pk=pk)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    move_to_parent = data.get('move_to_parent', True)
    success, error = ServiceService.delete_category(category, move_to_parent)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


# =============================================================================
# Variants
# =============================================================================

@login_required
def variant_create(request, service_pk):
    """Create a service variant."""
    service = get_object_or_404(Service, pk=service_pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            variant, error = ServiceService.create_variant(
                service=service,
                name=data.get('name', ''),
                price_adjustment=Decimal(data.get('price_adjustment', '0')),
                duration_adjustment=int(data.get('duration_adjustment', 0)),
                description=data.get('description', ''),
                order=int(data.get('order', 0)),
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({
                'success': True,
                'id': variant.id,
                'final_price': str(variant.final_price),
                'final_duration': variant.final_duration,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'services/variant_form.html', {
        'mode': 'create',
        'service': service,
    })


@login_required
def variant_edit(request, pk):
    """Edit a variant."""
    variant = get_object_or_404(ServiceVariant, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            kwargs = {}
            if 'name' in data:
                kwargs['name'] = data['name']
            if 'description' in data:
                kwargs['description'] = data['description']
            if 'price_adjustment' in data:
                kwargs['price_adjustment'] = Decimal(data['price_adjustment'])
            if 'duration_adjustment' in data:
                kwargs['duration_adjustment'] = int(data['duration_adjustment'])
            if 'order' in data:
                kwargs['order'] = int(data['order'])
            if 'is_active' in data:
                kwargs['is_active'] = data['is_active'] in ['true', True, '1', 1]

            success, error = ServiceService.update_variant(variant, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'services/variant_form.html', {
        'mode': 'edit',
        'variant': variant,
        'service': variant.service,
    })


@login_required
@require_POST
def variant_delete(request, pk):
    """Delete a variant."""
    variant = get_object_or_404(ServiceVariant, pk=pk)
    success, error = ServiceService.delete_variant(variant)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


# =============================================================================
# Addons
# =============================================================================

@login_required
def addon_list(request):
    """List all addons."""
    search = request.GET.get('search', '')

    addons = ServiceAddon.objects.all().order_by('name')

    if search:
        addons = addons.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    return render(request, 'services/addon_list.html', {
        'addons': addons,
        'search': search,
    })


@login_required
def addon_create(request):
    """Create an addon."""
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            service_ids = data.get('service_ids', [])
            if isinstance(service_ids, str):
                service_ids = [int(x) for x in service_ids.split(',') if x]

            addon, error = ServiceService.create_addon(
                name=data.get('name', ''),
                price=Decimal(data.get('price', '0')),
                duration_minutes=int(data.get('duration_minutes', 0)),
                description=data.get('description', ''),
                service_ids=service_ids,
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True, 'id': addon.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    services = Service.objects.filter(is_active=True).order_by('name')

    return render(request, 'services/addon_form.html', {
        'mode': 'create',
        'services': services,
    })


@login_required
def addon_edit(request, pk):
    """Edit an addon."""
    addon = get_object_or_404(ServiceAddon, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            kwargs = {}
            if 'name' in data:
                kwargs['name'] = data['name']
            if 'description' in data:
                kwargs['description'] = data['description']
            if 'price' in data:
                kwargs['price'] = Decimal(data['price'])
            if 'duration_minutes' in data:
                kwargs['duration_minutes'] = int(data['duration_minutes'])
            if 'is_active' in data:
                kwargs['is_active'] = data['is_active'] in ['true', True, '1', 1]

            service_ids = data.get('service_ids')
            if service_ids is not None:
                if isinstance(service_ids, str):
                    service_ids = [int(x) for x in service_ids.split(',') if x]
            else:
                service_ids = None

            success, error = ServiceService.update_addon(addon, service_ids=service_ids, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    services = Service.objects.filter(is_active=True).order_by('name')
    selected_services = list(addon.services.values_list('id', flat=True))

    return render(request, 'services/addon_form.html', {
        'mode': 'edit',
        'addon': addon,
        'services': services,
        'selected_services': selected_services,
    })


@login_required
@require_POST
def addon_delete(request, pk):
    """Delete an addon."""
    addon = get_object_or_404(ServiceAddon, pk=pk)
    success, error = ServiceService.delete_addon(addon)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


# =============================================================================
# Packages
# =============================================================================

@login_required
def package_list(request):
    """List all packages."""
    search = request.GET.get('search', '')

    packages = ServicePackage.objects.all().order_by('order', 'name')

    if search:
        packages = packages.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    return render(request, 'services/package_list.html', {
        'packages': packages,
        'search': search,
    })


@login_required
def package_create(request):
    """Create a package."""
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            service_items = data.get('service_items', [])

            package, error = ServiceService.create_package(
                name=data.get('name', ''),
                service_items=service_items,
                discount_type=data.get('discount_type', 'percentage'),
                discount_value=Decimal(data.get('discount_value', '0')),
                fixed_price=Decimal(data['fixed_price']) if data.get('fixed_price') else None,
                description=data.get('description', ''),
                validity_days=int(data['validity_days']) if data.get('validity_days') else None,
                max_uses=int(data['max_uses']) if data.get('max_uses') else None,
                is_featured=data.get('is_featured', False) in ['true', True, '1', 1],
                order=int(data.get('order', 0)),
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({
                'success': True,
                'id': package.id,
                'slug': package.slug,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    services = Service.objects.filter(is_active=True).order_by('category__name', 'name')

    return render(request, 'services/package_form.html', {
        'mode': 'create',
        'services': services,
    })


@login_required
def package_detail(request, pk):
    """Package detail view."""
    package = get_object_or_404(ServicePackage, pk=pk)
    items = package.items.all().select_related('service').order_by('order')

    return render(request, 'services/package_detail.html', {
        'package': package,
        'items': items,
    })


@login_required
def package_edit(request, pk):
    """Edit a package."""
    package = get_object_or_404(ServicePackage, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            kwargs = {}
            if 'name' in data:
                kwargs['name'] = data['name']
            if 'description' in data:
                kwargs['description'] = data['description']
            if 'discount_type' in data:
                kwargs['discount_type'] = data['discount_type']
            if 'discount_value' in data:
                kwargs['discount_value'] = Decimal(data['discount_value'])
            if 'fixed_price' in data:
                kwargs['fixed_price'] = Decimal(data['fixed_price']) if data['fixed_price'] else None
            if 'validity_days' in data:
                kwargs['validity_days'] = int(data['validity_days']) if data['validity_days'] else None
            if 'max_uses' in data:
                kwargs['max_uses'] = int(data['max_uses']) if data['max_uses'] else None
            if 'is_featured' in data:
                kwargs['is_featured'] = data['is_featured'] in ['true', True, '1', 1]
            if 'is_active' in data:
                kwargs['is_active'] = data['is_active'] in ['true', True, '1', 1]
            if 'order' in data:
                kwargs['order'] = int(data['order'])

            service_items = data.get('service_items')

            success, error = ServiceService.update_package(package, service_items=service_items, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    services = Service.objects.filter(is_active=True).order_by('category__name', 'name')
    current_items = list(package.items.values('service_id', 'quantity', 'order'))

    return render(request, 'services/package_form.html', {
        'mode': 'edit',
        'package': package,
        'services': services,
        'current_items': current_items,
    })


@login_required
@require_POST
def package_delete(request, pk):
    """Delete a package."""
    package = get_object_or_404(ServicePackage, pk=pk)
    success, error = ServiceService.delete_package(package)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


# =============================================================================
# Settings
# =============================================================================

@login_required
@module_view("services", "settings")
def settings_view(request):
    """Settings page."""
    config = ServicesConfig.get_config()
    return {'config': config}


@login_required
@require_POST
def settings_save(request):
    """Save settings."""
    config = ServicesConfig.get_config()

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        if 'default_duration' in data:
            config.default_duration = int(data['default_duration'])
        if 'default_buffer_time' in data:
            config.default_buffer_time = int(data['default_buffer_time'])
        if 'default_tax_rate' in data:
            config.default_tax_rate = Decimal(data['default_tax_rate'])
        if 'currency' in data:
            config.currency = data['currency']
        if 'price_decimal_places' in data:
            config.price_decimal_places = int(data['price_decimal_places'])

        config.save()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def settings_toggle(request):
    """Toggle boolean settings."""
    config = ServicesConfig.get_config()
    field = request.POST.get('field')

    toggleable_fields = [
        'show_prices',
        'show_duration',
        'allow_online_booking',
        'include_tax_in_price',
    ]

    if field not in toggleable_fields:
        return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)

    setattr(config, field, not getattr(config, field))
    config.save()

    return JsonResponse({'success': True, 'value': getattr(config, field)})


# =============================================================================
# API Endpoints
# =============================================================================

@login_required
@require_GET
def api_search(request):
    """Search services API."""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 20))

    services = ServiceService.search_services(
        query=query,
        is_active=True,
    )[:limit]

    results = [
        {
            'id': s.id,
            'name': s.name,
            'price': str(s.price),
            'duration_minutes': s.duration_minutes,
            'category': s.category.name if s.category else None,
            'is_bookable': s.is_bookable,
        }
        for s in services
    ]

    return JsonResponse({'results': results})


@login_required
@require_GET
def api_services_list(request):
    """List services API."""
    category_id = request.GET.get('category_id')
    bookable_only = request.GET.get('bookable', 'false') == 'true'

    if bookable_only:
        services = ServiceService.get_bookable_services()
    elif category_id:
        services = ServiceService.get_services_by_category(int(category_id))
    else:
        services = Service.objects.filter(is_active=True).order_by('order', 'name')

    results = [
        {
            'id': s.id,
            'name': s.name,
            'slug': s.slug,
            'price': str(s.price),
            'price_display': s.get_price_display(),
            'duration_minutes': s.duration_minutes,
            'total_duration': s.total_duration,
            'category_id': s.category_id,
            'category_name': s.category.name if s.category else None,
            'is_bookable': s.is_bookable,
            'max_capacity': s.max_capacity,
            'icon': s.icon,
            'color': s.color,
        }
        for s in services
    ]

    return JsonResponse({'services': results})


@login_required
@require_GET
def api_service_detail(request, pk):
    """Service detail API."""
    try:
        service = Service.objects.get(pk=pk)
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)

    variants = [
        {
            'id': v.id,
            'name': v.name,
            'price_adjustment': str(v.price_adjustment),
            'duration_adjustment': v.duration_adjustment,
            'final_price': str(v.final_price),
            'final_duration': v.final_duration,
        }
        for v in service.variants.filter(is_active=True)
    ]

    addons = [
        {
            'id': a.id,
            'name': a.name,
            'price': str(a.price),
            'duration_minutes': a.duration_minutes,
        }
        for a in service.addons.filter(is_active=True)
    ]

    return JsonResponse({
        'id': service.id,
        'name': service.name,
        'slug': service.slug,
        'description': service.description,
        'short_description': service.short_description,
        'price': str(service.price),
        'price_display': service.get_price_display(),
        'price_with_tax': str(service.price_with_tax),
        'duration_minutes': service.duration_minutes,
        'buffer_before': service.buffer_before,
        'buffer_after': service.buffer_after,
        'total_duration': service.total_duration,
        'max_capacity': service.max_capacity,
        'is_bookable': service.is_bookable,
        'requires_confirmation': service.requires_confirmation,
        'category_id': service.category_id,
        'category_name': service.category.name if service.category else None,
        'variants': variants,
        'addons': addons,
    })
