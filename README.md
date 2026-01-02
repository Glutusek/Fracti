# Fracti - Receipt Splitter & Tracker

**Fracti** to nowoczesna platforma webowa służąca do automatyzacji rozliczania wspólnych zakupów. System wykorzystuje technologię OCR (Optical Character Recognition) do odczytu pozycji z paragonów, logikę grup rozliczeniowych do sprawiedliwego podziału kosztów oraz GIS (Geographic Information System) do wizualizacji miejsc zakupu na mapie.

## 🏗 Stack Technologiczny

Projekt realizowany w architekturze mikroserwisowej (Monorepo):

* **Backend:** Python 3.12, Django 5.1, Django REST Framework.
* **Autoryzacja:** JWT (SimpleJWT) - zabezpieczony dostęp do danych użytkownika i grup.
* **Baza Danych & GIS:** PostgreSQL 16 + PostGIS 3.4 (Geometria).
* **Asynchroniczność:** Celery 5.4 + Redis 7.4 (Kolejkowanie zadań OCR).
* **Przetwarzanie Obrazu (OCR):**
    * **Silnik:** Tesseract OCR (z pakietem języka polskiego).
    * **Biblioteki:** OpenCV + Pillow (preprocessing), pytesseract (wrapper).
* **Frontend:** Vue.js 3.5 (Composition API) + Vite + Pinia + TypeScript.
* **Mapy:** Leaflet + OpenStreetMap (Tiles) + Nominatim (Geocoding).
* **Infrastruktura:** Docker Compose V2.

## 🌟 Kluczowe Funkcjonalności

- **System Rozliczeń (Settlements):** Tworzenie grup, zapraszanie członków za pomocą unikalnych kodów i wspólne zarządzanie wydatkami.
- **Inteligentne Rozpoznawanie Paragonów:** Automatyczne wyodrębnianie produktów, cen i sprzedawców dzięki OCR.
- **Podział Kosztów:** Precyzyjne przypisywanie produktów do konkretnych konsumentów w ramach rozliczenia.
- **Wizualizacja Mapowa:** Śledzenie lokalizacji zakupów na interaktywnej mapie GIS z możliwością filtrowania po rozliczeniach.
- **Bezpieczeństwo:** Pełna autoryzacja JWT, chroniąca prywatność danych i dostęp do grup.

## 🚀 Quick Start (Jak uruchomić)

Wymagane jest posiadanie zainstalowanego **Docker Desktop** oraz **Git**.

### 1. Pobranie projektu
```bash
git clone <adres_repozytorium>
cd fracti
```

### 2. Uruchomienie środowiska
Budujemy obrazy i uruchamiamy kontenery:
```bash
docker compose up --build
```

### 3. Inicjalizacja bazy danych i kont
Po uruchomieniu kontenerów (gdy zobaczysz logi startowe Django), wykonaj migracje oraz utwórz administratora:
```bash
# Wygenerowanie migracji (jeśli zmieniano modele)
docker compose exec backend python manage.py makemigrations

# Migracje bazy danych
docker compose exec backend python manage.py migrate

# Utworzenie Superusera
docker compose exec backend python manage.py createsuperuser
```

### 4. Dostęp do aplikacji
- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000/api/](http://localhost:8000/api/)
- **Panel Admina:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

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

## Autorzy

Projekt realizowany w ramach przedmiotów Programowanie w Internecie i Systemy informacji przestrzennej GIS.

**Kamil Wieczorek 200814**

**Sebastian Rogiński 200800**