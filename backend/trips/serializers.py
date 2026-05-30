from rest_framework import serializers
from django.contrib.gis.geos import Point, LineString
from django.contrib.auth import get_user_model
from .models import Trip, TripStop, TripParticipant, TripLeg, TripOtherCost, TripDebt

User = get_user_model()


class TripParticipantSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = TripParticipant
        fields = ['id', 'user', 'guest_label', 'color', 'display_name']

    def get_display_name(self, obj):
        return obj.display_name


class TripStopSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = TripStop
        fields = ['id', 'order', 'name', 'latitude', 'longitude', 'arrived_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['latitude'] = instance.location.y if instance.location else None
        data['longitude'] = instance.location.x if instance.location else None
        return data


class TripLegSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    participants = TripParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = TripLeg
        fields = [
            'id', 'order', 'from_stop', 'to_stop',
            'distance_km', 'duration_seconds',
            'consumption_l_per_100km', 'consumption_override',
            'participant_ids', 'participants',
        ]


class TripOtherCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripOtherCost
        fields = ['id', 'label', 'amount', 'paid_by', 'split_scope', 'leg']


class TripDebtSerializer(serializers.ModelSerializer):
    debtor_name = serializers.SerializerMethodField()
    creditor_name = serializers.SerializerMethodField()

    class Meta:
        model = TripDebt
        fields = ['id', 'debtor', 'creditor', 'debtor_name', 'creditor_name', 'amount', 'breakdown', 'computed_at']

    def get_debtor_name(self, obj):
        return obj.debtor.display_name

    def get_creditor_name(self, obj):
        return obj.creditor.display_name


class TripListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            'id', 'name', 'trip_date', 'settlement', 'total_cost',
            'total_distance_km', 'currency', 'created_at',
        ]


class TripSerializer(serializers.ModelSerializer):
    stops = TripStopSerializer(many=True, read_only=True)
    participants = TripParticipantSerializer(many=True, read_only=True)
    legs = TripLegSerializer(many=True, read_only=True)
    other_costs = TripOtherCostSerializer(many=True, read_only=True)
    debts = TripDebtSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'name', 'description', 'settlement', 'trip_date',
            'global_consumption_l_per_100km', 'fuel_price_per_liter',
            'currency', 'total_tolls', 'payer',
            'total_distance_km', 'total_fuel_cost', 'total_other_cost', 'total_cost',
            'stops', 'participants', 'legs', 'other_costs', 'debts',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TripBulkWriteSerializer(serializers.Serializer):
    """Bulk PUT payload for atomic trip save."""

    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, default='')
    settlement = serializers.UUIDField(allow_null=True, required=False)
    trip_date = serializers.DateTimeField(allow_null=True, required=False)
    global_consumption_l_per_100km = serializers.DecimalField(max_digits=6, decimal_places=3)
    fuel_price_per_liter = serializers.DecimalField(max_digits=8, decimal_places=4)
    currency = serializers.CharField(max_length=3, default='PLN')
    total_tolls = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    payer_index = serializers.IntegerField(allow_null=True, required=False)

    stops = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    participants = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    legs = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    other_costs = serializers.ListField(child=serializers.DictField(), required=False, default=list)
