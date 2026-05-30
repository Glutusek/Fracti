$dataDir = "C:\osrm-data"
$pbfFile = "$dataDir\poland-latest.osm.pbf"
$url = "https://download.geofabrik.de/europe/poland-latest.osm.pbf"

if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Force $dataDir | Out-Null
}

if (Test-Path $pbfFile) {
    Write-Host "Plik juz istnieje: $pbfFile" -ForegroundColor Green
    exit 0
}

Write-Host "Pobieranie danych OSM dla Polski (~1.5GB)..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $url -OutFile $pbfFile
Write-Host "Pobrano. Uruchom: docker compose up -d osrm" -ForegroundColor Green
Write-Host "Preprocessing zajmie ~20-40 min (jednorazowo)." -ForegroundColor Yellow
