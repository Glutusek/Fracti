from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django import forms
from django.contrib.gis.geos import Point
from .models import Receipt, Product, Settlement


# Default map configuration constants
DEFAULT_LONGITUDE = 21.0122
DEFAULT_LATITUDE = 52.2297
DEFAULT_ZOOM = 12
POINT_ZOOM = 14


class MapItemAdminForm(forms.ModelForm):
    latitude = forms.FloatField(
        required=False,
        label="Szerokość (Lat)",
        help_text="Np. 52.2297 (Warszawa)",
        widget=forms.NumberInput(attrs={'step': '0.1', 'placeholder': '52.2297'})
    )
    longitude = forms.FloatField(
        required=False,
        label="Długość (Lon)",
        help_text="Np. 21.0122 (Warszawa)",
        widget=forms.NumberInput(attrs={'step': '0.1', 'placeholder': '21.0122'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.location:
            self.fields['longitude'].initial = self.instance.location.x
            self.fields['latitude'].initial = self.instance.location.y
        elif not self.instance.pk:
            self.fields['latitude'].initial = DEFAULT_LATITUDE
            self.fields['longitude'].initial = DEFAULT_LONGITUDE

    def save(self, commit=True):
        instance = super().save(commit=False)
        lat = self.cleaned_data.get('latitude')
        lon = self.cleaned_data.get('longitude')

        if lat is not None and lon is not None:
            instance.location = Point(lon, lat)

        if commit:
            instance.save()
        return instance

class ReceiptForm(MapItemAdminForm):
    class Meta:
        model = Receipt
        fields = '__all__'


@admin.register(Receipt)
class ReceiptAdmin(GISModelAdmin):
    form = ReceiptForm
    list_display = ('merchant_name', 'purchase_date', 'total_amount', 'id')
    
    default_lon = DEFAULT_LONGITUDE
    default_lat = DEFAULT_LATITUDE
    default_zoom = DEFAULT_ZOOM
    point_zoom = POINT_ZOOM
    
    gis_widget_kwargs = {
        'attrs': {
            'default_lon': DEFAULT_LONGITUDE,
            'default_lat': DEFAULT_LATITUDE,
            'default_zoom': DEFAULT_ZOOM,
        }
    }

    fieldsets = (
        (None, {
            'fields': ('merchant_name', 'purchase_date', 'total_amount', 'image', 'purchaser', 'settlement', 'category')
        }),
        ('Lokalizacja', {
            'fields': ('location', 'latitude', 'longitude'),
            'description': 'Zaznacz punkt na mapie lub wpisz współrzędne poniżej.'
        }),
    )

    class Media:
        js = ('receipts/js/map_sync.js',)


class ProductForm(MapItemAdminForm):
    class Meta:
        model = Product
        fields = '__all__'


@admin.register(Product)
class ProductAdmin(GISModelAdmin):
    form = ProductForm
    list_display = ('name', 'price', 'receipt', 'id')
    list_filter = ('receipt',)
    
    default_lon = DEFAULT_LONGITUDE
    default_lat = DEFAULT_LATITUDE
    default_zoom = DEFAULT_ZOOM
    point_zoom = POINT_ZOOM
    
    gis_widget_kwargs = {
        'attrs': {
            'default_lon': DEFAULT_LONGITUDE,
            'default_lat': DEFAULT_LATITUDE,
            'default_zoom': DEFAULT_ZOOM,
        }
    }

    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'receipt', 'settlement', 'consumers', 'category')
        }),
        ('Lokalizacja', {
            'fields': ('location', 'latitude', 'longitude'),
            'description': 'Zaznacz punkt na mapie lub wpisz współrzędne poniżej.'
        }),
    )

    class Media:
        js = ('receipts/js/map_sync.js',)


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('name', 'members_count', 'total_expenses', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'join_code', 'created_at', 'updated_at')
    filter_horizontal = ('members',)

    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = 'Liczba członków'