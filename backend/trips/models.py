import uuid
from django.contrib.gis.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.core.validators import MinValueValidator


class Trip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Nazwa"), max_length=255)
    description = models.TextField(_("Opis"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trips',
        verbose_name=_("Właściciel"),
    )
    settlement = models.ForeignKey(
        'receipts.Settlement',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trips',
        verbose_name=_("Rozliczenie"),
    )
    trip_date = models.DateTimeField(_("Data podróży"), null=True, blank=True)
    global_consumption_l_per_100km = models.DecimalField(
        _("Średnie spalanie L/100km"), max_digits=6, decimal_places=3,
        default=Decimal('7.000'),
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    fuel_price_per_liter = models.DecimalField(
        _("Cena paliwa PLN/L"), max_digits=8, decimal_places=4,
        default=Decimal('6.5000'),
        validators=[MinValueValidator(Decimal('0.0001'))],
    )
    currency = models.CharField(_("Waluta"), max_length=3, default='PLN')
    total_tolls = models.DecimalField(
        _("Opłaty drogowe"), max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    route_polyline = models.LineStringField(
        _("Trasa"), geography=True, srid=4326, null=True, blank=True
    )
    payer = models.ForeignKey(
        'TripParticipant',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='trips_as_payer',
        verbose_name=_("Płatnik"),
    )
    linked_receipt = models.OneToOneField(
        'receipts.Receipt',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='source_trip',
        verbose_name=_("Powiązany paragon"),
    )
    total_distance_km = models.DecimalField(
        _("Łączny dystans km"), max_digits=10, decimal_places=3,
        null=True, blank=True,
    )
    total_fuel_cost = models.DecimalField(
        _("Koszt paliwa"), max_digits=10, decimal_places=2,
        null=True, blank=True,
    )
    total_other_cost = models.DecimalField(
        _("Inne koszty"), max_digits=10, decimal_places=2,
        null=True, blank=True,
    )
    total_cost = models.DecimalField(
        _("Całkowity koszt"), max_digits=10, decimal_places=2,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Podróż")
        verbose_name_plural = _("Podróże")
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TripStop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    order = models.PositiveIntegerField(_("Kolejność"))
    name = models.CharField(_("Nazwa"), max_length=255, blank=True)
    location = models.PointField(_("Lokalizacja"), geography=True, srid=4326)
    arrived_at = models.DateTimeField(_("Przyjazd"), null=True, blank=True)

    class Meta:
        verbose_name = _("Przystanek")
        verbose_name_plural = _("Przystanki")
        unique_together = ('trip', 'order')
        ordering = ['order']

    def __str__(self):
        return f"{self.name or 'Przystanek'} #{self.order}"


class TripParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trip_participations',
        verbose_name=_("Użytkownik"),
    )
    guest_label = models.CharField(_("Gość (imię)"), max_length=255, blank=True)
    color = models.CharField(_("Kolor"), max_length=7, blank=True)

    class Meta:
        verbose_name = _("Uczestnik")
        verbose_name_plural = _("Uczestnicy")
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user__isnull=True, guest_label=''),
                name='participant_user_or_label',
            )
        ]

    @property
    def display_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_label

    def __str__(self):
        return self.display_name


class TripLeg(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='legs')
    order = models.PositiveIntegerField(_("Kolejność"))
    from_stop = models.ForeignKey(
        TripStop, on_delete=models.CASCADE, related_name='legs_from'
    )
    to_stop = models.ForeignKey(
        TripStop, on_delete=models.CASCADE, related_name='legs_to'
    )
    distance_km = models.DecimalField(
        _("Dystans km"), max_digits=10, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    duration_seconds = models.PositiveIntegerField(_("Czas (s)"), default=0)
    consumption_l_per_100km = models.DecimalField(
        _("Spalanie L/100km"), max_digits=6, decimal_places=3,
        default=Decimal('7.000'),
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    consumption_override = models.BooleanField(_("Nadpisane spalanie"), default=False)
    leg_polyline = models.LineStringField(
        _("Trasa odcinka"), geography=True, srid=4326, null=True, blank=True
    )
    participants = models.ManyToManyField(
        TripParticipant,
        blank=True,
        related_name='legs',
        verbose_name=_("Uczestnicy na odcinku"),
    )

    class Meta:
        verbose_name = _("Odcinek")
        verbose_name_plural = _("Odcinki")
        unique_together = ('trip', 'order')
        ordering = ['order']

    def __str__(self):
        return f"Odcinek {self.order}: {self.from_stop} → {self.to_stop}"


class TripOtherCost(models.Model):
    SPLIT_ALL = 'ALL'
    SPLIT_LEG = 'LEG'
    SPLIT_CHOICES = [
        (SPLIT_ALL, _('Wszyscy równo')),
        (SPLIT_LEG, _('Uczestnicy odcinka')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='other_costs')
    label = models.CharField(_("Opis"), max_length=255)
    amount = models.DecimalField(
        _("Kwota"), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    paid_by = models.ForeignKey(
        TripParticipant,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='paid_costs',
        verbose_name=_("Zapłacił"),
    )
    split_scope = models.CharField(
        _("Podział"), max_length=3, choices=SPLIT_CHOICES, default=SPLIT_ALL
    )
    leg = models.ForeignKey(
        TripLeg,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='other_costs',
        verbose_name=_("Odcinek"),
    )

    class Meta:
        verbose_name = _("Koszt dodatkowy")
        verbose_name_plural = _("Koszty dodatkowe")

    def __str__(self):
        return f"{self.label}: {self.amount}"


class TripDebt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='debts')
    debtor = models.ForeignKey(
        TripParticipant, on_delete=models.CASCADE, related_name='debts_owed'
    )
    creditor = models.ForeignKey(
        TripParticipant, on_delete=models.CASCADE, related_name='debts_owed_to'
    )
    amount = models.DecimalField(
        _("Kwota"), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    breakdown = models.JSONField(_("Podział"), default=dict)
    computed_at = models.DateTimeField(auto_now=True)
    transferred_to_debt_settlement = models.ForeignKey(
        'receipts.DebtSettlement',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='source_trip_debts',
    )

    class Meta:
        verbose_name = _("Dług")
        verbose_name_plural = _("Długi")
        unique_together = ('trip', 'debtor', 'creditor')

    def __str__(self):
        return f"{self.debtor} → {self.creditor}: {self.amount}"
