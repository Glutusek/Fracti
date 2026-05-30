import uuid
from decimal import Decimal
from django.db import transaction
from django.contrib.gis.geos import Point, LineString
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from receipts.models import Settlement, Receipt, Product
from .models import Trip, TripStop, TripParticipant, TripLeg, TripOtherCost, TripDebt
from .serializers import (
    TripSerializer, TripListSerializer, TripBulkWriteSerializer,
    TripDebtSerializer,
)
from .permissions import IsTripOwnerOrSettlementMember
from .services import (
    compute_trip_split, preview_trip_split,
    compute_simple_mode, rebalance_leg_consumptions,
    InconsistentConsumptionError,
)

User = get_user_model()


def _serialize_debts(trip, debts):
    pmap = {str(p.id): p for p in trip.participants.all()}
    out = []
    for d in debts:
        debtor = pmap.get(str(d.debtor_id))
        creditor = pmap.get(str(d.creditor_id))
        out.append({
            'debtor': str(d.debtor_id),
            'creditor': str(d.creditor_id),
            'debtor_name': debtor.display_name if debtor else str(d.debtor_id),
            'creditor_name': creditor.display_name if creditor else str(d.creditor_id),
            'debtor_color': (debtor.color if debtor else '') or '',
            'creditor_color': (creditor.color if creditor else '') or '',
            'amount': str(d.amount),
            'breakdown': d.breakdown,
        })
    return out


class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTripOwnerOrSettlementMember]

    def get_queryset(self):
        user = self.request.user
        settlement_id = self.request.query_params.get('settlement')
        qs = Trip.objects.filter(owner=user)
        if settlement_id:
            from receipts.models import Settlement as S
            try:
                settlement = S.objects.get(pk=settlement_id)
                if user in settlement.members.all():
                    qs = Trip.objects.filter(settlement=settlement)
            except S.DoesNotExist:
                pass
        return qs.select_related('owner', 'settlement', 'payer')

    def get_serializer_class(self):
        if self.action == 'list':
            return TripListSerializer
        return TripSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.payer = None
        instance.save(update_fields=['payer'])
        instance.delete()

    def update(self, request, *args, **kwargs):
        """Bulk PUT — atomic nuke-and-recreate of nested children."""
        partial = kwargs.pop('partial', False)
        trip = self.get_object()
        bulk = TripBulkWriteSerializer(data=request.data, partial=partial)
        if not bulk.is_valid():
            return Response(bulk.errors, status=status.HTTP_400_BAD_REQUEST)
        data = bulk.validated_data

        try:
            with transaction.atomic():
                trip.name = data['name']
                trip.description = data.get('description', '')
                trip.trip_date = data.get('trip_date')
                trip.global_consumption_l_per_100km = data['global_consumption_l_per_100km']
                trip.fuel_price_per_liter = data['fuel_price_per_liter']
                trip.currency = data.get('currency', 'PLN')
                trip.total_tolls = data.get('total_tolls', Decimal('0'))

                if 'settlement' in data and data.get('settlement') is not None:
                    trip.settlement = get_object_or_404(Settlement, pk=data['settlement'])
                elif 'settlement' in data:
                    trip.settlement = None

                trip.payer = None
                trip.save()

                trip.legs.all().delete()
                trip.other_costs.all().delete()
                trip.stops.all().delete()
                trip.participants.all().delete()

                stops_data = data.get('stops', [])
                stops_map = {}
                for s in stops_data:
                    stop = TripStop.objects.create(
                        trip=trip,
                        order=s['order'],
                        name=s.get('name', ''),
                        location=Point(float(s['longitude']), float(s['latitude'])),
                        arrived_at=s.get('arrived_at'),
                    )
                    stops_map[s['order']] = stop

                participants_data = data.get('participants', [])
                participants_list = []
                for p in participants_data:
                    user_id = p.get('user')
                    guest_label = p.get('guest_label', '')
                    if user_id:
                        try:
                            u = User.objects.get(pk=user_id)
                        except User.DoesNotExist:
                            return Response({'error': f'User {user_id} not found'}, status=400)
                        participant = TripParticipant.objects.create(
                            trip=trip, user=u,
                            color=p.get('color', ''),
                        )
                    else:
                        if not guest_label:
                            return Response({'error': 'participant needs user or guest_label'}, status=400)
                        participant = TripParticipant.objects.create(
                            trip=trip, guest_label=guest_label,
                            color=p.get('color', ''),
                        )
                    participants_list.append(participant)

                payer_index = data.get('payer_index')
                if payer_index is not None and 0 <= payer_index < len(participants_list):
                    trip.payer = participants_list[payer_index]
                    trip.save(update_fields=['payer'])

                legs_data = data.get('legs', [])
                legs_map = {}
                for lg in legs_data:
                    from_stop = stops_map.get(lg.get('from_stop_index', lg.get('from_stop')))
                    to_stop = stops_map.get(lg.get('to_stop_index', lg.get('to_stop')))
                    if from_stop is None or to_stop is None:
                        return Response({'error': 'invalid stop index in leg'}, status=400)
                    leg = TripLeg.objects.create(
                        trip=trip,
                        order=lg['order'],
                        from_stop=from_stop,
                        to_stop=to_stop,
                        distance_km=lg['distance_km'],
                        duration_seconds=lg.get('duration_seconds', 0),
                        consumption_l_per_100km=lg.get(
                            'consumption_l_per_100km',
                            trip.global_consumption_l_per_100km,
                        ),
                        consumption_override=lg.get('consumption_override', False),
                    )
                    participant_indices = lg.get('participant_indices', [])
                    for idx in participant_indices:
                        if 0 <= idx < len(participants_list):
                            leg.participants.add(participants_list[idx])
                    legs_map[lg['order']] = leg

                for oc in data.get('other_costs', []):
                    leg_ref = None
                    if oc.get('leg_order') is not None:
                        leg_ref = legs_map.get(oc['leg_order'])
                    TripOtherCost.objects.create(
                        trip=trip,
                        label=oc['label'],
                        amount=oc['amount'],
                        split_scope=oc.get('split_scope', 'ALL'),
                        leg=leg_ref,
                    )

                try:
                    rebalance_leg_consumptions(trip)
                except InconsistentConsumptionError as e:
                    raise e

        except InconsistentConsumptionError as e:
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)

        return Response(TripSerializer(trip).data)

    @action(detail=True, methods=['post'])
    def compute(self, request, pk=None):
        trip = self.get_object()
        if not trip.payer:
            return Response({'error': 'payer_required'}, status=400)
        try:
            result = compute_trip_split(trip)
        except InconsistentConsumptionError as e:
            return Response(e.to_dict(), status=400)
        return Response({
            'total_distance_km': str(result.total_distance_km),
            'total_fuel_cost': str(result.total_fuel_cost),
            'total_other_cost': str(result.total_other_cost),
            'total_cost': str(result.total_cost),
            'debts': _serialize_debts(trip, result.debts),
        })

    @action(detail=True, methods=['post'], url_path='preview-compute')
    def preview_compute(self, request, pk=None):
        trip = self.get_object()
        try:
            result = preview_trip_split(trip)
        except InconsistentConsumptionError as e:
            return Response(e.to_dict(), status=400)
        return Response({
            'total_distance_km': str(result.total_distance_km),
            'total_fuel_cost': str(result.total_fuel_cost),
            'total_other_cost': str(result.total_other_cost),
            'total_cost': str(result.total_cost),
            'debts': _serialize_debts(trip, result.debts),
        })

    @action(detail=True, methods=['post'], url_path='transfer-to-settlement')
    def transfer_to_settlement(self, request, pk=None):
        trip = self.get_object()
        if not trip.settlement:
            return Response({'error': 'trip has no settlement'}, status=400)
        if not trip.payer:
            return Response({'error': 'payer_required'}, status=400)
        if not trip.debts.exists():
            try:
                compute_trip_split(trip)
            except InconsistentConsumptionError as e:
                return Response(e.to_dict(), status=400)

        with transaction.atomic():
            for debt in trip.debts.filter(debtor__user__isnull=True):
                p = debt.debtor
                if not p.guest_label:
                    continue
                unique_suffix = uuid.uuid4().hex[:8]
                guest_user = User.objects.create_user(
                    username=f"guest_{unique_suffix}",
                    first_name=p.guest_label,
                    is_active=False,
                )
                trip.settlement.members.add(guest_user)
                p.user = guest_user
                p.save(update_fields=['user'])

            payer_user = trip.payer.user if trip.payer else None
            if trip.linked_receipt:
                receipt = trip.linked_receipt
                receipt.merchant_name = f"Podróż: {trip.name}"
                receipt.total_amount = trip.total_cost
                receipt.purchase_date = trip.trip_date
                receipt.save()
                receipt.products.all().delete()
            else:
                from receipts.models import CategoryChoices
                receipt = Receipt.objects.create(
                    settlement=trip.settlement,
                    purchaser=payer_user,
                    merchant_name=f"Podróż: {trip.name}",
                    total_amount=trip.total_cost or Decimal('0'),
                    purchase_date=trip.trip_date,
                    category=CategoryChoices.TRANSPORT,
                )
                trip.linked_receipt = receipt
                trip.save(update_fields=['linked_receipt'])

            for debt in trip.debts.all():
                p = debt.debtor
                if not p.user:
                    continue
                from receipts.models import CategoryChoices
                product = Product.objects.create(
                    receipt=receipt,
                    name=f"Udział: {p.display_name}",
                    price=debt.amount,
                    purchaser=payer_user,
                    category=CategoryChoices.TRANSPORT,
                )
                product.consumers.set([p.user])

        return Response({'receipt': str(receipt.id)}, status=200)


class SimpleCalculatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mode = request.data.get('mode')
        if not mode:
            return Response({'error': 'mode required'}, status=400)
        try:
            result = compute_simple_mode(mode, request.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        out = {'mode': result.mode}
        for field in ['total_cost', 'per_person', 'fuel_liters', 'distance_km',
                      'distance_miles', 'consumption_l_per_100km']:
            v = getattr(result, field, None)
            if v is not None:
                out[field] = str(v)
        return Response(out)
