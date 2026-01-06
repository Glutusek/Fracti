from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from celery.result import AsyncResult
from .tasks import process_receipt_task # Upewnij się co do ścieżki importu
import os

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



class ReceiptAnalyzeView(APIView):
        """
        KROK 1: Wysyłka zdjęcia do analizy.
        Zwraca task_id, nie czekając na wynik.
        """
        permission_classes = [IsAuthenticated]

        def post(self, request):
            file_obj = request.FILES.get('image')
            if not file_obj:
                return Response({"error": "Brak pliku obrazu"}, status=status.HTTP_400_BAD_REQUEST)

            # Zapisz tymczasowo
            file_name = f"temp_ocr/{file_obj.name}"
            path = default_storage.save(file_name, ContentFile(file_obj.read()))
            full_path = os.path.join(default_storage.location, path)

            # Uruchom Celery Task
            task = process_receipt_task.delay(full_path)

            return Response({
                "task_id": task.id,
                "status": "PENDING"
            }, status=status.HTTP_202_ACCEPTED)

class OCRResultView(APIView):
        """
        KROK 2: Polling (odpytywanie) o wynik.
        Zwraca JSON z produktami i koordynatami, gdy gotowe.
        """
        permission_classes = [IsAuthenticated]

        def get(self, request, task_id):
            task_result = AsyncResult(task_id)

            if task_result.status == 'SUCCESS':
                return Response({
                    "status": "SUCCESS",
                    "data": task_result.result  # Tu będzie nasz JSON z ocr_engine
                })
            elif task_result.status == 'FAILURE':
                return Response({
                    "status": "FAILURE",
                    "error": str(task_result.result)
                })

            return Response({"status": task_result.status})