from rest_framework import serializers
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
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    consumers = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'receipt', 'settlement', 'consumers', 'latitude', 'longitude', 'created_at']

    def get_latitude(self, obj):
        # Wyciągamy Y (Szerokość) z obiektu Point, jeśli istnieje
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        # Wyciągamy X (Długość) z obiektu Point, jeśli istnieje
        return obj.location.x if obj.location else None

#RECEIPT
class ReceiptSerializer(serializers.ModelSerializer):
    # Zagnieżdżamy produkty, żeby jednym zapytaniem pobrać paragon I JEGO pozycje
    products = ProductSerializer(many=True, read_only=True)

    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = ['id', 'merchant_name', 'total_amount', 'purchase_date', 'image', 'latitude', 'longitude', 'products',
                  'created_at', 'settlement', 'purchaser']

    def get_latitude(self, obj):
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        return obj.location.x if obj.location else None

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

    def get_loose_products(self, obj):
        products = obj.products.filter(receipt__isnull=True)
        return ProductSerializer(products, many=True).data