# Fracti - Receipt Splitter & Tracker

**Fracti** to nowoczesna platforma webowa służąca do automatyzacji rozliczania wspólnych zakupów. System wykorzystuje technologię OCR (Optical Character Recognition) do odczytu pozycji z paragonów oraz GIS (Geographic Information System) do wizualizacji miejsc zakupu na mapie.

## 🏗 Stack Technologiczny

Projekt realizowany w architekturze mikroserwisowej (Monorepo):

* **Backend:** Python 3.12, Django 5.1, Django REST Framework.
* **Baza Danych & GIS:** PostgreSQL 16 + PostGIS 3.4 (Geometria).
* **Asynchroniczność:** Celery 5.4 + Redis 7.4 (Kolejkowanie zadań OCR).
* **Frontend:** Vue.js 3.5 (Composition API) + Vite + Pinia.
* **Mapy:** OpenStreetMap + Leaflet.
* **Infrastruktura:** Docker Compose V2.

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

### 3. Inicjalizacja bazy danych
Po uruchomieniu kontenerów (gdy zobaczysz logi startowe Django), otwórz nowy terminal w folderze projektu i wykonaj migracje:
```bash
docker compose exec backend python manage.py migrate
```

### 4. Utworzenie administratora
Aby utworzyć konto Superusera do panelu administracyjnego:
```bash
docker compose exec backend python manage.py createsuperuser
```

### 5. Workflow
Zatrzymanie i uruchomienie serwerów 
```bash
docker compose down
docker compose up
```
Przebudowa (po zmianie w requirements.txt lub Dockerfile)
```bash
docker compose up --build
```

## Autorzy

Projekt realizowany w ramach przedmiotów Programowanie w Internecie i Systemy informacji przestrzennej GIS.

**Kamil Wieczorek 200814**

**Sebastian Rogiński 200800**