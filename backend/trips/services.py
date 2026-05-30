from decimal import Decimal, ROUND_HALF_UP, getcontext
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Optional

getcontext().prec = 28

Q2 = Decimal('0.01')
Q3 = Decimal('0.001')


class InconsistentConsumptionError(Exception):
    def __init__(self, target_liters, committed_liters, max_for_overrides=None):
        self.target_liters = target_liters
        self.committed_liters = committed_liters
        self.max_for_overrides = max_for_overrides
        super().__init__(
            f"Overrides consume {committed_liters}L but global allows only {target_liters}L"
        )

    def to_dict(self):
        return {
            'error': 'inconsistent_consumption',
            'target_liters': str(self.target_liters),
            'committed_liters': str(self.committed_liters),
            'max_for_overrides': str(self.max_for_overrides) if self.max_for_overrides else None,
        }


@dataclass
class DebtResult:
    debtor_id: str
    creditor_id: str
    amount: Decimal
    breakdown: dict


@dataclass
class ComputeResult:
    total_distance_km: Decimal
    total_fuel_cost: Decimal
    total_other_cost: Decimal
    total_cost: Decimal
    debts: List[DebtResult]


@dataclass
class SimpleResult:
    mode: str
    total_cost: Optional[Decimal] = None
    per_person: Optional[Decimal] = None
    fuel_liters: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    distance_miles: Optional[Decimal] = None
    consumption_l_per_100km: Optional[Decimal] = None


def rebalance_leg_consumptions(trip):
    legs = list(trip.legs.order_by('order'))
    if not legs:
        return

    G = Decimal(str(trip.global_consumption_l_per_100km))
    D = sum(Decimal(str(l.distance_km)) for l in legs)
    if D == 0:
        return

    target = G * D

    overridden = [l for l in legs if l.consumption_override]
    free = [l for l in legs if not l.consumption_override]

    fixed_sum = sum(
        Decimal(str(l.distance_km)) * Decimal(str(l.consumption_l_per_100km))
        for l in overridden
    )

    if not free:
        new_global = (fixed_sum / D).quantize(Q3, rounding=ROUND_HALF_UP)
        trip.global_consumption_l_per_100km = new_global
        trip.save(update_fields=['global_consumption_l_per_100km'])
        return

    remaining = target - fixed_sum
    if remaining < 0:
        raise InconsistentConsumptionError(target, fixed_sum, target)

    free_dist = sum(Decimal(str(l.distance_km)) for l in free)
    if free_dist == 0:
        if abs(remaining) > Decimal('0.0001'):
            raise InconsistentConsumptionError(target, fixed_sum)
        return

    new_consumption = (remaining / free_dist).quantize(Q3, rounding=ROUND_HALF_UP)
    if new_consumption < 0:
        raise InconsistentConsumptionError(target, fixed_sum)

    for l in free:
        l.consumption_l_per_100km = new_consumption
        l.save(update_fields=['consumption_l_per_100km'])


def compute_trip_split(trip) -> ComputeResult:
    rebalance_leg_consumptions(trip)

    fuel_price = Decimal(str(trip.fuel_price_per_liter))
    total_tolls = Decimal(str(trip.total_tolls))

    fuel_per_p: dict = defaultdict(Decimal)
    tolls_per_p: dict = defaultdict(Decimal)
    other_per_p: dict = defaultdict(Decimal)
    total_distance = Decimal(0)
    total_fuel_cost = Decimal(0)

    legs = list(trip.legs.order_by('order').prefetch_related('participants'))
    D = sum(Decimal(str(l.distance_km)) for l in legs)

    for leg in legs:
        present = list(leg.participants.all())
        if not present:
            continue
        dist = Decimal(str(leg.distance_km))
        cons = Decimal(str(leg.consumption_l_per_100km))
        liters = dist * cons / Decimal(100)
        leg_fuel_cost = liters * fuel_price
        leg_toll_cost = (total_tolls * dist / D) if D > 0 else Decimal(0)
        n = len(present)
        share_fuel = leg_fuel_cost / n
        share_toll = leg_toll_cost / n
        for p in present:
            fuel_per_p[str(p.id)] += share_fuel
            tolls_per_p[str(p.id)] += share_toll
        total_distance += dist
        total_fuel_cost += leg_fuel_cost

    total_other = Decimal(0)
    for oc in trip.other_costs.all():
        amount = Decimal(str(oc.amount))
        total_other += amount
        if oc.split_scope == 'ALL':
            pool = list(trip.participants.all())
        else:
            pool = list(oc.leg.participants.all()) if oc.leg else []
        if not pool:
            continue
        share = amount / len(pool)
        for p in pool:
            other_per_p[str(p.id)] += share

    payer_id = str(trip.payer_id) if trip.payer_id else None
    debts = []
    for p in trip.participants.all():
        pid = str(p.id)
        if pid == payer_id:
            continue
        f = fuel_per_p[pid].quantize(Q2, rounding=ROUND_HALF_UP)
        t = tolls_per_p[pid].quantize(Q2, rounding=ROUND_HALF_UP)
        o = other_per_p[pid].quantize(Q2, rounding=ROUND_HALF_UP)
        owed = f + t + o
        if owed > 0:
            debts.append(DebtResult(
                debtor_id=pid,
                creditor_id=payer_id,
                amount=owed,
                breakdown={'fuel': str(f), 'tolls': str(t), 'other': str(o)},
            ))

    trip.total_distance_km = total_distance.quantize(Q3)
    trip.total_fuel_cost = total_fuel_cost.quantize(Q2, rounding=ROUND_HALF_UP)
    trip.total_other_cost = total_other.quantize(Q2, rounding=ROUND_HALF_UP)
    trip.total_cost = (total_fuel_cost + total_tolls + total_other).quantize(Q2, rounding=ROUND_HALF_UP)
    trip.save(update_fields=['total_distance_km', 'total_fuel_cost', 'total_other_cost', 'total_cost'])

    _upsert_debts(trip, debts)

    return ComputeResult(
        total_distance_km=trip.total_distance_km,
        total_fuel_cost=trip.total_fuel_cost,
        total_other_cost=trip.total_other_cost,
        total_cost=trip.total_cost,
        debts=debts,
    )


def _upsert_debts(trip, debts: List[DebtResult]):
    from trips.models import TripDebt, TripParticipant
    trip.debts.all().delete()
    for d in debts:
        TripDebt.objects.create(
            trip=trip,
            debtor_id=d.debtor_id,
            creditor_id=d.creditor_id,
            amount=d.amount,
            breakdown=d.breakdown,
        )


def preview_trip_split(trip) -> ComputeResult:
    """Compute without persisting TripDebt rows."""
    from decimal import Decimal, ROUND_HALF_UP
    from collections import defaultdict

    legs = list(trip.legs.order_by('order').prefetch_related('participants'))
    D = sum(Decimal(str(l.distance_km)) for l in legs)
    G = Decimal(str(trip.global_consumption_l_per_100km))
    fuel_price = Decimal(str(trip.fuel_price_per_liter))
    total_tolls = Decimal(str(trip.total_tolls))

    fuel_per_p: dict = defaultdict(Decimal)
    tolls_per_p: dict = defaultdict(Decimal)
    other_per_p: dict = defaultdict(Decimal)
    total_distance = Decimal(0)
    total_fuel_cost = Decimal(0)

    for leg in legs:
        present = list(leg.participants.all())
        if not present:
            continue
        dist = Decimal(str(leg.distance_km))
        cons = Decimal(str(leg.consumption_l_per_100km))
        liters = dist * cons / Decimal(100)
        leg_fuel_cost = liters * fuel_price
        leg_toll_cost = (total_tolls * dist / D) if D > 0 else Decimal(0)
        n = len(present)
        share_fuel = leg_fuel_cost / n
        share_toll = leg_toll_cost / n
        for p in present:
            fuel_per_p[str(p.id)] += share_fuel
            tolls_per_p[str(p.id)] += share_toll
        total_distance += dist
        total_fuel_cost += leg_fuel_cost

    total_other = Decimal(0)
    for oc in trip.other_costs.all():
        amount = Decimal(str(oc.amount))
        total_other += amount
        pool = list(trip.participants.all()) if oc.split_scope == 'ALL' \
               else (list(oc.leg.participants.all()) if oc.leg else [])
        if not pool:
            continue
        share = amount / len(pool)
        for p in pool:
            other_per_p[str(p.id)] += share

    payer_id = str(trip.payer_id) if trip.payer_id else None
    debts = []
    for p in trip.participants.all():
        pid = str(p.id)
        if pid == payer_id:
            continue
        f = fuel_per_p[pid].quantize(Q2, rounding=ROUND_HALF_UP)
        t = tolls_per_p[pid].quantize(Q2, rounding=ROUND_HALF_UP)
        o = other_per_p[pid].quantize(Q2, rounding=ROUND_HALF_UP)
        owed = f + t + o
        if owed > 0:
            debts.append(DebtResult(
                debtor_id=pid,
                creditor_id=payer_id,
                amount=owed,
                breakdown={'fuel': str(f), 'tolls': str(t), 'other': str(o)},
            ))

    return ComputeResult(
        total_distance_km=total_distance.quantize(Q3),
        total_fuel_cost=total_fuel_cost.quantize(Q2, rounding=ROUND_HALF_UP),
        total_other_cost=total_other.quantize(Q2, rounding=ROUND_HALF_UP),
        total_cost=(total_fuel_cost + total_tolls + total_other).quantize(Q2, rounding=ROUND_HALF_UP),
        debts=debts,
    )


def compute_simple_mode(mode: str, payload: dict) -> SimpleResult:
    def d(key, default='0'):
        return Decimal(str(payload.get(key, default)))

    if mode == 'TRIP_COST':
        distance = d('distance_km')
        consumption = d('consumption')
        price = d('price_per_liter')
        n = max(1, int(payload.get('n', 1)))
        liters = consumption / 100 * distance
        cost = liters * price
        return SimpleResult(
            mode=mode,
            total_cost=cost.quantize(Q2, rounding=ROUND_HALF_UP),
            per_person=(cost / n).quantize(Q2, rounding=ROUND_HALF_UP),
            fuel_liters=liters.quantize(Q2, rounding=ROUND_HALF_UP),
        )

    elif mode == 'DISTANCE':
        liters = d('liters')
        consumption = d('consumption')
        price = d('price_per_liter')
        if consumption == 0:
            raise ValueError('consumption cannot be zero')
        distance = liters / (consumption / 100)
        cost = liters * price
        return SimpleResult(
            mode=mode,
            distance_km=distance.quantize(Q2, rounding=ROUND_HALF_UP),
            distance_miles=(distance * Decimal('0.621371')).quantize(Q2, rounding=ROUND_HALF_UP),
            total_cost=cost.quantize(Q2, rounding=ROUND_HALF_UP),
            fuel_liters=liters.quantize(Q2, rounding=ROUND_HALF_UP),
        )

    elif mode == 'CONSUMPTION_RATE':
        distance = d('distance_km')
        liters = d('liters')
        price = d('price_per_liter')
        if distance == 0:
            raise ValueError('distance_km cannot be zero')
        cons = liters / distance * 100
        cost = liters * price
        return SimpleResult(
            mode=mode,
            consumption_l_per_100km=cons.quantize(Q3, rounding=ROUND_HALF_UP),
            total_cost=cost.quantize(Q2, rounding=ROUND_HALF_UP),
            fuel_liters=liters.quantize(Q2, rounding=ROUND_HALF_UP),
        )

    elif mode == 'FUEL_NEEDED':
        distance = d('distance_km')
        consumption = d('consumption')
        price = d('price_per_liter')
        liters = consumption / 100 * distance
        cost = liters * price
        return SimpleResult(
            mode=mode,
            fuel_liters=liters.quantize(Q2, rounding=ROUND_HALF_UP),
            total_cost=cost.quantize(Q2, rounding=ROUND_HALF_UP),
        )

    else:
        raise ValueError(f'Unknown mode: {mode}')
