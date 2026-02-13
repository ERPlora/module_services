"""Services views."""

import json
from decimal import Decimal

from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST, require_GET

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .models import (
    ServicesSettings,
    ServiceCategory,
    Service,
    ServiceVariant,
    ServiceAddon,
    ServicePackage,
    ServicePackageItem,
)
from .forms import (
    ServiceForm,
    ServiceCategoryForm,
    ServiceVariantForm,
    ServiceAddonForm,
    ServicePackageForm,
    ServiceFilterForm,
    ServicesSettingsForm,
)


def _hub(request):
    return request.session.get('hub_id')


# =============================================================================
# Dashboard
# =============================================================================

@login_required
@with_module_nav('services', 'dashboard')
@htmx_view('services/pages/dashboard.html', 'services/partials/dashboard.html')
def index(request):
    """Redirect to dashboard."""
    return dashboard(request)


@login_required
@with_module_nav('services', 'dashboard')
@htmx_view('services/pages/dashboard.html', 'services/partials/dashboard.html')
def dashboard(request):
    """Services dashboard with statistics."""
    hub = _hub(request)
    services = Service.objects.filter(hub_id=hub, is_deleted=False)

    stats = {
        'total': services.count(),
        'active': services.filter(is_active=True).count(),
        'bookable': services.filter(is_bookable=True, is_active=True).count(),
        'categories': ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, is_active=True).count(),
        'packages': ServicePackage.objects.filter(hub_id=hub, is_deleted=False, is_active=True).count(),
        'avg_price': services.filter(is_active=True, price__gt=0).aggregate(avg=Avg('price'))['avg'] or 0,
    }

    recent_services = services.order_by('-created_at')[:5]
    featured_services = services.filter(is_featured=True, is_active=True)[:5]

    return {
        'stats': stats,
        'recent_services': recent_services,
        'featured_services': featured_services,
    }


# =============================================================================
# Service CRUD
# =============================================================================

@login_required
@with_module_nav('services', 'services')
@htmx_view('services/pages/list.html', 'services/partials/list.html')
def service_list(request):
    """List services with search and filters."""
    hub = _hub(request)
    services = Service.objects.filter(hub_id=hub, is_deleted=False).select_related('category')

    q = request.GET.get('q', '')
    category_id = request.GET.get('category')
    pricing_type = request.GET.get('pricing_type')
    is_active = request.GET.get('is_active')

    if q:
        services = services.filter(
            Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q)
        )
    if category_id:
        services = services.filter(category_id=category_id)
    if pricing_type:
        services = services.filter(pricing_type=pricing_type)
    if is_active == 'true':
        services = services.filter(is_active=True)
    elif is_active == 'false':
        services = services.filter(is_active=False)

    services = services.order_by('sort_order', 'name')
    categories = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, is_active=True).order_by('sort_order', 'name')

    filter_form = ServiceFilterForm(request.GET)
    filter_form.fields['category'].queryset = categories

    return {
        'services': services,
        'categories': categories,
        'filter_form': filter_form,
        'q': q,
    }


@login_required
@with_module_nav('services', 'services')
@htmx_view('services/pages/detail.html', 'services/partials/detail.html')
def service_detail(request, pk):
    """Service detail with variants and addons."""
    hub = _hub(request)
    service = Service.objects.filter(hub_id=hub, is_deleted=False, pk=pk).select_related('category').first()
    if not service:
        return JsonResponse({'error': 'Not found'}, status=404)

    variants = service.variants.filter(is_deleted=False, is_active=True).order_by('sort_order')
    addons = ServiceAddon.objects.filter(hub_id=hub, is_deleted=False, is_active=True, services=service)

    return {
        'service': service,
        'variants': variants,
        'addons': addons,
    }


@login_required
@with_module_nav('services', 'services')
@htmx_view('services/pages/form.html', 'services/partials/form.html')
def service_create(request):
    """Create a service."""
    hub = _hub(request)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.hub_id = hub
            if not service.slug:
                service.slug = slugify(service.name)
            service.save()
            return JsonResponse({'success': True, 'id': str(service.pk), 'name': service.name})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceForm()
    form.fields['category'].queryset = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
    settings = ServicesSettings.get_settings(hub)

    return {
        'form': form,
        'mode': 'create',
        'settings': settings,
    }


@login_required
@with_module_nav('services', 'services')
@htmx_view('services/pages/form.html', 'services/partials/form.html')
def service_edit(request, pk):
    """Edit a service."""
    hub = _hub(request)
    service = Service.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not service:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            service = form.save(commit=False)
            service.updated_at = timezone.now()
            service.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceForm(instance=service)
    form.fields['category'].queryset = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, is_active=True)

    return {
        'form': form,
        'service': service,
        'mode': 'edit',
    }


@login_required
@require_POST
def service_delete(request, pk):
    """Soft delete a service."""
    hub = _hub(request)
    service = Service.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not service:
        return JsonResponse({'error': 'Not found'}, status=404)

    service.is_deleted = True
    service.deleted_at = timezone.now()
    service.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def service_toggle(request, pk):
    """Toggle service active status."""
    hub = _hub(request)
    service = Service.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not service:
        return JsonResponse({'error': 'Not found'}, status=404)

    service.is_active = not service.is_active
    service.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({'success': True, 'is_active': service.is_active})


@login_required
@require_POST
def service_duplicate(request, pk):
    """Duplicate a service with its variants."""
    hub = _hub(request)
    service = Service.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not service:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    new_name = data.get('name', f'{service.name} (copy)')
    new_slug = slugify(new_name)

    # Copy service
    variants = list(service.variants.filter(is_deleted=False))
    service.pk = None
    service.name = new_name
    service.slug = new_slug
    service.is_featured = False
    service.save()

    # Copy variants
    for variant in variants:
        variant.pk = None
        variant.service = service
        variant.save()

    return JsonResponse({'success': True, 'id': str(service.pk), 'name': service.name})


# =============================================================================
# Categories
# =============================================================================

@login_required
@with_module_nav('services', 'categories')
@htmx_view('services/pages/categories.html', 'services/partials/categories.html')
def category_list(request):
    """List categories."""
    hub = _hub(request)
    categories = ServiceCategory.objects.filter(
        hub_id=hub, is_deleted=False
    ).annotate(
        service_count=Count('services', filter=Q(services__is_deleted=False))
    ).order_by('sort_order', 'name')

    return {'categories': categories}


@login_required
@with_module_nav('services', 'categories')
@htmx_view('services/pages/category_detail.html', 'services/partials/category_detail.html')
def category_detail(request, pk):
    """Category detail with services."""
    hub = _hub(request)
    category = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not category:
        return JsonResponse({'error': 'Not found'}, status=404)

    services = Service.objects.filter(hub_id=hub, is_deleted=False, category=category).order_by('sort_order', 'name')
    children = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, parent=category).order_by('sort_order', 'name')

    return {
        'category': category,
        'services': services,
        'children': children,
    }


@login_required
def category_add(request):
    """Add a category."""
    hub = _hub(request)

    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit=False)
            category.hub_id = hub
            if not category.slug:
                category.slug = slugify(category.name)
            category.save()
            return JsonResponse({'success': True, 'id': str(category.pk), 'name': category.name})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceCategoryForm()
    form.fields['parent'].queryset = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
    return JsonResponse({'form': 'render'})


@login_required
def category_edit(request, pk):
    """Edit a category."""
    hub = _hub(request)
    category = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not category:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceCategoryForm(instance=category)
    form.fields['parent'].queryset = ServiceCategory.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True
    ).exclude(pk=pk)
    return JsonResponse({'form': 'render'})


@login_required
@require_POST
def category_delete(request, pk):
    """Soft delete a category."""
    hub = _hub(request)
    category = ServiceCategory.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not category:
        return JsonResponse({'error': 'Not found'}, status=404)

    # Move children to parent
    ServiceCategory.objects.filter(hub_id=hub, parent=category).update(parent=category.parent)
    # Unlink services
    Service.objects.filter(hub_id=hub, category=category).update(category=None)

    category.is_deleted = True
    category.deleted_at = timezone.now()
    category.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# =============================================================================
# Variants
# =============================================================================

@login_required
def variant_add(request, service_pk):
    """Add variant to a service."""
    hub = _hub(request)
    service = Service.objects.filter(hub_id=hub, is_deleted=False, pk=service_pk).first()
    if not service:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        form = ServiceVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.hub_id = hub
            variant.service = service
            variant.save()
            return JsonResponse({'success': True, 'id': str(variant.pk), 'name': variant.name})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceVariantForm()
    return JsonResponse({'form': 'render'})


@login_required
def variant_edit(request, pk):
    """Edit a variant."""
    hub = _hub(request)
    variant = ServiceVariant.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not variant:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        form = ServiceVariantForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceVariantForm(instance=variant)
    return JsonResponse({'form': 'render'})


@login_required
@require_POST
def variant_delete(request, pk):
    """Soft delete a variant."""
    hub = _hub(request)
    variant = ServiceVariant.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not variant:
        return JsonResponse({'error': 'Not found'}, status=404)

    variant.is_deleted = True
    variant.deleted_at = timezone.now()
    variant.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# =============================================================================
# Addons
# =============================================================================

@login_required
@with_module_nav('services', 'services')
@htmx_view('services/pages/addons.html', 'services/partials/addons.html')
def addon_list(request):
    """List addons."""
    hub = _hub(request)
    addons = ServiceAddon.objects.filter(hub_id=hub, is_deleted=False).prefetch_related('services').order_by('name')
    return {'addons': addons}


@login_required
def addon_add(request):
    """Add an addon."""
    hub = _hub(request)

    if request.method == 'POST':
        form = ServiceAddonForm(request.POST)
        if form.is_valid():
            addon = form.save(commit=False)
            addon.hub_id = hub
            addon.save()
            form.save_m2m()
            return JsonResponse({'success': True, 'id': str(addon.pk), 'name': addon.name})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceAddonForm()
    form.fields['services'].queryset = Service.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
    return JsonResponse({'form': 'render'})


@login_required
def addon_edit(request, pk):
    """Edit an addon."""
    hub = _hub(request)
    addon = ServiceAddon.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not addon:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        form = ServiceAddonForm(request.POST, instance=addon)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServiceAddonForm(instance=addon)
    form.fields['services'].queryset = Service.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
    return JsonResponse({'form': 'render'})


@login_required
@require_POST
def addon_delete(request, pk):
    """Soft delete an addon."""
    hub = _hub(request)
    addon = ServiceAddon.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not addon:
        return JsonResponse({'error': 'Not found'}, status=404)

    addon.is_deleted = True
    addon.deleted_at = timezone.now()
    addon.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# =============================================================================
# Packages
# =============================================================================

@login_required
@with_module_nav('services', 'packages')
@htmx_view('services/pages/packages.html', 'services/partials/packages.html')
def package_list(request):
    """List packages."""
    hub = _hub(request)
    packages = ServicePackage.objects.filter(hub_id=hub, is_deleted=False).order_by('sort_order', 'name')
    return {'packages': packages}


@login_required
@with_module_nav('services', 'packages')
@htmx_view('services/pages/package_detail.html', 'services/partials/package_detail.html')
def package_detail(request, pk):
    """Package detail with items."""
    hub = _hub(request)
    package = ServicePackage.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not package:
        return JsonResponse({'error': 'Not found'}, status=404)

    items = ServicePackageItem.objects.filter(
        package=package, is_deleted=False
    ).select_related('service').order_by('sort_order')

    return {
        'package': package,
        'items': items,
    }


@login_required
def package_add(request):
    """Add a package."""
    hub = _hub(request)

    if request.method == 'POST':
        form = ServicePackageForm(request.POST, request.FILES)
        if form.is_valid():
            package = form.save(commit=False)
            package.hub_id = hub
            if not package.slug:
                package.slug = slugify(package.name)
            package.save()
            return JsonResponse({'success': True, 'id': str(package.pk), 'name': package.name})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServicePackageForm()
    return JsonResponse({'form': 'render'})


@login_required
def package_edit(request, pk):
    """Edit a package."""
    hub = _hub(request)
    package = ServicePackage.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not package:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        form = ServicePackageForm(request.POST, request.FILES, instance=package)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = ServicePackageForm(instance=package)
    return JsonResponse({'form': 'render'})


@login_required
@require_POST
def package_delete(request, pk):
    """Soft delete a package."""
    hub = _hub(request)
    package = ServicePackage.objects.filter(hub_id=hub, is_deleted=False, pk=pk).first()
    if not package:
        return JsonResponse({'error': 'Not found'}, status=404)

    package.is_deleted = True
    package.deleted_at = timezone.now()
    package.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# =============================================================================
# API Endpoints
# =============================================================================

@login_required
@require_GET
def api_search(request):
    """Search services API."""
    hub = _hub(request)
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'results': []})

    services = Service.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True
    ).filter(
        Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q)
    ).select_related('category')[:20]

    results = [{
        'id': str(s.pk),
        'name': s.name,
        'price': str(s.price),
        'duration_minutes': s.duration_minutes,
        'category': s.category.name if s.category else None,
        'is_bookable': s.is_bookable,
    } for s in services]

    return JsonResponse({'results': results})


@login_required
@require_GET
def api_services_list(request):
    """List services API with filters."""
    hub = _hub(request)
    services = Service.objects.filter(hub_id=hub, is_deleted=False, is_active=True)

    category_id = request.GET.get('category')
    if category_id:
        services = services.filter(category_id=category_id)
    if request.GET.get('bookable') == 'true':
        services = services.filter(is_bookable=True)

    services = services.select_related('category').order_by('sort_order', 'name')

    results = [{
        'id': str(s.pk),
        'name': s.name,
        'slug': s.slug,
        'price': str(s.price),
        'price_display': s.get_price_display(),
        'duration_minutes': s.duration_minutes,
        'total_duration': s.total_duration,
        'category_id': str(s.category_id) if s.category_id else None,
        'category_name': s.category.name if s.category else None,
        'is_bookable': s.is_bookable,
        'max_capacity': s.max_capacity,
        'icon': s.icon,
        'color': s.color,
    } for s in services]

    return JsonResponse({'services': results})


@login_required
@require_GET
def api_service_detail(request, pk):
    """Service detail API with variants and addons."""
    hub = _hub(request)
    service = Service.objects.filter(hub_id=hub, is_deleted=False, pk=pk).select_related('category').first()
    if not service:
        return JsonResponse({'error': 'Not found'}, status=404)

    variants = [{
        'id': str(v.pk),
        'name': v.name,
        'price_adjustment': str(v.price_adjustment),
        'duration_adjustment': v.duration_adjustment,
        'final_price': str(v.final_price),
        'final_duration': v.final_duration,
    } for v in service.variants.filter(is_deleted=False, is_active=True)]

    addons = [{
        'id': str(a.pk),
        'name': a.name,
        'price': str(a.price),
        'duration_minutes': a.duration_minutes,
    } for a in ServiceAddon.objects.filter(hub_id=hub, is_deleted=False, is_active=True, services=service)]

    return JsonResponse({
        'id': str(service.pk),
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
        'category_id': str(service.category_id) if service.category_id else None,
        'category_name': service.category.name if service.category else None,
        'variants': variants,
        'addons': addons,
    })


# =============================================================================
# Settings
# =============================================================================

@login_required
@with_module_nav('services', 'settings')
@htmx_view('services/pages/settings.html', 'services/partials/settings.html')
def settings(request):
    """Settings page."""
    hub = _hub(request)
    s = ServicesSettings.get_settings(hub)
    form = ServicesSettingsForm(instance=s)
    return {'settings': s, 'form': form}


@login_required
@require_POST
def settings_save(request):
    """Save settings from JSON body."""
    hub = _hub(request)
    s = ServicesSettings.get_settings(hub)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = request.POST.dict()

    for field in ['default_duration', 'default_buffer_time']:
        if field in data:
            setattr(s, field, int(data[field]))
    for field in ['default_tax_rate']:
        if field in data:
            setattr(s, field, Decimal(str(data[field])))
    if 'currency' in data:
        s.currency = data['currency'][:3]

    s.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def settings_toggle(request):
    """Toggle boolean setting."""
    hub = _hub(request)
    s = ServicesSettings.get_settings(hub)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = request.POST.dict()

    field = data.get('field', '')
    toggleable = ['show_prices', 'show_duration', 'allow_online_booking', 'include_tax_in_price']

    if field not in toggleable:
        return JsonResponse({'error': 'Invalid field'}, status=400)

    setattr(s, field, not getattr(s, field))
    s.save()
    return JsonResponse({'success': True, 'value': getattr(s, field)})


@login_required
@require_POST
def settings_input(request):
    """Update numeric/text setting."""
    hub = _hub(request)
    s = ServicesSettings.get_settings(hub)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = request.POST.dict()

    field = data.get('field', '')
    value = data.get('value', '')

    numeric_fields = ['default_duration', 'default_buffer_time']
    decimal_fields = ['default_tax_rate']
    text_fields = ['currency']

    if field in numeric_fields:
        setattr(s, field, int(value))
    elif field in decimal_fields:
        setattr(s, field, Decimal(str(value)))
    elif field in text_fields:
        setattr(s, field, str(value)[:3] if field == 'currency' else str(value))
    else:
        return JsonResponse({'error': 'Invalid field'}, status=400)

    s.save()
    return JsonResponse({'success': True, 'value': str(getattr(s, field))})


@login_required
@require_POST
def settings_reset(request):
    """Reset settings to defaults."""
    hub = _hub(request)
    s = ServicesSettings.get_settings(hub)

    s.default_duration = 60
    s.default_buffer_time = 0
    s.default_tax_rate = Decimal('21.00')
    s.show_prices = True
    s.show_duration = True
    s.allow_online_booking = True
    s.include_tax_in_price = True
    s.currency = 'EUR'
    s.save()

    return JsonResponse({'success': True})
