from django.contrib import admin
from .models import Trip, TripStop, TripParticipant, TripLeg, TripOtherCost, TripDebt


class TripStopInline(admin.TabularInline):
    model = TripStop
    extra = 0


class TripParticipantInline(admin.TabularInline):
    model = TripParticipant
    extra = 0


class TripLegInline(admin.TabularInline):
    model = TripLeg
    extra = 0


class TripOtherCostInline(admin.TabularInline):
    model = TripOtherCost
    extra = 0


class TripDebtInline(admin.TabularInline):
    model = TripDebt
    extra = 0
    readonly_fields = ['computed_at']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'settlement', 'trip_date', 'total_cost', 'created_at']
    list_filter = ['settlement', 'trip_date']
    search_fields = ['name', 'owner__username']
    inlines = [TripStopInline, TripParticipantInline, TripLegInline, TripOtherCostInline, TripDebtInline]
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_distance_km', 'total_fuel_cost', 'total_other_cost', 'total_cost']


@admin.register(TripDebt)
class TripDebtAdmin(admin.ModelAdmin):
    list_display = ['trip', 'debtor', 'creditor', 'amount', 'computed_at']
    readonly_fields = ['computed_at']
