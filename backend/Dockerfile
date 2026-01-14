FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE - nie twórz plików .pyc (zbędne w kontenerze)
# PYTHONUNBUFFERED - logi wypisuj od razu na konsolę (ważne przy debugowaniu)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# binutils, libproj-dev, gdal-bin -> wymagane przez PostGIS/GeoDjango
# libgl1, libglib2.0-0 -> wymagane przez OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    binutils \
    libproj-dev \
    gdal-bin \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-pol \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]