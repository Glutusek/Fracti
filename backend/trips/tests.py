from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point

from receipts.models import Settlement
from .models import Trip, TripStop, TripParticipant, TripLeg, TripOtherCost
from .services import (
    rebalance_leg_consumptions, compute_trip_split,
    compute_simple_mode, InconsistentConsumptionError,
)

User = get_user_model()


def make_user(username='driver'):
    return User.objects.create_user(username=username, password='x')


def make_trip(owner, **kwargs):
    defaults = dict(
        name='Test trip',
        global_consumption_l_per_100km=Decimal('5.000'),
        fuel_price_per_liter=Decimal('6.0000'),
        total_tolls=Decimal('0.00'),
    )
    defaults.update(kwargs)
    return Trip.objects.create(owner=owner, **defaults)


def make_stop(trip, order, lat=52.0, lon=21.0, name=''):
    return TripStop.objects.create(
        trip=trip, order=order, name=name,
        location=Point(lon, lat),
    )


def make_participant(trip, user=None, guest_label='', color='#ff0000'):
    return TripParticipant.objects.create(
        trip=trip, user=user, guest_label=guest_label, color=color,
    )


def make_leg(trip, order, from_stop, to_stop, dist, consumption=None, override=False, participants=None):
    leg = TripLeg.objects.create(
        trip=trip, order=order,
        from_stop=from_stop, to_stop=to_stop,
        distance_km=Decimal(str(dist)),
        consumption_l_per_100km=Decimal(str(consumption)) if consumption else trip.global_consumption_l_per_100km,
        consumption_override=override,
    )
    if participants:
        leg.participants.set(participants)
    return leg


class RebalanceTest(TestCase):
    def setUp(self):
        self.u = make_user()
        self.trip = make_trip(self.u, global_consumption_l_per_100km=Decimal('5.000'))
        self.s0 = make_stop(self.trip, 0)
        self.s1 = make_stop(self.trip, 1, lat=52.5)
        self.s2 = make_stop(self.trip, 2, lat=53.0)

    def test_spec_example(self):
        """G=5, A→B=50km, B→C=150km, override B→C=6 → A→B auto=2."""
        l1 = make_leg(self.trip, 0, self.s0, self.s1, 50)
        l2 = make_leg(self.trip, 1, self.s1, self.s2, 150, consumption=6, override=True)
        rebalance_leg_consumptions(self.trip)
        l1.refresh_from_db()
        self.assertEqual(l1.consumption_l_per_100km, Decimal('2.000'))
        l2.refresh_from_db()
        self.assertEqual(l2.consumption_l_per_100km, Decimal('6.000'))

    def test_all_overridden_updates_global(self):
        """All legs overridden → global recalculated."""
        make_leg(self.trip, 0, self.s0, self.s1, 100, consumption=6, override=True)
        make_leg(self.trip, 1, self.s1, self.s2, 100, consumption=8, override=True)
        rebalance_leg_consumptions(self.trip)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.global_consumption_l_per_100km, Decimal('7.000'))

    def test_inconsistent_raises(self):
        """Overrides exceed global budget → InconsistentConsumptionError."""
        make_leg(self.trip, 0, self.s0, self.s1, 50)
        make_leg(self.trip, 1, self.s1, self.s2, 150, consumption=10, override=True)
        with self.assertRaises(InconsistentConsumptionError):
            rebalance_leg_consumptions(self.trip)


class ComputeSplitTest(TestCase):
    def setUp(self):
        self.driver = make_user('driver')
        self.passenger = make_user('passenger')
        self.passenger2 = make_user('passenger2')
        self.trip = make_trip(
            self.driver,
            global_consumption_l_per_100km=Decimal('10.000'),
            fuel_price_per_liter=Decimal('6.0000'),
            total_tolls=Decimal('0.00'),
        )
        self.s0 = make_stop(self.trip, 0)
        self.s1 = make_stop(self.trip, 1, lat=52.5)
        self.s2 = make_stop(self.trip, 2, lat=53.0)

    def test_driver_pays_model(self):
        """Passenger who boards at stop 2 pays only leg 2."""
        p_driver = make_participant(self.trip, user=self.driver)
        p_pass = make_participant(self.trip, user=self.passenger)
        p_late = make_participant(self.trip, user=self.passenger2)
        self.trip.payer = p_driver
        self.trip.save()

        make_leg(self.trip, 0, self.s0, self.s1, 100, participants=[p_driver, p_pass])
        make_leg(self.trip, 1, self.s1, self.s2, 100, participants=[p_driver, p_pass, p_late])

        result = compute_trip_split(self.trip)
        self.assertEqual(len(result.debts), 2)

        debts_by_debtor = {d.debtor_id: d for d in result.debts}
        pass_pid = str(p_pass.id)
        late_pid = str(p_late.id)

        # passenger on both legs: 100km * 10L/100 / 100 * 6 / 2 (leg1 2 people)
        # leg1: 10L * 6 / 2 = 30, leg2: 10L * 6 / 3 = 20 → total 50
        self.assertEqual(debts_by_debtor[pass_pid].amount, Decimal('50.00'))
        # late passenger only leg2: 10L * 6 / 3 = 20
        self.assertEqual(debts_by_debtor[late_pid].amount, Decimal('20.00'))

    def test_other_cost_split_all(self):
        """Other cost split ALL divides equally among all participants."""
        p_driver = make_participant(self.trip, user=self.driver)
        p_pass = make_participant(self.trip, user=self.passenger)
        self.trip.payer = p_driver
        self.trip.save()
        make_leg(self.trip, 0, self.s0, self.s2, 100, participants=[p_driver, p_pass])
        TripOtherCost.objects.create(trip=self.trip, label='Parking', amount=Decimal('20.00'), split_scope='ALL')
        result = compute_trip_split(self.trip)
        pass_debt = next(d for d in result.debts if d.debtor_id == str(p_pass.id))
        self.assertEqual(pass_debt.breakdown['other'], '10.00')


class SimpleCalculatorTest(TestCase):
    def test_trip_cost(self):
        r = compute_simple_mode('TRIP_COST', {
            'distance_km': '100', 'consumption': '7', 'price_per_liter': '6.50', 'n': 4
        })
        self.assertEqual(r.total_cost, Decimal('45.50'))
        self.assertEqual(r.per_person, Decimal('11.38'))
        self.assertEqual(r.fuel_liters, Decimal('7.00'))

    def test_distance(self):
        r = compute_simple_mode('DISTANCE', {
            'liters': '10', 'consumption': '10', 'price_per_liter': '6.00'
        })
        self.assertEqual(r.distance_km, Decimal('100.00'))
        self.assertEqual(r.total_cost, Decimal('60.00'))

    def test_consumption_rate(self):
        r = compute_simple_mode('CONSUMPTION_RATE', {
            'distance_km': '200', 'liters': '14', 'price_per_liter': '6.00'
        })
        self.assertEqual(r.consumption_l_per_100km, Decimal('7.000'))

    def test_fuel_needed(self):
        r = compute_simple_mode('FUEL_NEEDED', {
            'distance_km': '100', 'consumption': '7', 'price_per_liter': '6.50'
        })
        self.assertEqual(r.fuel_liters, Decimal('7.00'))
        self.assertEqual(r.total_cost, Decimal('45.50'))
