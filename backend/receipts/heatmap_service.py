"""
Heatmap aggregation service using PostGIS ST_HexagonGrid.
Aggregates Receipt and Product financial data into hexagonal grid.
"""
from django.contrib.gis.geos import Polygon
from django.core.cache import cache
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import hashlib

from .models import Receipt, Product, Settlement


class HeatmapAggregator:
    """Aggregate Receipt and Product data into hexagonal heatmap grid."""
    
    def __init__(self, settlement: Settlement):
        self.settlement = settlement
    
    def get_heatmap_data(
        self,
        bbox: Tuple[float, float, float, float],  # (min_lon, min_lat, max_lon, max_lat)
        grid_resolution: int = 9,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        categories: Optional[List[str]] = None,
        user_ids: Optional[List[int]] = None,
        bbox_buffer_percent: float = 0.1,
        cell_size: Optional[float] = None,
        show_empty_hexagons: bool = True,
    ) -> List[Dict]:
        """
        Aggregate Receipt and Product data into hexagonal grid.
        
        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat) in EPSG:4326
            grid_resolution: H3 resolution or PostGIS hexagon resolution (higher = smaller cells)
            date_from: Filter receipts after this date (YYYY-MM-DD)
            date_to: Filter receipts before this date (YYYY-MM-DD)
            categories: Filter by expense categories (FOOD, TRANSPORT, etc.)
            user_ids: Filter by purchaser user IDs
            bbox_buffer_percent: Buffer around bbox as % of bbox size (0.1 = 10%)
            cell_size: Optional - cell size in degrees for PostGIS grid (if not set, computed from grid_resolution)
        
        Returns:
            List of hexagon data: [
                {
                    "hexagon_id": "string",
                    "geometry": {geojson polygon},
                    "weight": decimal sum of amounts,
                    "center_lat": float,
                    "center_lng": float,
                    "point_count": int
                }
            ]
        """
        # Generate cache key from parameters
        cache_key = self._generate_cache_key(bbox, grid_resolution, date_from, date_to, categories, user_ids, bbox_buffer_percent, cell_size)
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"[DEBUG] Cache HIT for heatmap: {cache_key}")
            return cached_result
        
        print(f"[DEBUG] Cache MISS for heatmap: {cache_key}")
        
        # Build bbox with buffer
        min_lon, min_lat, max_lon, max_lat = bbox
        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat
        
        buffered_bbox = (
            min_lon - (lon_range * bbox_buffer_percent),
            min_lat - (lat_range * bbox_buffer_percent),
            max_lon + (lon_range * bbox_buffer_percent),
            max_lat + (lat_range * bbox_buffer_percent),
        )
        
        # Create bbox polygon
        bbox_geom = Polygon.from_bbox(buffered_bbox)
        
        # Build Receipt queryset with filters
        receipts = Receipt.objects.filter(
            settlement=self.settlement,
            location__isnull=False
        )
        
        # Apply date filters
        if date_from:
            receipts = receipts.filter(purchase_date__gte=datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            receipts = receipts.filter(purchase_date__lte=datetime.strptime(date_to, '%Y-%m-%d'))
        
        # Apply category filter
        if categories:
            receipts = receipts.filter(category__in=categories)
        
        # Apply user filter (purchaser)
        if user_ids:
            receipts = receipts.filter(purchaser_id__in=user_ids)
        
        # Apply bbox filter
        receipts = receipts.filter(location__within=bbox_geom)
        
        # Build Loose Products queryset
        loose_products = Product.objects.filter(
            settlement=self.settlement,
            receipt__isnull=True,  # Only loose products
            location__isnull=False
        )
        
        if date_from:
            loose_products = loose_products.filter(created_at__gte=datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            loose_products = loose_products.filter(created_at__lte=datetime.strptime(date_to, '%Y-%m-%d'))
        
        if categories:
            loose_products = loose_products.filter(category__in=categories)
        
        if user_ids:
            loose_products = loose_products.filter(purchaser_id__in=user_ids)
        
        loose_products = loose_products.filter(location__within=bbox_geom)
        
        # Use raw SQL for ST_HexagonGrid aggregation
        heatmap_points = self._aggregate_with_hexagon_grid(
            receipts, loose_products, buffered_bbox, grid_resolution, cell_size,
            date_from=date_from,
            date_to=date_to,
            categories=categories,
            user_ids=user_ids,
        )
        
        # Filter out empty hexagons if requested
        if not show_empty_hexagons:
            heatmap_points = [h for h in heatmap_points if h.get('weight', 0) > 0.01]
            print(f"[DEBUG] Filtered to {len(heatmap_points)} hexagons with data (show_empty_hexagons=False)")
        
        # Cache results for 1 hour (3600 seconds)
        cache.set(cache_key, heatmap_points, 3600)
        print(f"[DEBUG] Cached heatmap results: {len(heatmap_points)} hexagons for 1 hour")
        
        return heatmap_points
    
    def _aggregate_with_hexagon_grid(
        self,
        receipts_qs,
        products_qs,
        bbox: Tuple[float, float, float, float],
        resolution: int,
        cell_size: Optional[float] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        categories: Optional[List[str]] = None,
        user_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        """
        Use PostGIS ST_HexagonGrid to aggregate data into hexagonal cells.
        
        PostGIS 3.1+ provides ST_HexagonGrid function.
        Falls back to ST_SquareGrid if ST_HexagonGrid is not available.
        """
        from django.db import connection
        from django.core.serializers.json import DjangoJSONEncoder
        import json
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # If cell_size not provided, compute from grid_resolution
        if cell_size is None:
            cell_size = 1.0 / (2 ** (resolution - 3))
        
        print(f"[DEBUG] Heatmap aggregation started: bbox={bbox}, resolution={resolution}, cell_size={cell_size}")
        print(f"[DEBUG] Settlement ID: {self.settlement.id}")
        print(f"[DEBUG] Filters: date_from={date_from}, date_to={date_to}, categories={categories}, user_ids={user_ids}")
        
        # Build WHERE clause conditions for receipts and products
        receipt_where_conditions = []
        product_where_conditions = []
        params = [cell_size, min_lon, min_lat, max_lon, max_lat, str(self.settlement.id), str(self.settlement.id)]
        
        # Date filters for receipts
        if date_from:
            receipt_where_conditions.append("r.purchase_date >= %s")
            params.append(date_from)
        if date_to:
            receipt_where_conditions.append("r.purchase_date <= %s")
            params.append(date_to)
        
        # Category filter for receipts
        if categories:
            placeholders = ','.join(['%s'] * len(categories))
            receipt_where_conditions.append(f"r.category IN ({placeholders})")
            params.extend(categories)
        
        # User filter for receipts
        if user_ids:
            placeholders = ','.join(['%s'] * len(user_ids))
            receipt_where_conditions.append(f"r.purchaser_id IN ({placeholders})")
            params.extend(user_ids)
        
        # Date filters for products
        if date_from:
            product_where_conditions.append("p.created_at >= %s")
            params.append(date_from)
        if date_to:
            product_where_conditions.append("p.created_at <= %s")
            params.append(date_to)
        
        # Category filter for products
        if categories:
            placeholders = ','.join(['%s'] * len(categories))
            product_where_conditions.append(f"p.category IN ({placeholders})")
            params.extend(categories)
        
        # User filter for products
        if user_ids:
            placeholders = ','.join(['%s'] * len(user_ids))
            product_where_conditions.append(f"p.purchaser_id IN ({placeholders})")
            params.extend(user_ids)
        
        # Build WHERE clauses
        receipt_where = " AND " + " AND ".join(receipt_where_conditions) if receipt_where_conditions else ""
        product_where = " AND " + " AND ".join(product_where_conditions) if product_where_conditions else ""
        
        # SQL query using ST_HexagonGrid with parameterized queries and filters
        # ST_HexagonGrid returns set of records - need to extract geom column
        sql = f"""
        WITH hex_grid AS (
            SELECT (h).geom 
            FROM ST_HexagonGrid(%s, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) h
        ),
        receipts_data AS (
            SELECT 
                h.geom AS hex_geom,
                SUM(COALESCE(r.total_amount, 0)) AS total_weight,
                COUNT(r.id) AS point_count,
                ST_Centroid(h.geom) AS center
            FROM hex_grid h
            LEFT JOIN receipts_receipt r ON ST_Intersects(r.location::geometry, h.geom) 
                AND r.settlement_id = %s::uuid
                AND r.location IS NOT NULL{receipt_where}
            GROUP BY h.geom
        ),
        products_data AS (
            SELECT 
                h.geom AS hex_geom,
                SUM(COALESCE(p.price, 0)) AS total_weight,
                COUNT(p.id) AS point_count,
                ST_Centroid(h.geom) AS center
            FROM hex_grid h
            LEFT JOIN receipts_product p ON ST_Intersects(p.location::geometry, h.geom)
                AND p.settlement_id = %s::uuid
                AND p.receipt_id IS NULL
                AND p.location IS NOT NULL{product_where}
            GROUP BY h.geom
        ),
        combined AS (
            SELECT 
                hex_geom,
                SUM(total_weight) AS total_weight,
                SUM(point_count) AS total_count,
                center
            FROM (
                SELECT hex_geom, total_weight, point_count, center FROM receipts_data
                UNION ALL
                SELECT hex_geom, total_weight, point_count, center FROM products_data
            ) combined_data
            GROUP BY hex_geom, center
        )
        SELECT 
            MD5(CAST(ST_AsText(hex_geom) AS text)) as hex_id,
            ST_AsGeoJSON(hex_geom) as geometry,
            total_weight,
            ST_X(center) as center_lng,
            ST_Y(center) as center_lat,
            total_count
        FROM combined
        ORDER BY total_weight DESC
        """
        
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                print(f"[DEBUG] SQL query successful. Got {len(results)} hexagon cells.")
            except Exception as e:
                # Fallback to SquareGrid if HexagonGrid not available
                print(f"[DEBUG] ST_HexagonGrid error: {e}. Falling back to SquareGrid.")
                results = self._aggregate_with_square_grid(
                    receipts_qs, products_qs, bbox, resolution
                )
        
        # Convert results to proper format
        heatmap_points = []
        for row in results:
            try:
                geometry = json.loads(row['geometry'])
                weight = float(row['total_weight']) if row['total_weight'] else 0.0
                
                # Get item details for non-empty hexagons
                items = []
                if weight > 0.01:
                    items = self._get_hexagon_items(
                        geometry, 
                        date_from=date_from,
                        date_to=date_to,
                        categories=categories,
                        user_ids=user_ids
                    )
                
                heatmap_points.append({
                    'hexagon_id': row['hex_id'],
                    'geometry': geometry,
                    'weight': weight,
                    'center_lat': float(row['center_lat']),
                    'center_lng': float(row['center_lng']),
                    'point_count': int(row['total_count'] or 0),
                    'items': items,  # Add item details
                })
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error processing heatmap point: {e}")
                continue
        
        return heatmap_points
    
    def _aggregate_with_square_grid(
        self,
        receipts_qs,
        products_qs,
        bbox: Tuple[float, float, float, float],
        resolution: int,
    ) -> List[Dict]:
        """
        Fallback: Use ST_SquareGrid instead of HexagonGrid.
        """
        from django.db import connection
        import json
        
        min_lon, min_lat, max_lon, max_lat = bbox
        cell_size = 1.0 / (2 ** (resolution - 3))
        
        # SQL with parameterized queries
        sql = """
        WITH square_grid AS (
            SELECT (s).geom 
            FROM ST_SquareGrid(%s, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) s
        ),
        data AS (
            SELECT 
                s.geom AS square_geom,
                SUM(COALESCE(r.total_amount, 0)) AS total_weight,
                COUNT(r.id) AS point_count,
                ST_Centroid(s.geom) AS center
            FROM square_grid s
            LEFT JOIN receipts_receipt r ON ST_Intersects(r.location::geometry, s.geom)
                AND r.settlement_id = %s::uuid
                AND r.location IS NOT NULL
            LEFT JOIN receipts_product p ON ST_Intersects(p.location::geometry, s.geom)
                AND p.settlement_id = %s::uuid
                AND p.receipt_id IS NULL
                AND p.location IS NOT NULL
            GROUP BY s.geom
        )
        SELECT 
            MD5(CAST(ST_AsText(square_geom) AS text)) as grid_id,
            ST_AsGeoJSON(square_geom) as geometry,
            total_weight,
            ST_X(center) as center_lng,
            ST_Y(center) as center_lat,
            point_count
        FROM data
        ORDER BY total_weight DESC
        """
        
        params = [
            cell_size,
            min_lon, min_lat, max_lon, max_lat,
            str(self.settlement.id),
            str(self.settlement.id),
        ]
        
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            except Exception as e:
                print(f"ST_SquareGrid error: {e}")
                results = []
        
        heatmap_points = []
        for row in results:
            try:
                geometry = json.loads(row['geometry'])
                weight = float(row['total_weight'])
                
                # Get item details for non-empty cells
                items = []
                if weight > 0.01:
                    items = self._get_hexagon_items(geometry)
                
                heatmap_points.append({
                    'hexagon_id': row['grid_id'],
                    'geometry': geometry,
                    'weight': weight,
                    'center_lat': float(row['center_lat']),
                    'center_lng': float(row['center_lng']),
                    'point_count': int(row['point_count']),
                    'items': items,
                })
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error processing grid point: {e}")
                continue
        
        return heatmap_points
    
    def _get_hexagon_items(
        self,
        geometry: dict,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        categories: Optional[List[str]] = None,
        user_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        """Get detailed items (receipts and products) within a hexagon."""
        from django.db import connection
        import json as json_lib
        
        # Convert GeoJSON polygon to WKT for PostGIS
        coords = geometry.get('coordinates', [[]])[0]
        if not coords:
            return []
        
        # Build WKT polygon
        coord_strs = [f"{lon} {lat}" for lon, lat in coords]
        wkt_polygon = f"POLYGON(({','.join(coord_strs)}))"
        
        # Build query for receipts and products in this hexagon
        sql = """
        WITH hexagon AS (
            SELECT ST_GeomFromText(%s, 4326) AS geom
        ),
        receipts_in_hex AS (
            SELECT 
                'receipt' AS type,
                r.id,
                r.merchant_name AS name,
                r.total_amount AS amount,
                r.category,
                r.purchase_date AS date,
                r.description
            FROM receipts_receipt r, hexagon h
            WHERE ST_Intersects(r.location::geometry, h.geom)
                AND r.settlement_id = %s::uuid
                AND r.location IS NOT NULL
        ),
        products_in_hex AS (
            SELECT 
                'product' AS type,
                p.id,
                p.name,
                p.price AS amount,
                p.category,
                p.created_at AS date,
                p.description
            FROM receipts_product p, hexagon h
            WHERE ST_Intersects(p.location::geometry, h.geom)
                AND p.settlement_id = %s::uuid
                AND p.receipt_id IS NULL
                AND p.location IS NOT NULL
        ),
        combined AS (
            SELECT * FROM receipts_in_hex
            UNION ALL
            SELECT * FROM products_in_hex
        )
        SELECT type, id, name, amount, category, date, description
        FROM combined
        ORDER BY date DESC
        LIMIT 10
        """
        
        params = [wkt_polygon, str(self.settlement.id), str(self.settlement.id)]
        
        items = []
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                for row in rows:
                    item = dict(zip(columns, row))
                    items.append({
                        'type': item['type'],
                        'id': str(item['id']),
                        'name': item['name'],
                        'amount': float(item['amount']) if item['amount'] else 0.0,
                        'category': item['category'],
                        'date': str(item['date']) if item['date'] else '',
                        'description': item['description'],
                    })
        except Exception as e:
            print(f"Error getting hexagon items: {e}")
        
        return items
    
    def _generate_cache_key(
        self,
        bbox: Tuple[float, float, float, float],
        grid_resolution: int,
        date_from: Optional[str],
        date_to: Optional[str],
        categories: Optional[List[str]],
        user_ids: Optional[List[int]],
        bbox_buffer_percent: float,
        cell_size: Optional[float],
    ) -> str:
        """Generate cache key from heatmap parameters."""
        # Create a deterministic string from all parameters
        key_parts = [
            str(self.settlement.id),
            f"bbox_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}",
            f"res_{grid_resolution}",
            f"date_{date_from}_{date_to}",
            f"cats_{'_'.join(sorted(categories or []))}",
            f"users_{'_'.join(map(str, sorted(user_ids or [])))}",
            f"buf_{bbox_buffer_percent}",
            f"cellsize_{cell_size}",
        ]
        
        key_str = "|".join(key_parts)
        # Hash to keep key length reasonable
        cache_key = f"heatmap:{hashlib.md5(key_str.encode()).hexdigest()}"
        return cache_key
