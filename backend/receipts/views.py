from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Importujemy nasze modele i serializery
from .models import Receipt, Product, Settlement
from .serializers import ReceiptSerializer, ProductSerializer, SettlementSerializer
# Importujemy naszego nowego ochroniarza
from .permissions import IsSettlementMember

class SettlementViewSet(viewsets.ModelViewSet):
    """
    Widok obsługujący Grupy Rozliczeniowe.
    Tylko zalogowani członkowie widzą swoje grupy.
    """
    serializer_class = SettlementSerializer
    # Wymagamy zalogowania (get_queryset() filtruje rozliczenia po członkostwie)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Settlement.objects.filter(members=self.request.user)

    def perform_create(self, serializer):
        # Przy tworzeniu grupy, automatycznie dodaj twórcę jako członka
        settlement = serializer.save()
        settlement.members.add(self.request.user)


class ReceiptViewSet(viewsets.ModelViewSet):
    """
    Widok obsługujący Paragony.
    """
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated] # Tylko zalogowani

    def get_queryset(self):
        # Pokazujemy paragony, które:
        # 1. Są moje (jestem płatnikiem) LUB
        # 2. Są w grupie rozliczeniowej, do której należę
        user = self.request.user
        return Receipt.objects.filter(
            models.Q(purchaser=user) |
            models.Q(settlement__members=user)
        ).distinct().order_by('-created_at')

    # Ta akcja pozwala pobrać produkty zalogowanego usera (Twoja prośba z wcześniej)
    @action(detail=False, methods=['get'], url_path='my-products')
    def get_my_products(self, request):
        user = request.user
        user_products = Product.objects.filter(receipt__purchaser=user)
        serializer = ProductSerializer(user_products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Widok obsługujący pojedyncze produkty (pozycje na paragonie).
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]