import uuid
import decimal
import django.contrib.gis.db.models.fields
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('receipts', '0018_add_location_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='Nazwa')),
                ('description', models.TextField(blank=True, verbose_name='Opis')),
                ('trip_date', models.DateTimeField(blank=True, null=True, verbose_name='Data podróży')),
                ('global_consumption_l_per_100km', models.DecimalField(decimal_places=3, default=decimal.Decimal('7.000'), max_digits=6, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.001'))], verbose_name='Średnie spalanie L/100km')),
                ('fuel_price_per_liter', models.DecimalField(decimal_places=4, default=decimal.Decimal('6.5000'), max_digits=8, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.0001'))], verbose_name='Cena paliwa PLN/L')),
                ('currency', models.CharField(default='PLN', max_length=3, verbose_name='Waluta')),
                ('total_tolls', models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.00'))], verbose_name='Opłaty drogowe')),
                ('route_polyline', django.contrib.gis.db.models.fields.LineStringField(blank=True, geography=True, null=True, srid=4326, verbose_name='Trasa')),
                ('total_distance_km', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='Łączny dystans km')),
                ('total_fuel_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Koszt paliwa')),
                ('total_other_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Inne koszty')),
                ('total_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Całkowity koszt')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trips', to=settings.AUTH_USER_MODEL, verbose_name='Właściciel')),
                ('settlement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trips', to='receipts.settlement', verbose_name='Rozliczenie')),
                ('linked_receipt', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_trip', to='receipts.receipt', verbose_name='Powiązany paragon')),
            ],
            options={
                'verbose_name': 'Podróż',
                'verbose_name_plural': 'Podróże',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TripStop',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order', models.PositiveIntegerField(verbose_name='Kolejność')),
                ('name', models.CharField(blank=True, max_length=255, verbose_name='Nazwa')),
                ('location', django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326, verbose_name='Lokalizacja')),
                ('arrived_at', models.DateTimeField(blank=True, null=True, verbose_name='Przyjazd')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stops', to='trips.trip')),
            ],
            options={
                'verbose_name': 'Przystanek',
                'verbose_name_plural': 'Przystanki',
                'ordering': ['order'],
                'unique_together': {('trip', 'order')},
            },
        ),
        migrations.CreateModel(
            name='TripParticipant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('guest_label', models.CharField(blank=True, max_length=255, verbose_name='Gość (imię)')),
                ('color', models.CharField(blank=True, max_length=7, verbose_name='Kolor')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='trips.trip')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trip_participations', to=settings.AUTH_USER_MODEL, verbose_name='Użytkownik')),
            ],
            options={
                'verbose_name': 'Uczestnik',
                'verbose_name_plural': 'Uczestnicy',
            },
        ),
        migrations.AddConstraint(
            model_name='tripparticipant',
            constraint=models.CheckConstraint(
                check=~models.Q(user__isnull=True, guest_label=''),
                name='participant_user_or_label',
            ),
        ),
        migrations.CreateModel(
            name='TripLeg',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order', models.PositiveIntegerField(verbose_name='Kolejność')),
                ('distance_km', models.DecimalField(decimal_places=3, max_digits=10, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.001'))], verbose_name='Dystans km')),
                ('duration_seconds', models.PositiveIntegerField(default=0, verbose_name='Czas (s)')),
                ('consumption_l_per_100km', models.DecimalField(decimal_places=3, default=decimal.Decimal('7.000'), max_digits=6, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.001'))], verbose_name='Spalanie L/100km')),
                ('consumption_override', models.BooleanField(default=False, verbose_name='Nadpisane spalanie')),
                ('leg_polyline', django.contrib.gis.db.models.fields.LineStringField(blank=True, geography=True, null=True, srid=4326, verbose_name='Trasa odcinka')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legs', to='trips.trip')),
                ('from_stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legs_from', to='trips.tripstop')),
                ('to_stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legs_to', to='trips.tripstop')),
                ('participants', models.ManyToManyField(blank=True, related_name='legs', to='trips.tripparticipant', verbose_name='Uczestnicy na odcinku')),
            ],
            options={
                'verbose_name': 'Odcinek',
                'verbose_name_plural': 'Odcinki',
                'ordering': ['order'],
                'unique_together': {('trip', 'order')},
            },
        ),
        migrations.CreateModel(
            name='TripOtherCost',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=255, verbose_name='Opis')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))], verbose_name='Kwota')),
                ('split_scope', models.CharField(choices=[('ALL', 'Wszyscy równo'), ('LEG', 'Uczestnicy odcinka')], default='ALL', max_length=3, verbose_name='Podział')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='other_costs', to='trips.trip')),
                ('paid_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paid_costs', to='trips.tripparticipant', verbose_name='Zapłacił')),
                ('leg', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='other_costs', to='trips.tripleg', verbose_name='Odcinek')),
            ],
            options={
                'verbose_name': 'Koszt dodatkowy',
                'verbose_name_plural': 'Koszty dodatkowe',
            },
        ),
        migrations.CreateModel(
            name='TripDebt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))], verbose_name='Kwota')),
                ('breakdown', models.JSONField(default=dict, verbose_name='Podział')),
                ('computed_at', models.DateTimeField(auto_now=True)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debts', to='trips.trip')),
                ('debtor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debts_owed', to='trips.tripparticipant')),
                ('creditor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debts_owed_to', to='trips.tripparticipant')),
                ('transferred_to_debt_settlement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_trip_debts', to='receipts.debtsettlement')),
            ],
            options={
                'verbose_name': 'Dług',
                'verbose_name_plural': 'Długi',
                'unique_together': {('trip', 'debtor', 'creditor')},
            },
        ),
        migrations.AddField(
            model_name='trip',
            name='payer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='trips_as_payer', to='trips.tripparticipant', verbose_name='Płatnik'),
        ),
    ]
