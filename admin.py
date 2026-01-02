from django.contrib import admin
from .models import (
    ServicesConfig,
    ServiceCategory,
    Service,
    ServiceVariant,
    ServiceAddon,
    ServicePackage,
    ServicePackageItem,
)


@admin.register(ServicesConfig)
class ServicesConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'default_duration', 'default_tax_rate', 'updated_at']


class ServiceVariantInline(admin.TabularInline):
    model = ServiceVariant
    extra = 0


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'is_active', 'service_count']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration_minutes', 'is_active', 'is_bookable']
    list_filter = ['is_active', 'is_bookable', 'category', 'pricing_type']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ServiceVariantInline]
    ordering = ['order', 'name']


@admin.register(ServiceAddon)
class ServiceAddonAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_minutes', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['services']


class ServicePackageItemInline(admin.TabularInline):
    model = ServicePackageItem
    extra = 0


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'final_price', 'discount_type', 'discount_value', 'is_active']
    list_filter = ['is_active', 'is_featured', 'discount_type']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ServicePackageItemInline]
