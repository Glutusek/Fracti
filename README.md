# Fracti - Receipt Splitter & Tracker

**Fracti** to nowoczesna platforma webowa służąca do automatyzacji rozliczania wspólnych zakupów. System wykorzystuje technologię OCR (Optical Character Recognition) do odczytu pozycji z paragonów, logikę grup rozliczeniowych do sprawiedliwego podziału kosztów oraz GIS (Geographic Information System) do wizualizacji miejsc zakupu na mapie.

## 🏗 Stack Technologiczny

Projekt realizowany w architekturze mikroserwisowej (Monorepo):

- **Backend:** Python 3.12, Django 5.1, Django REST Framework.
- **Autoryzacja:** JWT (SimpleJWT) - zabezpieczony dostęp do danych użytkownika i grup.
- **Baza Danych & GIS:** PostgreSQL 16 + PostGIS 3.4 (Geometria).
- **Asynchroniczność:** Celery 5.4 + Redis 7.4 (Kolejkowanie zadań OCR).
- **Przetwarzanie Obrazu (OCR):**
  - **Biblioteka:** receipt-ocr (wysokopoziomowa abstrakcja dla OCR)
  - **LLM:** Google Gemini API (via OpenAI-compatible endpoint)
  - **Preprocessing:** Obsługiwany automatycznie przez receipt-ocr
- **Frontend:** Vue.js 3.5 (Composition API) + Vue Router + Vite + TypeScript.
- **Mapy:** Leaflet + OpenStreetMap (Tiles) + Nominatim (Geocoding).
- **Routing:** OSRM (Open Source Routing Machine) - lokalna instancja w Dockerze, dane Geofabrik dla Polski.
- **Infrastruktura:** Docker Compose V2.

## 🌟 Kluczowe Funkcjonalności

- **System Rozliczeń (Settlements):** Tworzenie grup, zapraszanie członków za pomocą unikalnych kodów i wspólne zarządzanie wydatkami.
- **Inteligentne Rozpoznawanie Paragonów:** Automatyczne wyodrębnianie produktów, cen i sprzedawców dzięki OCR.
- **Podział Kosztów:** Precyzyjne przypisywanie produktów do konkretnych konsumentów w ramach rozliczenia.
  - Produkty z paragonów
  - Produkty dodane ręcznie do grupy
  - Walidacja konsumentów przy dodawaniu i edycji produktów
- **Rozliczenia (Debt Settlement):**
  - Automatyczne obliczanie uproszczonych długów między członkami grupy
  - Potwierdzanie rozliczeń z możliwością wycofania
  - Przegląd wykonanych rozliczeń z datą i czasem
- **Wizualizacja Mapowa:** Śledzenie lokalizacji zakupów na interaktywnej mapie GIS z możliwością filtrowania po rozliczeniach.
- **Kalkulator Transportu:** Sprawiedliwe rozliczanie kosztów wspólnej podróży.
  - Tryb prosty (4 sub-tryby: koszt, dystans, spalanie, paliwo) - bezstanowy
  - Tryb zaawansowany - real road routing przez lokalny OSRM, edytowalne waypointy, klik/drag do dodania przystanków
  - Per-leg consumption override z automatycznym rebalansem
  - Driver-pays model: pasażerowie zwracają kierowcy proporcjonalnie do faktycznie przejechanego dystansu
  - Tolls (proporcjonalnie do dystansu) + inne koszty (split ALL/LEG)
  - Live preview wyników bez konieczności zapisu
  - Transfer wyniku do Settlement jako Receipt + Products
- **Bezpieczeństwo:** Pełna autoryzacja JWT, chroniąca prywatność danych i dostęp do grup.

## 📊 Model Danych

### Kluczowe Modele:

- **Settlement:** Grupa rozliczeniowa z członkami
- **Receipt:** Paragon z produktami
- **Product:** Produkt (z paragonu lub dodany ręcznie) z przypisanymi konsumentami
- **DebtSettlement:** Zapis potwierdzonego rozliczenia między dwoma użytkownikami
- **User:** Użytkownik systemu (z JWT)
- **Trip:** Podróż w kalkulatorze transportu (opcjonalnie powiązana z Settlement)
- **TripStop / TripLeg / TripParticipant / TripOtherCost / TripDebt:** Składniki Trip - przystanki (PointField), odcinki, uczestnicy z board/alight stop, inne koszty, wyniki rozliczenia

### Relacje:

- Produkty usuwane są kaskadowo z paragonami
- DebtSettlement przechowuje historię rozliczeń z timestampem

## 🚀 Quick Start (Jak uruchomić)

Wymagane jest posiadanie zainstalowanego **Docker Desktop** oraz **Git**.

### 1. Pobranie projektu

```bash
git clone <adres_repozytorium>
cd fracti
```

### 2. ⚙️ Konfiguracja modelu AI (Gemini)

Aplikacja korzysta z modelu Gemini 2.5 Flash Lite od Google, ale używa klienta kompatybilnego z OpenAI. Dzięki temu konfiguracja jest prosta, ale wymaga odpowiedniego klucza.

Utwórz plik konfiguracyjny: Skopiuj przykładowy plik .env.example i zmień jego nazwę na .env:

```bash
cp .env.example .env
```

Pobierz darmowy klucz API: Wejdź na stronę [Google AI Studio](https://aistudio.google.com/app/api-keys)
i wygeneruj nowy klucz API

**Uzupełnij plik `.env`** Otwórz plik `.env` i wklej swój klucz. Skonfiguruj zmienne dokładnie tak, jak poniżej:

```ini
# 🔑 SECRET_KEY - Generuj lokalnie, nigdy nie commituj!
# Wygeneruj nowy klucz komendą:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_SECRET_KEY=your-generated-secret-key-here

# Django Debug Mode (postaw na False w produkcji)
DJANGO_DEBUG=False

# 🔑 Wklej tutaj swój klucz z Google AI Studio (zaczyna się od "AIza...")
# UWAGA: Mimo nazwy zmiennej, podajemy tu klucz GOOGLE!
OPENAI_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 🌐 Te wartości zostaw bez zmian (wymagane do połączenia z Google):
OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
OPENAI_MODEL=gemini-2.5-flash-lite
```

> **Dlaczego `OPENAI_API_KEY`?**
> Aplikacja korzysta z biblioteki klienckiej zaprojektowanej dla OpenAI, ale przekierowuje zapytania do Google (`OPENAI_BASE_URL`).
> Dlatego **musisz** wkleić klucz Gemini w pole `OPENAI_API_KEY`.
> Nie zmieniaj nazw zmiennych, w przeciwnym razie aplikacja nie zadziała.

🛡️ Bezpieczeństwo
Upewnij się, że plik `.env` znajduje się w Twoim `.gitignore`. Nigdy nie udostępniaj swojego klucza API publicznie!

### 3. Pobranie danych routingowych OSRM

Kalkulator transportu używa **lokalnej instancji OSRM** do wyznaczania tras po prawdziwych drogach. Wymaga pobrania danych OSM dla Polski (~1.5 GB, jednorazowo).

**Windows (PowerShell):**

```powershell
.\setup-osrm.ps1
```

Skrypt utworzy folder `C:\osrm-data\` i pobierze plik `poland-latest.osm.pbf` z Geofabrik. Po pobraniu OSRM przy pierwszym uruchomieniu wykona preprocessing (extract + partition + customize, ~20-40 min). Wynik cache'owany w `C:\osrm-data\`, kolejne starty są natychmiastowe.

**Linux/macOS (alternatywnie):**

```bash
mkdir -p /var/osrm-data
curl -L -o /var/osrm-data/poland-latest.osm.pbf https://download.geofabrik.de/europe/poland-latest.osm.pbf
```

Następnie zmień w `docker-compose.yml` wolumen z `C:/osrm-data:/data` na `/var/osrm-data:/data`.

> **Uwaga:** Każdy deweloper musi to zrobić raz — pliki są za duże dla repo. Po pierwszym preprocessingu kontener OSRM startuje od razu i nasłuchuje na porcie 5000.

### 4. Uruchomienie środowiska

Budujemy obrazy i uruchamiamy kontenery:

```bash
docker compose up --build
```

OSRM startuje równolegle. Pierwsze uruchomienie wymaga ~20-40 min na preprocessing danych OSM (widać postęp w `docker logs -f fracti_osrm`). Reszta stacku (backend, frontend, db, redis, celery) wystartuje od razu — kalkulator transportu będzie zwracał błąd routingu dopóki OSRM nie skończy preprocessingu.

### 5. Inicjalizacja bazy danych i kont

Po uruchomieniu kontenerów (gdy zobaczysz logi startowe Django), wykonaj migracje oraz utwórz administratora:

```bash
# Wygenerowanie migracji (jeśli zmieniano modele)
docker compose exec backend python manage.py makemigrations

# Migracje bazy danych
docker compose exec backend python manage.py migrate

# Utworzenie Superusera
docker compose exec backend python manage.py createsuperuser
```

### 5.5 Zaseedowanie bazy danych (opcjonalnie)

Aby przetestować aplikację z przykładowymi danymi, możesz zasiać bazę testowymi paragoniami rozmieszczonymi w polskich miastach:

```bash
# Defaultowe: 5 paragonów na miasto, użytkownik test_user, hasło test123
docker compose exec backend python manage.py seed_heatmap

# Niestandardowe parametry:
docker compose exec backend python manage.py seed_heatmap --count 10 --settlement "Moja Podróż" --password mypassword123
```

**Parametry:**

- `--count` (default: 5) - Liczba paragonów na każde miasto
- `--settlement` (default: "Test Trip Polska") - Nazwa grupy rozliczeniowej
- `--password` (default: "test123") - Hasło dla użytkownika test_user

**Po zasianiu będziesz mieć:**

- ✅ Użytkownika `test_user` z danym hasłem
- ✅ Grupę rozliczeniową z opisaną nazwą
- ✅ 60 paragonów (12 miast × liczba paragonów na miasto)
- ✅ ~180 produktów (średnio 3 produkty na paragon)
- ✅ Wszystkie lokalizacje na mapie Polski

Możesz teraz zalogować się na `test_user` i przetestować heatmapę!

### 6. Dostęp do aplikacji

- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000/api/](http://localhost:8000/api/)
- **Panel Admina:** [http://localhost:8000/admin/](http://localhost:8000/admin/)
- **OSRM Routing API:** [http://localhost:5000/](http://localhost:5000/)

## 🛠 Workflow deweloperski

Zatrzymanie i uruchomienie serwerów:

```bash
docker compose down
docker compose up
```

Przebudowa (po zmianie w requirements.txt lub Dockerfile):

```bash
docker compose up --build
```

Przydatne komendy Django:

```bash
# Sprawdzenie stanu migracji
docker compose exec backend python manage.py showmigrations

# Reset bazy danych (uwaga: usuwa dane!)
docker compose down -v
docker compose up
```

### Logi OSRM

```bash
docker logs -f fracti_osrm
```

Wyglądający na zdrowy OSRM:
```
[info] starting up engines, v5.26.0
[info] Listening on: 0.0.0.0:5000
[info] running and waiting for requests
```

### Reset preprocessingu OSRM

Jeśli chcesz odświeżyć dane drogowe (Geofabrik aktualizuje co tydzień), usuń pliki `.osrm*` z `C:\osrm-data\` (zostaw `poland-latest.osm.pbf` lub pobierz nowy) i zrestartuj kontener:

```powershell
Remove-Item C:\osrm-data\poland-latest.osrm*
docker compose restart osrm
```

## Autorzy

Projekt realizowany w ramach przedmiotów Programowanie w Internecie i Systemy informacji przestrzennej GIS.

**Kamil Wieczorek 200814**

**Sebastian Rogiński 200800**
