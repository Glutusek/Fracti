import os
from celery import Celery

# Ustawiamy domyślne ustawienia Django dla Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fracti.settings')

app = Celery('fracti')

# Wczytujemy konfigurację z pliku settings.py (wszystko z prefixem CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatycznie wykrywamy pliki tasks.py w aplikacjach (np. w receipts)
app.autodiscover_tasks()