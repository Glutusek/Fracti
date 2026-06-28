import os
import json
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
        
        if len(code) != 6:
            return Response(
                {"error": "Kod musi mieć dokładnie 6 znaków"},
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
        
        if not user_id_to_remove:
            return Response({"error": "user_id jest wymagane"}, status=status.HTTP_400_BAD_REQUEST)

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
            amount = float(amount)
            if amount <= 0 or amount > 1000000:
                return Response(
                    {"error": "Nieprawidłowa kwota (musi być > 0 i <= 1000000)"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Nieprawidłowy format kwoty"},
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
        
        if from_user not in settlement.members.all() or to_user not in settlement.members.all():
            return Response(
                {"error": "Użytkownicy muszą być członkami grupy"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if from_user == to_user:
            return Response(
                {"error": "Nie można rozliczyć długu z samą sobą"},
                status=status.HTTP_400_BAD_REQUEST
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
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Product.objects.filter(
            models.Q(purchaser=user) |
            models.Q(settlement__members=user) |
            models.Q(consumers=user) |
            models.Q(receipt__purchaser=user) |
            models.Q(receipt__settlement__members=user)
        ).distinct()


class ReceiptAnalyzeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({"error": "Brak pliku obrazu"}, status=status.HTTP_400_BAD_REQUEST)
        
        if file_obj.size > 10 * 1024 * 1024:
            return Response({"error": "Plik jest za duży (max 10MB)"}, status=status.HTTP_400_BAD_REQUEST)
        
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if file_obj.content_type not in allowed_types:
            return Response({"error": "Nieprawidłowy format pliku"}, status=status.HTTP_400_BAD_REQUEST)

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
        if not task_id or len(task_id) > 100:
            return Response(
                {"error": "Nieprawidłowy task_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        if len(name) < 2 or len(name) > 50:
            return Response({"error": "Nazwa musi mieć 2-50 znaków"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not name.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            return Response({"error": "Nazwa zawiera nieprawidłowe znaki"}, status=status.HTTP_400_BAD_REQUEST)

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


class ConvexHullView(APIView):
    """Zasięg terytorialny: poligon (convex hull) oplatający wszystkie
    lokalizacje paragonów i luźnych produktów w danym rozliczeniu."""
    permission_classes = [IsAuthenticated]

    def get(self, request, settlement_pk=None):
        from django.contrib.gis.geos import MultiPoint

        try:
            settlement = Settlement.objects.get(pk=settlement_pk, members=request.user)
        except Settlement.DoesNotExist:
            return Response(
                {"error": "Settlement not found or you don't have access"},
                status=status.HTTP_404_NOT_FOUND
            )

        points = []
        for loc in Receipt.objects.filter(
            settlement=settlement, location__isnull=False
        ).values_list('location', flat=True):
            if loc:
                points.append(loc)
        for loc in Product.objects.filter(
            settlement=settlement, receipt__isnull=True, location__isnull=False
        ).values_list('location', flat=True):
            if loc:
                points.append(loc)

        point_count = len(points)
        if point_count < 3:
            return Response({
                "settlement_id": str(settlement.id),
                "point_count": point_count,
                "geometry": None,
                "detail": "Za mało lokalizacji do wyznaczenia obszaru (min. 3).",
            }, status=status.HTTP_200_OK)

        multipoint = MultiPoint(points, srid=4326)
        hull = multipoint.convex_hull

        return Response({
            "settlement_id": str(settlement.id),
            "point_count": point_count,
            "geometry": json.loads(hull.geojson),
            "area_type": hull.geom_type,
        }, status=status.HTTP_200_OK)


class HeatmapViewSet(viewsets.ViewSet):
    """Heatmap visualization endpoint for settlement expense aggregation."""
    permission_classes = [IsAuthenticated]
    
    def list(self, request, settlement_pk=None):
        """Get heatmap data for a settlement."""
        try:
            # Get settlement and verify user has access
            settlement = Settlement.objects.get(pk=settlement_pk, members=request.user)
            print(f"[DEBUG] Heatmap request for settlement: {settlement.id} ({settlement.name})")
        except Settlement.DoesNotExist:
            return Response(
                {"error": "Settlement not found or you don't have access"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get query parameters
        bbox_str = request.query_params.get('bbox')
        if not bbox_str:
            return Response(
                {"error": "bbox parameter required (min_lon,min_lat,max_lon,max_lat)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bbox = tuple(map(float, bbox_str.split(',')))
            if len(bbox) != 4:
                raise ValueError
        except (ValueError, AttributeError):
            return Response(
                {"error": "Invalid bbox format. Expected: min_lon,min_lat,max_lon,max_lat"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional parameters
        grid_resolution = int(request.query_params.get('grid_resolution', 9))
        cell_size_str = request.query_params.get('cell_size')
        cell_size = float(cell_size_str) if cell_size_str else None
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        categories = request.query_params.get('categories')
        categories = categories.split(',') if categories else None
        
        user_ids_str = request.query_params.get('user_ids')
        user_ids = [int(uid) for uid in user_ids_str.split(',')] if user_ids_str else None
        
        show_empty_hexagons_str = request.query_params.get('show_empty_hexagons', 'true').lower()
        show_empty_hexagons = show_empty_hexagons_str in ('true', '1', 'yes')
        
        print(f"[DEBUG] Query params: bbox={bbox}, grid_resolution={grid_resolution}, cell_size={cell_size}, categories={categories}, user_ids={user_ids}, show_empty_hexagons={show_empty_hexagons}")
        
        # Get heatmap data
        from .heatmap_service import HeatmapAggregator
        
        aggregator = HeatmapAggregator(settlement)
        heatmap_data = aggregator.get_heatmap_data(
            bbox=bbox,
            grid_resolution=grid_resolution,
            date_from=date_from,
            date_to=date_to,
            categories=categories,
            user_ids=user_ids,
            cell_size=cell_size,
            show_empty_hexagons=show_empty_hexagons,
        )
        
        print(f"[DEBUG] Heatmap data returned: {len(heatmap_data)} points")
        
        return Response({
            "settlement_id": str(settlement.id),
            "bbox": bbox,
            "grid_resolution": grid_resolution,
            "heatmap_points": heatmap_data,
            "point_count": len(heatmap_data),
        }, status=status.HTTP_200_OK)