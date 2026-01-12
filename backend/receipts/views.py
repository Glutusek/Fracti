import os
import uuid
from django.db import models
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from celery.result import AsyncResult
from .tasks import process_receipt_task

# Importujemy nasze modele i serializery
from .models import Receipt, Product, Settlement
from .serializers import ReceiptSerializer, ProductSerializer, SettlementSerializer
# Importujemy permissions (jeśli masz ten plik, jeśli nie - usuń tę linię)
# from .permissions import IsSettlementMember

class SettlementViewSet(viewsets.ModelViewSet):
    """
    Widok obsługujący Grupy Rozliczeniowe.
    Tylko zalogowani członkowie widzą swoje grupy.
    """
    serializer_class = SettlementSerializer
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Pokazujemy paragony, które:
        # 1. Są moje (jestem płatnikiem) LUB
        # 2. Są w grupie rozliczeniowej, do której należę
        user = self.request.user
        return Receipt.objects.filter(
            models.Q(purchaser=user) |
            models.Q(settlement__members=user)
        ).distinct().order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='my-products')
    def get_my_products(self, request):
        user = request.user
        user_products = Product.objects.filter(receipt__purchaser=user)
        serializer = ProductSerializer(user_products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Widok obsługujący pojedyncze produkty.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ReceiptAnalyzeView(APIView):
    """
    KROK 1: Wysyłka zdjęcia do analizy.
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
    KROK 2: Polling o wynik.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)

        if task_result.status == 'SUCCESS':
            return Response({
                "status": "SUCCESS",
                "data": task_result.result
            })
        elif task_result.status == 'FAILURE':
            return Response({
                "status": "FAILURE",
                "error": str(task_result.result)
            })

        return Response({"status": task_result.status})


class AddGuestUserView(APIView):
    # POPRAWKA: Usunąłem "permissions." przed IsAuthenticated
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        settlement = get_object_or_404(Settlement, pk=pk)

        # Security check
        if request.user not in settlement.members.all():
            return Response(
                {"error": "Nie masz uprawnień do tej grupy"},
                status=status.HTTP_403_FORBIDDEN
            )

        name = request.data.get('name')
        if not name:
            return Response({"error": "Nazwa jest wymagana"}, status=status.HTTP_400_BAD_REQUEST)

        unique_suffix = uuid.uuid4().hex[:8]
        dummy_username = f"guest_{unique_suffix}"

        try:
            # Tworzymy usera-cienia
            guest_user = User.objects.create_user(
                username=dummy_username,
                first_name=name,
                is_active=False
            )

            settlement.members.add(guest_user)

            return Response({
                "id": guest_user.id,
                "username": guest_user.first_name,
                "is_guest": True
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)