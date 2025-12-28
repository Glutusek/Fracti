import uuid
from django.contrib.gis.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.core.validators import MinValueValidator


# --- ABSTRAKCYJNA KLASA GEO (Bez zmian) ---
class MapItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.PointField(_("Lokalizacja"), geography=True, srid=4326, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# --- NOWOŚĆ: MODEL ROZLICZENIA (GRUPY) ---
class Settlement(models.Model):
    """
    Reprezentuje grupę rozliczeniową (np. 'Wyjazd w Tatry').
    To jest kontener dla paragonów i użytkowników.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Nazwa rozliczenia"), max_length=255)
    description = models.TextField(_("Opis"), blank=True)

    # Kto należy do tego rozliczenia? (Many-to-Many: User może być w wielu grupach)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='settlements',
        verbose_name=_("Członkowie")
    )

    # Token do zapraszania znajomych (Bezpieczeństwo)
    join_code = models.UUIDField(default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.members.count()} os.)"

    # Logika biznesowa: Suma wydatków w grupie
    @property
    def total_expenses(self):
        # 1. Suma z paragonów
        receipts_total = sum(r.total_amount for r in self.receipts.all() if r.total_amount)
        products_total = sum(p.price for p in self.products.filter(receipt__isnull=True))

        return receipts_total + products_total


# --- MODEL PARAGONU (ZMODYFIKOWANY) ---
class Receipt(MapItem):
    merchant_name = models.CharField(_("Nazwa sklepu"), max_length=255)
    purchase_date = models.DateTimeField(_("Data zakupu"), null=True, blank=True)
    total_amount = models.DecimalField(_("Kwota całkowita"), max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='receipts/%Y/%m/', null=True, blank=True)

    # Kto zapłacił? (Płatnik)
    purchaser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchased_receipts',
        null=True, blank=True
    )

    # NOWOŚĆ: Do którego rozliczenia to należy?
    settlement = models.ForeignKey(
        Settlement,
        on_delete=models.CASCADE,  # Jak usuniesz grupę, paragony też znikną (lub SET_NULL)
        related_name='receipts',
        null=True,  # Paragon może być prywatny (bez grupy)
        blank=True
    )

    class Meta:
        verbose_name = _("Paragon")
        verbose_name_plural = _("Paragony")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.merchant_name} - {self.total_amount} PLN"


# --- MODEL PRODUKTU (Bez zmian, ale przypominam) ---
class Product(MapItem):

    name = models.CharField(_("Nazwa produktu"), max_length=255)
    price = models.DecimalField(_("Cena"), max_digits=10, decimal_places=2)
    receipt = models.ForeignKey(Receipt, on_delete=models.SET_NULL, related_name='products', null=True, blank=True)
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, related_name='products', null=True, blank=True, verbose_name=_("Przypisane rozliczenie"))
    consumers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='consumed_products', blank=True, verbose_name=_("Konsumenci"))

    def __str__(self):
        return f"{self.name} ({self.price})"