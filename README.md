# Services Module

Service catalog management for appointment-based businesses like salons, spas, clinics, and consulting services.

## Features

- Service catalog with categories
- Duration and pricing management
- Staff service assignments
- Service add-ons and packages
- Integration with Appointments module
- Service-based reporting

## Installation

This module is installed automatically when activated in ERPlora Hub.

### Dependencies

- ERPlora Hub >= 1.0.0
- Optional: `appointments` >= 1.0.0 for scheduling
- Optional: `staff` >= 1.0.0 for staff assignments

## Configuration

Access module settings at `/m/services/settings/`.

### Available Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_duration_minutes` | integer | `60` | Default service duration |
| `show_prices` | boolean | `true` | Show prices in catalog |
| `require_staff` | boolean | `true` | Require staff assignment |

## Usage

### Views

| View | URL | Description |
|------|-----|-------------|
| Overview | `/m/services/` | Dashboard |
| Catalog | `/m/services/list/` | Service list |
| Categories | `/m/services/categories/` | Category management |
| Settings | `/m/services/settings/` | Module configuration |

## Permissions

| Permission | Description |
|------------|-------------|
| `services.view_service` | View services |
| `services.add_service` | Create services |
| `services.change_service` | Edit services |
| `services.delete_service` | Delete services |
| `services.view_category` | View categories |
| `services.add_category` | Create categories |
| `services.change_category` | Edit categories |
| `services.delete_category` | Delete categories |

## Module Icon

Location: `static/icons/icon.svg`

Icon source: [React Icons - Ionicons 5](https://react-icons.github.io/react-icons/icons/io5/)

---

**Version:** 1.0.0
**Category:** services
**Author:** ERPlora Team
