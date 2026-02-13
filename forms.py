"""Services forms."""

from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Service,
    ServiceCategory,
    ServiceVariant,
    ServiceAddon,
    ServicePackage,
    ServicesSettings,
)


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'name', 'slug', 'description', 'short_description', 'category',
            'pricing_type', 'price', 'min_price', 'max_price', 'cost', 'tax_rate',
            'duration_minutes', 'buffer_before', 'buffer_after', 'max_capacity',
            'image', 'icon', 'color',
            'is_bookable', 'requires_confirmation', 'allow_online_booking',
            'sort_order', 'is_active', 'is_featured',
            'sku', 'barcode', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'slug': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'short_description': forms.TextInput(attrs={'class': 'input'}),
            'category': forms.Select(attrs={'class': 'select'}),
            'pricing_type': forms.Select(attrs={'class': 'select'}),
            'price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'min_price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'max_price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'cost': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0', 'max': '100'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'input', 'min': '5'}),
            'buffer_before': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'buffer_after': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'max_capacity': forms.NumberInput(attrs={'class': 'input', 'min': '1'}),
            'icon': forms.TextInput(attrs={'class': 'input'}),
            'color': forms.TextInput(attrs={'class': 'input', 'type': 'color'}),
            'is_bookable': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'requires_confirmation': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'allow_online_booking': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'sort_order': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'sku': forms.TextInput(attrs={'class': 'input'}),
            'barcode': forms.TextInput(attrs={'class': 'input'}),
            'notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
        }


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'slug', 'description', 'parent', 'icon', 'color', 'image', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'slug': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
            'parent': forms.Select(attrs={'class': 'select'}),
            'icon': forms.TextInput(attrs={'class': 'input'}),
            'color': forms.TextInput(attrs={'class': 'input', 'type': 'color'}),
            'sort_order': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class ServiceVariantForm(forms.ModelForm):
    class Meta:
        model = ServiceVariant
        fields = ['name', 'description', 'price_adjustment', 'duration_adjustment', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
            'price_adjustment': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'duration_adjustment': forms.NumberInput(attrs={'class': 'input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class ServiceAddonForm(forms.ModelForm):
    class Meta:
        model = ServiceAddon
        fields = ['name', 'description', 'price', 'duration_minutes', 'services', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
            'price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'services': forms.SelectMultiple(attrs={'class': 'select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class ServicePackageForm(forms.ModelForm):
    class Meta:
        model = ServicePackage
        fields = [
            'name', 'slug', 'description', 'discount_type', 'discount_value',
            'fixed_price', 'validity_days', 'max_uses', 'image',
            'sort_order', 'is_active', 'is_featured',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'slug': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'discount_type': forms.Select(attrs={'class': 'select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'fixed_price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'validity_days': forms.NumberInput(attrs={'class': 'input', 'min': '1'}),
            'max_uses': forms.NumberInput(attrs={'class': 'input', 'min': '1'}),
            'sort_order': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class ServiceFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input', 'placeholder': _('Search services...')}))
    category = forms.ModelChoiceField(required=False, queryset=ServiceCategory.objects.none(), widget=forms.Select(attrs={'class': 'select'}))
    pricing_type = forms.ChoiceField(required=False, choices=[('', _('All types'))] + Service.PRICING_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'select'}))
    is_active = forms.NullBooleanField(required=False, widget=forms.Select(attrs={'class': 'select'}, choices=[('', _('All')), ('true', _('Active')), ('false', _('Inactive'))]))


class ServicesSettingsForm(forms.ModelForm):
    class Meta:
        model = ServicesSettings
        fields = [
            'default_duration', 'default_buffer_time', 'default_tax_rate',
            'show_prices', 'show_duration', 'allow_online_booking',
            'include_tax_in_price', 'currency',
        ]
        widgets = {
            'default_duration': forms.NumberInput(attrs={'class': 'input', 'min': '5'}),
            'default_buffer_time': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'default_tax_rate': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0', 'max': '100'}),
            'show_prices': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'show_duration': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'allow_online_booking': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'include_tax_in_price': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'currency': forms.TextInput(attrs={'class': 'input', 'maxlength': '3'}),
        }
