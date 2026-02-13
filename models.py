"""Services module models.

Models:
- ServicesSettings — per-hub configuration
- ServiceCategory — hierarchical categories
- Service — service with pricing, duration, booking options
- ServiceVariant — variants with price/duration adjustments
- ServiceAddon — add-ons for services
- ServicePackage — bundles of services at a discount
- ServicePackageItem — through model for package-service
"""

from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# ==============================================================================
# SETTINGS
# ==============================================================================

class ServicesSettings(HubBaseModel):
    """Per-hub services configuration."""

    default_duration = models.PositiveIntegerField(default=60, help_text=_('Default service duration in minutes'))
    default_buffer_time = models.PositiveIntegerField(default=0, help_text=_('Default buffer time between services'))
    default_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('21.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
    )
    show_prices = models.BooleanField(default=True, help_text=_('Display prices in catalog'))
    show_duration = models.BooleanField(default=True, help_text=_('Display duration in catalog'))
    allow_online_booking = models.BooleanField(default=True)
    include_tax_in_price = models.BooleanField(default=True, help_text=_('Prices include tax'))
    currency = models.CharField(max_length=3, default='EUR')

    class Meta(HubBaseModel.Meta):
        db_table = 'services_settings'
        verbose_name = _('Services Settings')
        verbose_name_plural = _('Services Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return f'Services Settings (hub {self.hub_id})'

    @classmethod
    def get_settings(cls, hub_id):
        obj, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return obj


# ==============================================================================
# CATEGORY
# ==============================================================================

class ServiceCategory(HubBaseModel):
    """Hierarchical service categories."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children',
    )
    icon = models.CharField(max_length=50, blank=True, help_text=_("Icon name"))
    color = models.CharField(max_length=7, blank=True, help_text=_("Hex color"))
    image = models.ImageField(upload_to='services/categories/', blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'services_category'
        verbose_name = _('Service Category')
        verbose_name_plural = _('Service Categories')
        ordering = ['sort_order', 'name']
        unique_together = [('hub_id', 'slug')]

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} > {self.name}'
        return self.name

    def clean(self):
        if self.parent == self:
            raise ValidationError(_('A category cannot be its own parent.'))
        if self.parent:
            ancestor = self.parent
            while ancestor:
                if ancestor == self:
                    raise ValidationError(_('Circular reference detected.'))
                ancestor = ancestor.parent

    @property
    def service_count(self):
        return self.services.filter(is_active=True, is_deleted=False).count()

    @property
    def total_service_count(self):
        count = self.service_count
        for child in self.children.filter(is_active=True, is_deleted=False):
            count += child.total_service_count
        return count

    def get_ancestors(self):
        ancestors = []
        ancestor = self.parent
        while ancestor:
            ancestors.insert(0, ancestor)
            ancestor = ancestor.parent
        return ancestors

    def get_descendants(self):
        descendants = []
        for child in self.children.filter(is_deleted=False):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


# ==============================================================================
# SERVICE
# ==============================================================================

class Service(HubBaseModel):
    """Service with pricing, duration, and booking options."""

    PRICING_TYPE_CHOICES = [
        ('fixed', _('Fixed Price')),
        ('hourly', _('Hourly Rate')),
        ('from', _('Starting From')),
        ('variable', _('Variable')),
        ('free', _('Free')),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='services',
    )

    # Pricing
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES, default='fixed')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0'))])
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0'))])
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0'))])
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0'))], help_text=_('Internal cost'))
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
    )

    # Duration
    duration_minutes = models.PositiveIntegerField(default=60, validators=[MinValueValidator(5)])
    buffer_before = models.PositiveIntegerField(default=0, help_text=_('Preparation time'))
    buffer_after = models.PositiveIntegerField(default=0, help_text=_('Cleanup time'))

    # Capacity
    max_capacity = models.PositiveIntegerField(default=1, help_text=_('Max simultaneous bookings'))

    # Media
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, blank=True)

    # Booking options
    is_bookable = models.BooleanField(default=True, help_text=_('Can be booked through appointments'))
    requires_confirmation = models.BooleanField(default=False)
    allow_online_booking = models.BooleanField(default=True)

    # Display
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Metadata
    sku = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'services_service'
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        ordering = ['sort_order', 'name']
        unique_together = [('hub_id', 'slug')]
        indexes = [
            models.Index(fields=['hub_id', 'is_active', 'is_bookable']),
            models.Index(fields=['hub_id', 'category_id']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.pricing_type == 'variable' and self.min_price and self.max_price:
            if self.min_price > self.max_price:
                raise ValidationError({'min_price': _('Minimum price cannot exceed maximum.')})

    @property
    def effective_tax_rate(self):
        if self.tax_rate is not None:
            return self.tax_rate
        settings = ServicesSettings.get_settings(self.hub_id)
        return settings.default_tax_rate

    @property
    def price_with_tax(self):
        settings = ServicesSettings.get_settings(self.hub_id)
        if settings.include_tax_in_price:
            return self.price
        tax = self.price * (self.effective_tax_rate / Decimal('100'))
        return self.price + tax

    @property
    def price_without_tax(self):
        settings = ServicesSettings.get_settings(self.hub_id)
        if not settings.include_tax_in_price:
            return self.price
        divisor = 1 + (self.effective_tax_rate / Decimal('100'))
        return self.price / divisor

    @property
    def tax_amount(self):
        return self.price_with_tax - self.price_without_tax

    @property
    def profit(self):
        return self.price_without_tax - self.cost

    @property
    def profit_margin(self):
        if self.price_without_tax == 0:
            return Decimal('0')
        return (self.profit / self.price_without_tax) * Decimal('100')

    @property
    def total_duration(self):
        return self.buffer_before + self.duration_minutes + self.buffer_after

    def get_price_display(self):
        if self.pricing_type == 'free':
            return _('Free')
        elif self.pricing_type == 'from':
            return _('From %(price)s') % {'price': self.price}
        elif self.pricing_type == 'variable':
            if self.min_price and self.max_price:
                return f'{self.min_price} - {self.max_price}'
            return _('Variable')
        elif self.pricing_type == 'hourly':
            return _('%(price)s/hour') % {'price': self.price}
        return str(self.price)


# ==============================================================================
# VARIANT
# ==============================================================================

class ServiceVariant(HubBaseModel):
    """Variant of a service with price/duration adjustments."""

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text=_('Added to base price'))
    duration_adjustment = models.IntegerField(default=0, help_text=_('Added to base duration (min)'))
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'services_variant'
        verbose_name = _('Service Variant')
        verbose_name_plural = _('Service Variants')
        ordering = ['sort_order', 'name']
        unique_together = [('service', 'name')]

    def __str__(self):
        return f'{self.service.name} — {self.name}'

    @property
    def final_price(self):
        return self.service.price + self.price_adjustment

    @property
    def final_duration(self):
        return self.service.duration_minutes + self.duration_adjustment


# ==============================================================================
# ADDON
# ==============================================================================

class ServiceAddon(HubBaseModel):
    """Add-on that can be added to services."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0'))])
    duration_minutes = models.PositiveIntegerField(default=0)
    services = models.ManyToManyField(Service, blank=True, related_name='addons')
    is_active = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'services_addon'
        verbose_name = _('Service Addon')
        verbose_name_plural = _('Service Addons')
        ordering = ['name']

    def __str__(self):
        return self.name


# ==============================================================================
# PACKAGE
# ==============================================================================

class ServicePackage(HubBaseModel):
    """Package combining multiple services at a discount."""

    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    services = models.ManyToManyField(Service, through='ServicePackageItem', related_name='packages')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text=_('Overrides calculated price'))
    validity_days = models.PositiveIntegerField(null=True, blank=True, help_text=_('Days to use after purchase'))
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='services/packages/', blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta(HubBaseModel.Meta):
        db_table = 'services_package'
        verbose_name = _('Service Package')
        verbose_name_plural = _('Service Packages')
        ordering = ['sort_order', 'name']
        unique_together = [('hub_id', 'slug')]

    def __str__(self):
        return self.name

    @property
    def original_price(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.service.price * item.quantity
        return total

    @property
    def final_price(self):
        if self.fixed_price is not None:
            return self.fixed_price
        original = self.original_price
        if self.discount_type == 'percentage':
            discount = original * (self.discount_value / Decimal('100'))
        else:
            discount = self.discount_value
        return max(Decimal('0.00'), original - discount)

    @property
    def savings(self):
        return self.original_price - self.final_price

    @property
    def savings_percentage(self):
        if self.original_price == 0:
            return Decimal('0')
        return (self.savings / self.original_price) * Decimal('100')

    @property
    def total_duration(self):
        total = 0
        for item in self.items.all():
            total += item.service.duration_minutes * item.quantity
        return total


class ServicePackageItem(HubBaseModel):
    """Through model for package-service relationship."""

    package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='package_items')
    quantity = models.PositiveIntegerField(default=1)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta(HubBaseModel.Meta):
        db_table = 'services_packageitem'
        verbose_name = _('Package Item')
        verbose_name_plural = _('Package Items')
        ordering = ['sort_order']
        unique_together = [('package', 'service')]

    def __str__(self):
        return f'{self.package.name} — {self.service.name} x{self.quantity}'
