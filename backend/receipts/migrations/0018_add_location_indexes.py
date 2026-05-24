# Generated migration for adding performance indexes

from django.db import migrations, models
from django.contrib.gis.db import models as gis_models


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0017_debtsettlement'),
    ]

    operations = [
        # GIST indexes for location fields (for spatial queries)
        migrations.RunSQL(
            sql="CREATE INDEX idx_receipt_location_gist ON receipts_receipt USING GIST(location);",
            reverse_sql="DROP INDEX IF EXISTS idx_receipt_location_gist;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX idx_product_location_gist ON receipts_product USING GIST(location);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_location_gist;",
        ),
        # Regular indexes for foreign keys and filters
        migrations.RunSQL(
            sql="CREATE INDEX idx_receipt_settlement_id ON receipts_receipt(settlement_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_receipt_settlement_id;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX idx_product_settlement_id ON receipts_product(settlement_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_settlement_id;",
        ),
        # Indexes for common filters
        migrations.RunSQL(
            sql="CREATE INDEX idx_receipt_category ON receipts_receipt(category);",
            reverse_sql="DROP INDEX IF EXISTS idx_receipt_category;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX idx_receipt_purchase_date ON receipts_receipt(purchase_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_receipt_purchase_date;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX idx_product_category ON receipts_product(category);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_category;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX idx_product_created_at ON receipts_product(created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_created_at;",
        ),
        # Composite indexes for common filter combinations
        migrations.RunSQL(
            sql="CREATE INDEX idx_receipt_settlement_category ON receipts_receipt(settlement_id, category);",
            reverse_sql="DROP INDEX IF EXISTS idx_receipt_settlement_category;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX idx_product_settlement_receipt ON receipts_product(settlement_id, receipt_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_settlement_receipt;",
        ),
    ]
