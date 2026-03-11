"""
AI context for the Services module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Services

### Models

**ServicesSettings** (singleton per hub)
- default_duration (min, 60), default_buffer_time (min, 0)
- default_tax_rate (Decimal, 21.00%), currency (str, 'EUR')
- show_prices, show_duration, allow_online_booking, include_tax_in_price (bools)

**ServiceCategory**
- name, slug (unique per hub), description
- parent (FK → self, optional) — supports hierarchical categories
- icon, color (hex), image, sort_order, is_active
- Property: service_count (active services), total_service_count (including subcategories)

**Service**
- name, slug (unique per hub), description, short_description
- category (FK → ServiceCategory, optional)
- pricing_type: fixed | hourly | from | variable | free
- price (Decimal), min_price/max_price (for variable pricing)
- cost (internal cost for margin calculation)
- tax_rate (Decimal, optional — falls back to ServicesSettings.default_tax_rate)
- duration_minutes (min 5), buffer_before, buffer_after (preparation/cleanup minutes)
- max_capacity (simultaneous bookings, default 1)
- is_bookable (bool), requires_confirmation (bool), allow_online_booking (bool)
- is_active, is_featured, sort_order
- sku, barcode (for POS integration)
- Properties: effective_tax_rate, price_with_tax, price_without_tax, tax_amount, profit, profit_margin, total_duration (buffer_before + duration + buffer_after)

**ServiceVariant**
- service (FK → Service, related_name='variants'), name (unique per service)
- price_adjustment (added to base price), duration_adjustment (minutes, can be negative)
- sort_order, is_active
- Properties: final_price, final_duration

**ServiceAddon**
- name, description, price, duration_minutes
- services (M2M → Service, related_name='addons')
- is_active

**ServicePackage**
- name, slug (unique per hub), description
- services (M2M → Service via ServicePackageItem)
- discount_type: percentage | fixed
- discount_value, fixed_price (overrides calculated price if set)
- validity_days (after purchase), max_uses
- is_active, is_featured, sort_order
- Properties: original_price (sum of items), final_price (after discount), savings, savings_percentage, total_duration

**ServicePackageItem** (through model)
- package (FK → ServicePackage), service (FK → Service), quantity (int, default 1)
- Unique: (package, service)

### Key flows

1. **Create service catalog**: Create ServiceCategory → Create Service linked to category
2. **Add variants**: Create ServiceVariant for the same service with different prices/durations (e.g. Short / Long)
3. **Add add-ons**: Create ServiceAddon and link to one or more services via M2M
4. **Create package**: Create ServicePackage → Create ServicePackageItem for each included service + quantity
5. **Staff assignment**: Create staff.StaffService to link a StaffMember to a Service

### Relationships

- Service.category → ServiceCategory
- ServiceVariant.service → Service
- ServiceAddon.services → Service (M2M)
- ServicePackage.services → Service (through ServicePackageItem)
- appointments.Appointment.service → Service
- staff.StaffService.service → Service
"""
