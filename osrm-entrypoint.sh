#!/bin/sh
set -e

if [ ! -f /data/poland-latest.osm.pbf ]; then
  echo "=== OSRM: brak pliku /data/poland-latest.osm.pbf — pobierz go na hosta ==="
  exit 1
fi

if [ ! -f /data/poland-latest.osrm.partition ]; then
  echo "=== OSRM: preprocessing start ==="
  osrm-extract -p /opt/car.lua /data/poland-latest.osm.pbf
  osrm-partition /data/poland-latest.osrm
  osrm-customize /data/poland-latest.osrm
  echo "=== OSRM: preprocessing gotowy ==="
fi

exec osrm-routed --algorithm mld /data/poland-latest.osrm --max-table-size 10000
