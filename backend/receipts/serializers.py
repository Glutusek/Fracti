from rest_framework import serializers
from django.contrib.gis.geos import Point
import uuid
from .models import Receipt, Product, Settlement
from django.contrib.auth import get_user_model
User = get_user_model()
#USER
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username'] # Możesz dodać avatar jeśli masz

#PRODUCT
class ProductSerializer(serializers.ModelSerializer):
    # Pola wirtualne (obliczane w locie), żeby Frontend miał łatwiej
    # Umożliwiamy odczyt i zapis współrzędnych (mapa)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    consumers = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'receipt', 'settlement', 'consumers', 'latitude', 'longitude', 'created_at', 'category']

    def get_latitude(self, obj):
        # Wyciągamy Y (Szerokość) z obiektu Point, jeśli istnieje
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        # Wyciągamy X (Długość) z obiektu Point, jeśli istnieje
        return obj.location.x if obj.location else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Nadpisujemy pola latitude/longitude z obiektu Point
        data['latitude'] = instance.location.y if instance.location else None
        data['longitude'] = instance.location.x if instance.location else None
        return data

    def create(self, validated_data):
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)

        # Tworzymy instancję produktu
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
            # Jeśli przesłano jawnie null, wyczyść lokalizację
            instance.location = None

        return super().update(instance, validated_data)

#RECEIPT
class ReceiptSerializer(serializers.ModelSerializer):
    # Zagnieżdżamy produkty, żeby jednym zapytaniem pobrać paragon I JEGO pozycje
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

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)
        if lat is not None and lon is not None:
            instance.location = Point(lon, lat)
        elif lat is None and lon is None and 'latitude' in self.initial_data and 'longitude' in self.initial_data:
            instance.location = None

        return super().update(instance, validated_data)

#SETTELMENTS
class SettlementSerializer(serializers.ModelSerializer):
    # Pokażemy od razu listę paragonów wewnątrz grupy
    receipts = ReceiptSerializer(many=True, read_only=True)

    loose_products = serializers.SerializerMethodField()
    members = UserSerializer(many=True, read_only=True)
    # Dodatkowe pole obliczane w locie (Logika biznesowa)
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Settlement
        fields = ['id', 'name', 'description', 'join_code', 'members','receipts', 'loose_products', 'total_expenses', 'created_at']

    def create(self, validated_data):
        # join_code jest automatycznie generowane przez model (uuid.uuid4)
        # nie musimy go tutaj nadpisywać
        return super().create(validated_data)

    def get_loose_products(self, obj):
        products = obj.products.filter(receipt__isnull=True)
        return ProductSerializer(products, many=True).data