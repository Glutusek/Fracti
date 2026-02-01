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
from .models import Receipt, Product, Settlement, DebtSettlement
from .serializers import ReceiptSerializer, ProductSerializer, SettlementSerializer, DebtSettlementSerializer

class SettlementViewSet(viewsets.ModelViewSet):
    serializer_class = SettlementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Settlement.objects.filter(members=self.request.user)

    def perform_create(self, serializer):

        settlement = serializer.save(owner=self.request.user)

        settlement.members.add(self.request.user)

    @action(detail=False, methods=['post'], url_path='join')
    def join_group(self, request):
        code = request.data.get('join_code')

        if not code:
            return Response(
                {"error": "Kod dołączenia jest wymagany"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            settlement = Settlement.objects.get(join_code__iexact=code)
        except Settlement.DoesNotExist:
            return Response(
                {"error": "Nieprawidłowy kod grupy"},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.user in settlement.members.all():
            return Response(
                {"message": "Już jesteś członkiem tej grupy", "id": settlement.id},
                status=status.HTTP_200_OK
            )

        settlement.members.add(request.user)

        serializer = self.get_serializer(settlement)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        settlement = self.get_object()
        user_id_to_remove = request.data.get('user_id')

        is_owner = settlement.owner == request.user
        is_self_removal = str(request.user.id) == str(user_id_to_remove)

        if not (is_owner or is_self_removal):
            return Response({"error": "Tylko właściciel może usuwać innych."}, status=status.HTTP_403_FORBIDDEN)

        if settlement.owner.id == user_id_to_remove:
            return Response({"error": "Nie można usunąć właściciela grupy."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_to_remove = User.objects.get(id=user_id_to_remove)
            settlement.members.remove(user_to_remove)
            return Response({"status": "Użytkownik usunięty"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Użytkownik nie istnieje"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='settle-debt')
    def settle_debt(self, request, pk=None):
        settlement = self.get_object()
        from_user_id = request.data.get('from_user')
        to_user_id = request.data.get('to_user')
        amount = request.data.get('amount')

        if not all([from_user_id, to_user_id, amount]):
            return Response(
                {"error": "Wymagane pola: from_user, to_user, amount"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from_user = User.objects.get(id=from_user_id)
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Użytkownik nie istnieje"},
                status=status.HTTP_404_NOT_FOUND
            )

        debt_settlement = DebtSettlement.objects.create(
            settlement=settlement,
            from_user=from_user,
            to_user=to_user,
            amount=amount
        )

        serializer = DebtSettlementSerializer(debt_settlement)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='settle-debt/(?P<debt_id>[^/.]+)')
    def undo_settle_debt(self, request, pk=None, debt_id=None):
        settlement = self.get_object()
        
        try:
            debt_settlement = DebtSettlement.objects.get(id=debt_id, settlement=settlement)
            debt_settlement.delete()
            return Response({"status": "Rozliczenie cofnięte"}, status=status.HTTP_200_OK)
        except DebtSettlement.DoesNotExist:
            return Response(
                {"error": "Rozliczenie nie znalezione"},
                status=status.HTTP_404_NOT_FOUND
            )

class ReceiptViewSet(viewsets.ModelViewSet):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ReceiptAnalyzeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({"error": "Brak pliku obrazu"}, status=status.HTTP_400_BAD_REQUEST)

        file_name = f"temp_ocr/{file_obj.name}"
        path = default_storage.save(file_name, ContentFile(file_obj.read()))
        full_path = os.path.join(default_storage.location, path)

        task = process_receipt_task.delay(full_path)

        return Response({
            "task_id": task.id,
            "status": "PENDING"
        }, status=status.HTTP_202_ACCEPTED)


class OCRResultView(APIView):
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
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        settlement = get_object_or_404(Settlement, pk=pk)

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