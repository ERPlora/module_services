"""
Services module models.
Manages service catalog, categories, pricing, and durations.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class ServicesConfig(models.Model):
    """
    Singleton configuration for services module.
    Stores global settings for service management.
    """
    # Default settings
    default_duration = models.PositiveIntegerField(
        _("Default Duration (minutes)"),
        default=60,
        help_text=_("Default service duration in minutes")
    )
    default_buffer_time = models.PositiveIntegerField(
        _("Buffer Time (minutes)"),
        default=0,
        help_text=_("Default buffer time between services")
    )
    default_tax_rate = models.DecimalField(
        _("Default Tax Rate"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('21.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    # Display options
    show_prices = models.BooleanField(
        _("Show Prices"),
        default=True,
        help_text=_("Display prices in service catalog")
    )
    show_duration = models.BooleanField(
        _("Show Duration"),
        default=True,
        help_text=_("Display duration in service catalog")
    )
    allow_online_booking = models.BooleanField(
        _("Allow Online Booking"),
        default=True,
        help_text=_("Allow services to be booked online")
    )

    # Pricing options
    include_tax_in_price = models.BooleanField(
        _("Include Tax in Price"),
        default=True,
        help_text=_("Prices include tax")
    )
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        default='EUR'
    )
    price_decimal_places = models.PositiveSmallIntegerField(
        _("Price Decimal Places"),
        default=2,
        validators=[MaxValueValidator(4)]
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Services Configuration")
        verbose_name_plural = _("Services Configuration")

    def __str__(self):
        return "Services Configuration"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class ServiceCategory(models.Model):
    """
    Service category for organizing services.
    Supports hierarchical categories with parent-child relationships.
    """
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Category")
    )
    icon = models.CharField(
        _("Icon"),
        max_length=50,
        blank=True,
        help_text=_("Icon name (e.g., 'cut-outline')")
    )
    color = models.CharField(
        _("Color"),
        max_length=7,
        blank=True,
        help_text=_("Hex color code (e.g., '#3880ff')")
    )
    image = models.ImageField(
        _("Image"),
        upload_to='services/categories/',
        blank=True,
        null=True
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def clean(self):
        """Validate that category doesn't have itself as parent."""
        if self.parent == self:
            raise ValidationError(_("A category cannot be its own parent."))
        # Check for circular reference
        if self.parent:
            ancestor = self.parent
            while ancestor:
                if ancestor == self:
                    raise ValidationError(_("Circular reference detected in category hierarchy."))
                ancestor = ancestor.parent

    @property
    def service_count(self):
        """Get count of active services in this category."""
        return self.services.filter(is_active=True).count()

    @property
    def total_service_count(self):
        """Get count of all services including subcategories."""
        count = self.service_count
        for child in self.children.filter(is_active=True):
            count += child.total_service_count
        return count

    def get_ancestors(self):
        """Get all ancestor categories."""
        ancestors = []
        ancestor = self.parent
        while ancestor:
            ancestors.insert(0, ancestor)
            ancestor = ancestor.parent
        return ancestors

    def get_descendants(self):
        """Get all descendant categories."""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Service(models.Model):
    """
    Service model representing a service offered.
    Can be linked to appointments for booking.
    """
    PRICING_TYPE_CHOICES = [
        ('fixed', _("Fixed Price")),
        ('hourly', _("Hourly Rate")),
        ('from', _("Starting From")),
        ('variable', _("Variable")),
        ('free', _("Free")),
    ]

    # Basic info
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=200, unique=True)
    description = models.TextField(_("Description"), blank=True)
    short_description = models.CharField(
        _("Short Description"),
        max_length=200,
        blank=True
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        verbose_name=_("Category")
    )

    # Pricing
    pricing_type = models.CharField(
        _("Pricing Type"),
        max_length=20,
        choices=PRICING_TYPE_CHOICES,
        default='fixed'
    )
    price = models.DecimalField(
        _("Price"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    min_price = models.DecimalField(
        _("Minimum Price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    max_price = models.DecimalField(
        _("Maximum Price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    cost = models.DecimalField(
        _("Cost"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text=_("Internal cost for profit calculation")
    )
    tax_rate = models.DecimalField(
        _("Tax Rate (%)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    # Duration
    duration_minutes = models.PositiveIntegerField(
        _("Duration (minutes)"),
        default=60,
        validators=[MinValueValidator(5)]
    )
    buffer_before = models.PositiveIntegerField(
        _("Buffer Before (minutes)"),
        default=0,
        help_text=_("Preparation time before service")
    )
    buffer_after = models.PositiveIntegerField(
        _("Buffer After (minutes)"),
        default=0,
        help_text=_("Cleanup time after service")
    )

    # Capacity
    max_capacity = models.PositiveIntegerField(
        _("Maximum Capacity"),
        default=1,
        help_text=_("Maximum simultaneous bookings")
    )

    # Media
    image = models.ImageField(
        _("Image"),
        upload_to='services/',
        blank=True,
        null=True
    )
    icon = models.CharField(
        _("Icon"),
        max_length=50,
        blank=True
    )
    color = models.CharField(
        _("Color"),
        max_length=7,
        blank=True
    )

    # Booking options
    is_bookable = models.BooleanField(
        _("Is Bookable"),
        default=True,
        help_text=_("Can be booked through appointments")
    )
    requires_confirmation = models.BooleanField(
        _("Requires Confirmation"),
        default=False,
        help_text=_("Booking requires staff confirmation")
    )
    allow_online_booking = models.BooleanField(
        _("Allow Online Booking"),
        default=True
    )

    # Display
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    is_featured = models.BooleanField(
        _("Featured"),
        default=False,
        help_text=_("Show in featured services")
    )

    # Metadata
    sku = models.CharField(
        _("SKU"),
        max_length=50,
        blank=True,
        unique=True,
        null=True
    )
    barcode = models.CharField(
        _("Barcode"),
        max_length=50,
        blank=True
    )
    notes = models.TextField(_("Internal Notes"), blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate price ranges."""
        if self.pricing_type == 'variable':
            if self.min_price and self.max_price:
                if self.min_price > self.max_price:
                    raise ValidationError({
                        'min_price': _("Minimum price cannot be greater than maximum price.")
                    })

    @property
    def effective_tax_rate(self):
        """Get effective tax rate (service-specific or default)."""
        if self.tax_rate is not None:
            return self.tax_rate
        config = ServicesConfig.get_config()
        return config.default_tax_rate

    @property
    def price_with_tax(self):
        """Calculate price including tax."""
        config = ServicesConfig.get_config()
        if config.include_tax_in_price:
            return self.price
        tax = self.price * (self.effective_tax_rate / Decimal('100'))
        return self.price + tax

    @property
    def price_without_tax(self):
        """Calculate price excluding tax."""
        config = ServicesConfig.get_config()
        if not config.include_tax_in_price:
            return self.price
        divisor = 1 + (self.effective_tax_rate / Decimal('100'))
        return self.price / divisor

    @property
    def tax_amount(self):
        """Calculate tax amount."""
        return self.price_with_tax - self.price_without_tax

    @property
    def profit(self):
        """Calculate profit per service."""
        return self.price_without_tax - self.cost

    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.price_without_tax == 0:
            return Decimal('0')
        return (self.profit / self.price_without_tax) * Decimal('100')

    @property
    def total_duration(self):
        """Get total duration including buffers."""
        return self.buffer_before + self.duration_minutes + self.buffer_after

    def get_price_display(self):
        """Get formatted price for display."""
        config = ServicesConfig.get_config()
        if self.pricing_type == 'free':
            return _("Free")
        elif self.pricing_type == 'from':
            return _("From %(price)s") % {'price': self.price}
        elif self.pricing_type == 'variable':
            if self.min_price and self.max_price:
                return f"{self.min_price} - {self.max_price}"
            return _("Variable")
        elif self.pricing_type == 'hourly':
            return _("%(price)s/hour") % {'price': self.price}
        return str(self.price)


class ServiceVariant(models.Model):
    """
    Service variant for services with multiple options.
    E.g., Haircut - Short, Medium, Long with different prices/durations.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_("Service")
    )
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    price_adjustment = models.DecimalField(
        _("Price Adjustment"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Added to base service price")
    )
    duration_adjustment = models.IntegerField(
        _("Duration Adjustment (minutes)"),
        default=0,
        help_text=_("Added to base service duration")
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Service Variant")
        verbose_name_plural = _("Service Variants")
        ordering = ['order', 'name']
        unique_together = ['service', 'name']

    def __str__(self):
        return f"{self.service.name} - {self.name}"

    @property
    def final_price(self):
        """Calculate final price with adjustment."""
        return self.service.price + self.price_adjustment

    @property
    def final_duration(self):
        """Calculate final duration with adjustment."""
        return self.service.duration_minutes + self.duration_adjustment


class ServiceAddon(models.Model):
    """
    Service addon that can be added to services.
    E.g., Deep conditioning for hair services.
    """
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    price = models.DecimalField(
        _("Price"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    duration_minutes = models.PositiveIntegerField(
        _("Duration (minutes)"),
        default=0
    )
    services = models.ManyToManyField(
        Service,
        blank=True,
        related_name='addons',
        verbose_name=_("Available for Services")
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Service Addon")
        verbose_name_plural = _("Service Addons")
        ordering = ['name']

    def __str__(self):
        return self.name


class ServicePackage(models.Model):
    """
    Service package combining multiple services at a discount.
    """
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=200, unique=True)
    description = models.TextField(_("Description"), blank=True)
    services = models.ManyToManyField(
        Service,
        through='ServicePackageItem',
        related_name='packages',
        verbose_name=_("Services")
    )
    discount_type = models.CharField(
        _("Discount Type"),
        max_length=20,
        choices=[
            ('percentage', _("Percentage")),
            ('fixed', _("Fixed Amount")),
        ],
        default='percentage'
    )
    discount_value = models.DecimalField(
        _("Discount Value"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    fixed_price = models.DecimalField(
        _("Fixed Price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("If set, overrides calculated price")
    )
    validity_days = models.PositiveIntegerField(
        _("Validity (days)"),
        null=True,
        blank=True,
        help_text=_("Days to use package after purchase")
    )
    max_uses = models.PositiveIntegerField(
        _("Maximum Uses"),
        null=True,
        blank=True,
        help_text=_("Maximum times package can be used")
    )
    image = models.ImageField(
        _("Image"),
        upload_to='services/packages/',
        blank=True,
        null=True
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    is_featured = models.BooleanField(_("Featured"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Service Package")
        verbose_name_plural = _("Service Packages")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def original_price(self):
        """Calculate total price of all services."""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.service.price * item.quantity
        return total

    @property
    def final_price(self):
        """Calculate discounted price."""
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
        """Calculate total savings."""
        return self.original_price - self.final_price

    @property
    def savings_percentage(self):
        """Calculate savings as percentage."""
        if self.original_price == 0:
            return Decimal('0')
        return (self.savings / self.original_price) * Decimal('100')

    @property
    def total_duration(self):
        """Calculate total duration of all services."""
        total = 0
        for item in self.items.all():
            total += item.service.duration_minutes * item.quantity
        return total


class ServicePackageItem(models.Model):
    """
    Through model for package-service relationship.
    """
    package = models.ForeignKey(
        ServicePackage,
        on_delete=models.CASCADE,
        related_name='items'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='package_items'
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Package Item")
        verbose_name_plural = _("Package Items")
        ordering = ['order']
        unique_together = ['package', 'service']

    def __str__(self):
        return f"{self.package.name} - {self.service.name} x{self.quantity}"
