# Services

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `services` |
| **Version** | `1.0.0` |
| **Dependencies** | None |

## Models

### `ServicesSettings`

Per-hub services configuration.

| Field | Type | Details |
|-------|------|---------|
| `default_duration` | PositiveIntegerField |  |
| `default_buffer_time` | PositiveIntegerField |  |
| `default_tax_rate` | DecimalField |  |
| `show_prices` | BooleanField |  |
| `show_duration` | BooleanField |  |
| `allow_online_booking` | BooleanField |  |
| `include_tax_in_price` | BooleanField |  |
| `currency` | CharField | max_length=3 |

**Methods:**

- `get_settings()`

### `ServiceCategory`

Hierarchical service categories.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `slug` | SlugField | max_length=100 |
| `description` | TextField | optional |
| `parent` | ForeignKey | → `services.ServiceCategory`, on_delete=CASCADE, optional |
| `icon` | CharField | max_length=50, optional |
| `color` | CharField | max_length=7, optional |
| `image` | ImageField | max_length=100, optional |
| `sort_order` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |

**Methods:**

- `get_ancestors()`
- `get_descendants()`

**Properties:**

- `service_count`
- `total_service_count`

### `Service`

Service with pricing, duration, and booking options.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=200 |
| `slug` | SlugField | max_length=200 |
| `description` | TextField | optional |
| `short_description` | CharField | max_length=200, optional |
| `category` | ForeignKey | → `services.ServiceCategory`, on_delete=SET_NULL, optional |
| `pricing_type` | CharField | max_length=20, choices: fixed, hourly, from, variable, free |
| `price` | DecimalField |  |
| `min_price` | DecimalField | optional |
| `max_price` | DecimalField | optional |
| `cost` | DecimalField |  |
| `tax_rate` | DecimalField | optional |
| `duration_minutes` | PositiveIntegerField |  |
| `buffer_before` | PositiveIntegerField |  |
| `buffer_after` | PositiveIntegerField |  |
| `max_capacity` | PositiveIntegerField |  |
| `image` | ImageField | max_length=100, optional |
| `icon` | CharField | max_length=50, optional |
| `color` | CharField | max_length=7, optional |
| `is_bookable` | BooleanField |  |
| `requires_confirmation` | BooleanField |  |
| `allow_online_booking` | BooleanField |  |
| `sort_order` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |
| `is_featured` | BooleanField |  |
| `sku` | CharField | max_length=50, optional |
| `barcode` | CharField | max_length=50, optional |
| `notes` | TextField | optional |

**Methods:**

- `get_price_display()`

**Properties:**

- `effective_tax_rate`
- `price_with_tax`
- `price_without_tax`
- `tax_amount`
- `profit`
- `profit_margin`
- `total_duration`

### `ServiceVariant`

Variant of a service with price/duration adjustments.

| Field | Type | Details |
|-------|------|---------|
| `service` | ForeignKey | → `services.Service`, on_delete=CASCADE |
| `name` | CharField | max_length=100 |
| `description` | TextField | optional |
| `price_adjustment` | DecimalField |  |
| `duration_adjustment` | IntegerField |  |
| `sort_order` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |

**Properties:**

- `final_price`
- `final_duration`

### `ServiceAddon`

Add-on that can be added to services.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `description` | TextField | optional |
| `price` | DecimalField |  |
| `duration_minutes` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |
| `services` | ManyToManyField | → `services.Service`, optional |

### `ServicePackage`

Package combining multiple services at a discount.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=200 |
| `slug` | SlugField | max_length=200 |
| `description` | TextField | optional |
| `discount_type` | CharField | max_length=20, choices: percentage, fixed |
| `discount_value` | DecimalField |  |
| `fixed_price` | DecimalField | optional |
| `validity_days` | PositiveIntegerField | optional |
| `max_uses` | PositiveIntegerField | optional |
| `image` | ImageField | max_length=100, optional |
| `sort_order` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |
| `is_featured` | BooleanField |  |
| `services` | ManyToManyField | → `services.Service` |

**Properties:**

- `original_price`
- `final_price`
- `savings`
- `savings_percentage`
- `total_duration`

### `ServicePackageItem`

Through model for package-service relationship.

| Field | Type | Details |
|-------|------|---------|
| `package` | ForeignKey | → `services.ServicePackage`, on_delete=CASCADE |
| `service` | ForeignKey | → `services.Service`, on_delete=CASCADE |
| `quantity` | PositiveIntegerField |  |
| `sort_order` | PositiveIntegerField |  |

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `ServiceCategory` | `parent` | `services.ServiceCategory` | CASCADE | Yes |
| `Service` | `category` | `services.ServiceCategory` | SET_NULL | Yes |
| `ServiceVariant` | `service` | `services.Service` | CASCADE | No |
| `ServicePackageItem` | `package` | `services.ServicePackage` | CASCADE | No |
| `ServicePackageItem` | `service` | `services.Service` | CASCADE | No |

## URL Endpoints

Base path: `/m/services/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `index` | GET |
| `services/` | `services` | GET |
| `dashboard/` | `dashboard` | GET |
| `list/` | `list` | GET |
| `create/` | `create` | GET/POST |
| `<uuid:pk>/` | `detail` | GET |
| `<uuid:pk>/edit/` | `edit` | GET |
| `<uuid:pk>/delete/` | `delete` | GET/POST |
| `<uuid:pk>/toggle/` | `toggle` | GET |
| `<uuid:pk>/duplicate/` | `duplicate` | GET |
| `categories/` | `categories` | GET |
| `categories/add/` | `category_add` | GET/POST |
| `categories/<uuid:pk>/` | `category_detail` | GET |
| `categories/<uuid:pk>/edit/` | `category_edit` | GET |
| `categories/<uuid:pk>/delete/` | `category_delete` | GET/POST |
| `<uuid:service_pk>/variants/add/` | `variant_add` | GET/POST |
| `variants/<uuid:pk>/edit/` | `variant_edit` | GET |
| `variants/<uuid:pk>/delete/` | `variant_delete` | GET/POST |
| `addons/` | `addon_list` | GET/POST |
| `addons/add/` | `addon_add` | GET/POST |
| `addons/<uuid:pk>/edit/` | `addon_edit` | GET/POST |
| `addons/<uuid:pk>/delete/` | `addon_delete` | GET/POST |
| `packages/` | `package_list` | GET |
| `packages/add/` | `package_add` | GET/POST |
| `packages/<uuid:pk>/` | `package_detail` | GET |
| `packages/<uuid:pk>/edit/` | `package_edit` | GET |
| `packages/<uuid:pk>/delete/` | `package_delete` | GET/POST |
| `api/search/` | `api_search` | GET |
| `api/services/` | `api_services` | GET |
| `api/services/<uuid:pk>/` | `api_service_detail` | GET |
| `settings/` | `settings` | GET |
| `settings/save/` | `settings_save` | GET/POST |
| `settings/toggle/` | `settings_toggle` | GET |
| `settings/input/` | `settings_input` | GET |
| `settings/reset/` | `settings_reset` | GET |

## Permissions

| Permission | Description |
|------------|-------------|
| `services.view_service` | View Service |
| `services.add_service` | Add Service |
| `services.change_service` | Change Service |
| `services.delete_service` | Delete Service |
| `services.view_category` | View Category |
| `services.add_category` | Add Category |
| `services.change_category` | Change Category |
| `services.delete_category` | Delete Category |
| `services.view_package` | View Package |
| `services.add_package` | Add Package |
| `services.change_package` | Change Package |
| `services.delete_package` | Delete Package |
| `services.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_category`, `add_package`, `add_service`, `change_category`, `change_package`, `change_service`, `view_category`, `view_package` (+1 more)
- **employee**: `add_service`, `view_category`, `view_package`, `view_service`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Overview | `grid-outline` | `dashboard` | No |
| Services | `briefcase-outline` | `services` | No |
| Categories | `folder-outline` | `categories` | No |
| Packages | `gift-outline` | `packages` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_services`

List services with optional search. Returns name, price, duration, category.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Search by name |
| `category_id` | string | No | Filter by category ID |
| `limit` | integer | No | Max results (default 20) |

### `create_service`

Create a new service.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Service name |
| `price` | string | Yes | Price |
| `pricing_type` | string | No | Pricing type: fixed, hourly, from, variable, free |
| `duration_minutes` | integer | No | Duration in minutes |
| `description` | string | No | Service description |
| `is_bookable` | boolean | No | Can be booked online |
| `category_id` | string | No | Category ID |

### `list_service_categories`

List service categories.

### `create_service_category`

Create a service category (e.g., 'Cortes', 'Color', 'Tratamientos').

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Category name |
| `icon` | string | No | Icon name |
| `color` | string | No | Hex color |

### `update_service`

Update an existing service.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `service_id` | string | Yes | Service ID |
| `name` | string | No |  |
| `price` | string | No |  |
| `duration_minutes` | integer | No |  |
| `description` | string | No |  |
| `is_bookable` | boolean | No |  |
| `category_id` | string | No |  |

## File Structure

```
CHANGELOG.md
README.md
TODO.md
__init__.py
ai_tools.py
apps.py
forms.py
locale/
  es/
    LC_MESSAGES/
      django.po
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
static/
  icons/
    ion/
templates/
  services/
    pages/
      addons.html
      categories.html
      category_detail.html
      dashboard.html
      detail.html
      form.html
      list.html
      package_detail.html
      packages.html
      settings.html
    partials/
      addons.html
      categories.html
      category_detail.html
      dashboard.html
      detail.html
      form.html
      list.html
      package_detail.html
      packages.html
      service_list_items.html
      settings.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_services.py
  test_views.py
urls.py
views.py
```
