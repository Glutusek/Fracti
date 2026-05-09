"""
Django management command to seed test data for heatmap visualization.
Creates receipts at various Polish cities to simulate a trip.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from receipts.models import Settlement, Receipt, Product, CategoryChoices
from decimal import Decimal
import random
from datetime import datetime, timedelta

# Polish cities with coordinates (lat, lng)
POLISH_CITIES = [
    {"name": "Warszawa", "lat": 52.2297, "lng": 21.0122, "region": "Mazovia"},
    {"name": "Kraków", "lat": 50.0647, "lng": 19.9450, "region": "Little Poland"},
    {"name": "Gdańsk", "lat": 54.3520, "lng": 18.6466, "region": "Pomerania"},
    {"name": "Wrocław", "lat": 51.1079, "lng": 17.0385, "region": "Lower Silesia"},
    {"name": "Poznań", "lat": 52.4064, "lng": 16.9252, "region": "Greater Poland"},
    {"name": "Łódź", "lat": 51.7658, "lng": 19.4560, "region": "Łódź"},
    {"name": "Sopot", "lat": 54.4516, "lng": 18.5607, "region": "Pomerania"},
    {"name": "Gdynia", "lat": 54.519637, "lng": 18.529816, "region": "Pomerania"},
    {"name": "Toruń", "lat": 53.6139, "lng": 18.5974, "region": "Kuyavia-Pomerania"},
    {"name": "Szczecin", "lat": 53.4285, "lng": 14.5528, "region": "West Pomerania"},
    {"name": "Katowice", "lat": 50.2645, "lng": 19.0238, "region": "Silesia"},
    {"name": "Warszawa (Mall)", "lat": 52.1956, "lng": 21.0881, "region": "Mazovia"},
]

MERCHANTS = {
    "FOOD": ["Piekarnia Kowalskiego", "Restauracja Pod Kasztanem", "Supermarket Carrefour", "Żabka", "Biedronka", "Steak House", "Pizzeria Roma"],
    "TRANSPORT": ["PKP", "Uber", "Taxi Warszawa", "Paliwo", "Benzyna", "Orlen", "PKN"],
    "ACCOMMODATION": ["Hotel Marriott", "Hostel Happy", "Airbnb", "Hotel Złota Warszawa", "Noclegi.pl"],
    "ENTERTAINMENT": ["Cinema City", "Kino Multikino", "Teatr Wielki", "Muzeum Prado", "Aquapark"],
    "SHOPPING": ["H&M", "Zara", "Nike Store", "Apple", "Empik", "Galeria Handlowa Arkadia"],
    "SERVICES": ["Salon fryzjerski", "Klinika dentystyczna", "Pralnia chemiczna", "Oprawiacz", "SPA"],
}

PRODUCT_NAMES = {
    "FOOD": ["Chlebek", "Mleko", "Jajka", "Masło", "Chleb żytni", "Bułki", "Pizza", "Pierogi", "Barszcz", "Zurek"],
    "TRANSPORT": ["Bilet", "Paliwo", "Przegląd", "Olej", "Kółka", "Serwis"],
    "ACCOMMODATION": ["Noclegi", "Pokój", "Suite", "Parking"],
    "ENTERTAINMENT": ["Bilet", "Popcorn", "Napój", "Lody"],
    "SHOPPING": ["Koszulka", "Spodnie", "Buty", "Torebka", "Płaszcz", "Telefon"],
    "SERVICES": ["Strzyżenie", "Zabiegi", "Masaż", "Konsultacja"],
}

AMOUNTS = {
    "FOOD": (10, 150),
    "TRANSPORT": (20, 100),
    "ACCOMMODATION": (100, 500),
    "ENTERTAINMENT": (20, 80),
    "SHOPPING": (30, 300),
    "SERVICES": (30, 150),
}

CATEGORIES = [
    CategoryChoices.FOOD,
    CategoryChoices.TRANSPORT,
    CategoryChoices.ACCOMMODATION,
    CategoryChoices.ENTERTAINMENT,
    CategoryChoices.SHOPPING,
    CategoryChoices.SERVICES,
]

class Command(BaseCommand):
    help = "Seed database with test receipts across Polish cities for heatmap testing"

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of receipts per city (default: 5)',
        )
        parser.add_argument(
            '--settlement',
            type=str,
            help='Settlement name (creates new if not exists)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='test123',
            help='Password for test_user (default: test123)',
        )

    def handle(self, *args, **options):
        count_per_city = options['count']
        settlement_name = options['settlement'] or "Test Trip Polska"
        password = options['password']

        self.stdout.write(self.style.SUCCESS(f'🌱 Starting seeder with {count_per_city} receipts per city...'))

        # Get or create user
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
        )
        
        # Set password
        user.set_password(password)
        user.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created user: {user.username}'))
        else:
            self.stdout.write(f'  → Using existing user: {user.username}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Password set to: {password}'))

        # Get or create settlement
        settlement, created = Settlement.objects.get_or_create(
            name=settlement_name,
            defaults={'owner': user}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created settlement: {settlement.name}'))
        else:
            self.stdout.write(f'  → Using existing settlement: {settlement.name}')

        # Add user to settlement members
        settlement.members.add(user)

        total_receipts = 0
        total_products = 0

        # Create receipts for each city
        for city in POLISH_CITIES:
            for i in range(count_per_city):
                # Random category
                category_value = random.choice(CATEGORIES)
                merchant = random.choice(MERCHANTS.get(category_value, ['Unknown Merchant']))

                # Random date in last 30 days
                days_ago = random.randint(0, 30)
                purchase_date = datetime.now() - timedelta(days=days_ago)

                # Create receipt with placeholder amount (will be updated after creating products)
                receipt = Receipt.objects.create(
                    settlement=settlement,
                    merchant_name=merchant,
                    total_amount=Decimal('0'),
                    purchase_date=purchase_date,
                    category=category_value,
                    purchaser=user,
                    location=Point(city['lng'], city['lat'], srid=4326),
                    description=f"Purchase in {city['name']} - {city['region']}",
                )

                # Create 1-3 products and calculate total
                num_products = random.randint(1, 3)
                product_total = Decimal('0')
                for j in range(num_products):
                    product_name = random.choice(PRODUCT_NAMES.get(category_value, ['Product']))
                    # Price ranges based on category
                    min_price, max_price = AMOUNTS.get(category_value, (5, 50))
                    product_price = Decimal(str(round(random.uniform(min_price / 3, max_price / 3), 2)))

                    Product.objects.create(
                        receipt=receipt,
                        settlement=settlement,
                        name=f"{product_name} #{j+1}",
                        price=product_price,
                        category=category_value,
                        purchaser=user,
                        location=receipt.location,
                    )
                    product_total += product_price
                    total_products += 1

                # Update receipt total to match sum of products
                receipt.total_amount = product_total
                receipt.save()
                total_receipts += 1

            self.stdout.write(f'  ✓ {city["name"]:15} - {count_per_city} receipts')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Seeding complete!\n'
            f'   📄 Created {total_receipts} receipts\n'
            f'   📦 Created {total_products} products\n'
            f'   📍 Across {len(POLISH_CITIES)} Polish cities\n'
            f'   👤 Settlement: {settlement.name} (ID: {settlement.id})'
        ))
