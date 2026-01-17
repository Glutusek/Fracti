from rest_framework import serializers
from django.contrib.gis.geos import Point
import uuid
from .models import Receipt, Product, Settlement, DebtSettlement
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username','first_name']

class ProductSerializer(serializers.ModelSerializer):

    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    consumers = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    purchaser = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    settlement = serializers.PrimaryKeyRelatedField(queryset=Settlement.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity','receipt', 'settlement', 'consumers', 'purchaser', 'latitude', 'longitude', 'created_at', 'category']

    def get_latitude(self, obj):
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        return obj.location.x if obj.location else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['latitude'] = instance.location.y if instance.location else None
        data['longitude'] = instance.location.x if instance.location else None
        return data

    def create(self, validated_data):
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)
        consumers = validated_data.pop('consumers', [])

        instance = super().create(validated_data)

        if lat is not None and lon is not None:
            instance.location = Point(lon, lat)
            instance.save()

        if consumers:
            instance.consumers.set(consumers)

        return instance

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)
        consumers = validated_data.pop('consumers', None)

        if lat is not None and lon is not None:
            instance.location = Point(lon, lat)
        elif lat is None and lon is None and 'latitude' in self.initial_data and 'longitude' in self.initial_data:
            # Jeśli przesłano jawnie null, wyczyść lokalizację
            instance.location = None

        instance = super().update(instance, validated_data)

        # Aktualizujemy konsumentów jeśli zostali przekazani
        if consumers is not None:
            instance.consumers.set(consumers)

        return instance

class ReceiptSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = Receipt
        fields = ['id', 'merchant_name', 'description', 'total_amount', 'purchase_date', 'image', 'latitude', 'longitude', 'products',
                  'created_at', 'settlement', 'purchaser', 'category']

    def get_latitude(self, obj):
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        return obj.location.x if obj.location else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['latitude'] = instance.location.y if instance.location else None
        data['longitude'] = instance.location.x if instance.location else None
        return data

    def create(self, validated_data):
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)

        # Tworzymy instancję paragonu
        instance = super().create(validated_data)

        # Ustawiamy lokalizację jeśli podano współrzędne
        if lat is not None and lon is not None:
            instance.location = Point(lon, lat)
            instance.save()

        return instance

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)
        if lat is not None and lon is not None:
            instance.location = Point(lon, lat)
        elif lat is None and lon is None and 'latitude' in self.initial_data and 'longitude' in self.initial_data:
            instance.location = None

        return super().update(instance, validated_data)

class SettlementSerializer(serializers.ModelSerializer):
    receipts = ReceiptSerializer(many=True, read_only=True)
    owner_id = serializers.ReadOnlyField(source='owner.id')
    loose_products = serializers.SerializerMethodField()
    members = UserSerializer(many=True, read_only=True)
    debt_settlements = serializers.SerializerMethodField()
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Settlement
        fields = ['id', 'name', 'description', 'join_code', 'members','receipts', 'loose_products', 'debt_settlements', 'total_expenses', 'created_at', 'owner_id']

    def create(self, validated_data):
        # join_code jest automatycznie generowane przez model (uuid.uuid4)
        # nie musimy go tutaj nadpisywać
        return super().create(validated_data)

    def get_loose_products(self, obj):
        products = obj.products.filter(receipt__isnull=True)
        return ProductSerializer(products, many=True).data

    def get_debt_settlements(self, obj):
        debt_settlements = obj.debt_settlements.all()
        return DebtSettlementSerializer(debt_settlements, many=True).data


class DebtSettlementSerializer(serializers.ModelSerializer):
    from_user_name = serializers.SerializerMethodField()
    to_user_name = serializers.SerializerMethodField()

    class Meta:
        model = DebtSettlement
        fields = ['id', 'settlement', 'from_user', 'to_user', 'from_user_name', 'to_user_name', 'amount', 'settled_at']
        read_only_fields = ['id', 'settled_at']

    def get_from_user_name(self, obj):
        return obj.from_user.first_name or obj.from_user.username

    def get_to_user_name(self, obj):
        return obj.to_user.first_name or obj.to_user.username