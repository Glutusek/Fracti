from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django import forms
from django.contrib.gis.geos import Point
from .models import Receipt, Product, Settlement


class MapItemAdminForm(forms.ModelForm):
    """
    Formularz obsługujący logikę wyświetlania i zapisywania współrzędnych.
    """
    latitude = forms.FloatField(
        required=False,
        label="Szerokość (Lat)",
        help_text="Np. 52.2297 (Warszawa)"
    )
    longitude = forms.FloatField(
        required=False,
        label="Długość (Lon)",
        help_text="Np. 21.0122 (Warszawa)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # SCENARIUSZ 1: EDYCJA (Pobierz dane z bazy, jeśli istnieją)
        if self.instance and self.instance.pk and self.instance.location:
            self.fields['longitude'].initial = self.instance.location.x
            self.fields['latitude'].initial = self.instance.location.y

        # SCENARIUSZ 2: NOWY OBIEKT (Ustaw wartości domyślne)
        elif not self.instance.pk:
            # Tutaj wpisujemy "Startowe" koordynaty dla pól tekstowych
            self.fields['latitude'].initial = 52.2297  # Warszawa
            self.fields['longitude'].initial = 21.0122  # Warszawa

    def save(self, commit=True):
        instance = super().save(commit=False)
        lat = self.cleaned_data.get('latitude')
        lon = self.cleaned_data.get('longitude')

        if lat is not None and lon is not None:
            instance.location = Point(lon, lat)

        if commit:
            instance.save()
        return instance

# --- KONFIGURACJA DLA PARAGONU ---
class ReceiptForm(MapItemAdminForm):
    class Meta:
        model = Receipt
        fields = '__all__'


@admin.register(Receipt)
class ReceiptAdmin(GISModelAdmin):
    form = ReceiptForm  # Podpinamy formularz z Lat/Lon
    list_display = ('merchant_name', 'purchase_date', 'total_amount', 'id')
    default_lon = 21.0122  # Warszawa (domyślny widok mapy)
    default_lat = 52.2297
    default_zoom = 6


# --- KONFIGURACJA DLA PRODUKTU ---
class ProductForm(MapItemAdminForm):
    class Meta:
        model = Product
        fields = '__all__'


@admin.register(Product)
class ProductAdmin(GISModelAdmin):
    form = ProductForm  # <--- TERAZ PRODUKT TEŻ MA FORMULARZ!
    list_display = ('name', 'price', 'receipt', 'id')
    list_filter = ('receipt',)
    default_lon = 21.0122
    default_lat = 52.2297
    default_zoom = 6


# --- KONFIGURACJA DLA ROZLICZENIA ---
@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('name', 'members_count', 'total_expenses', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'join_code', 'created_at', 'updated_at')
    filter_horizontal = ('members',)

    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = 'Liczba członków'