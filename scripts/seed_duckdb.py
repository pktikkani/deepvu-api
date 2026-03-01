"""Seed DuckDB with realistic ad analytics dummy data for the Dev Tenant (ADV001)."""

import duckdb

DB_PATH = "data/analytics.duckdb"
ADVERTISER_ID = "ADV001"

conn = duckdb.connect(DB_PATH)

# ──────────────────────────────────────────────
# 1. Campaign Overview — campaign_metrics
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS campaign_metrics")
conn.execute("""
    CREATE TABLE campaign_metrics (
        advertiser_id VARCHAR,
        campaign VARCHAR,
        sub_campaign VARCHAR,
        plan_line_item VARCHAR,
        channel VARCHAR,
        currency VARCHAR,
        spends DOUBLE,
        impressions BIGINT,
        clicks BIGINT,
        ctr DOUBLE,
        views BIGINT,
        vtr DOUBLE,
        conversions BIGINT,
        cpm DOUBLE,
        cpc DOUBLE
    )
""")

campaigns = [
    ("Spring Sale 2026", "Brand Awareness", "Display - Premium", "Display", "USD", 12500.00, 850000, 4250, 0.50, 42500, 5.00, 320, 14.71, 2.94),
    ("Spring Sale 2026", "Brand Awareness", "Video - YouTube", "Video", "USD", 18200.00, 620000, 3100, 0.50, 186000, 30.00, 540, 29.35, 5.87),
    ("Spring Sale 2026", "Retargeting", "Display - Retarget", "Display", "USD", 8900.00, 420000, 6300, 1.50, 21000, 5.00, 890, 21.19, 1.41),
    ("Spring Sale 2026", "Retargeting", "Video - Social", "Video", "USD", 6500.00, 310000, 4650, 1.50, 93000, 30.00, 420, 20.97, 1.40),
    ("Summer Campaign", "Prospecting", "Display - Broad", "Display", "USD", 15800.00, 1200000, 6000, 0.50, 60000, 5.00, 450, 13.17, 2.63),
    ("Summer Campaign", "Prospecting", "Video - CTV", "Video", "USD", 22000.00, 440000, 2200, 0.50, 352000, 80.00, 280, 50.00, 10.00),
    ("Summer Campaign", "Performance", "Search - Brand", "Search", "USD", 9200.00, 180000, 14400, 8.00, 0, 0.00, 1920, 51.11, 0.64),
    ("Summer Campaign", "Performance", "Search - Generic", "Search", "USD", 11500.00, 230000, 11500, 5.00, 0, 0.00, 1150, 50.00, 1.00),
    ("Fall Push", "Awareness", "Display - Native", "Display", "USD", 7800.00, 560000, 3360, 0.60, 28000, 5.00, 224, 13.93, 2.32),
    ("Fall Push", "Awareness", "Video - Pre-roll", "Video", "USD", 14200.00, 480000, 2400, 0.50, 192000, 40.00, 360, 29.58, 5.92),
    ("Fall Push", "Conversion", "Display - DCO", "Display", "USD", 10300.00, 720000, 10800, 1.50, 36000, 5.00, 1620, 14.31, 0.95),
    ("Fall Push", "Conversion", "Social - Feed", "Social", "USD", 8400.00, 380000, 7600, 2.00, 114000, 30.00, 1140, 22.11, 1.11),
]

for c in campaigns:
    conn.execute(
        "INSERT INTO campaign_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, *c],
    )

# Also insert a few rows for a second advertiser (to verify RLS blocks them)
for c in campaigns[:3]:
    conn.execute(
        "INSERT INTO campaign_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ["ADV_OTHER", *c],
    )

# ──────────────────────────────────────────────
# 2. YouTube metrics (Campaign Overview → YouTube sub-tab)
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS youtube_metrics")
conn.execute("""
    CREATE TABLE youtube_metrics (
        advertiser_id VARCHAR,
        campaign VARCHAR,
        sub_campaign VARCHAR,
        plan_line_item VARCHAR,
        currency VARCHAR,
        spends DOUBLE,
        impressions BIGINT,
        views BIGINT,
        vtr DOUBLE,
        clicks BIGINT,
        ctr DOUBLE,
        earned_views BIGINT,
        earned_subscribers BIGINT
    )
""")

yt_data = [
    ("Spring Sale 2026", "Brand Awareness", "Video - YouTube", "USD", 18200.00, 620000, 186000, 30.00, 3100, 0.50, 12400, 320),
    ("Summer Campaign", "Prospecting", "Video - CTV", "USD", 22000.00, 440000, 352000, 80.00, 2200, 0.50, 18600, 480),
    ("Fall Push", "Awareness", "Video - Pre-roll", "USD", 14200.00, 480000, 192000, 40.00, 2400, 0.50, 9600, 240),
]

for yt in yt_data:
    conn.execute(
        "INSERT INTO youtube_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, *yt],
    )

# ──────────────────────────────────────────────
# 3. Reach & Frequency
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS reach_frequency")
conn.execute("""
    CREATE TABLE reach_frequency (
        advertiser_id VARCHAR,
        sub_campaign VARCHAR,
        plan_line_item VARCHAR,
        frequency INTEGER,
        reach BIGINT,
        impressions BIGINT,
        currency VARCHAR,
        spends DOUBLE
    )
""")

rf_data = [
    ("Brand Awareness", "Display - Premium", 1, 420000, 420000, "USD", 6200.00),
    ("Brand Awareness", "Display - Premium", 2, 180000, 360000, "USD", 3800.00),
    ("Brand Awareness", "Display - Premium", 3, 45000, 135000, "USD", 1500.00),
    ("Brand Awareness", "Display - Premium", 4, 12000, 48000, "USD", 600.00),
    ("Brand Awareness", "Display - Premium", 5, 5000, 25000, "USD", 400.00),
    ("Brand Awareness", "Video - YouTube", 1, 310000, 310000, "USD", 9100.00),
    ("Brand Awareness", "Video - YouTube", 2, 140000, 280000, "USD", 5600.00),
    ("Brand Awareness", "Video - YouTube", 3, 35000, 105000, "USD", 2100.00),
    ("Brand Awareness", "Video - YouTube", 4, 8000, 32000, "USD", 900.00),
    ("Retargeting", "Display - Retarget", 1, 180000, 180000, "USD", 3600.00),
    ("Retargeting", "Display - Retarget", 2, 95000, 190000, "USD", 2800.00),
    ("Retargeting", "Display - Retarget", 3, 40000, 120000, "USD", 1500.00),
    ("Retargeting", "Display - Retarget", 4, 15000, 60000, "USD", 700.00),
    ("Retargeting", "Video - Social", 1, 155000, 155000, "USD", 3250.00),
    ("Retargeting", "Video - Social", 2, 70000, 140000, "USD", 2100.00),
    ("Retargeting", "Video - Social", 3, 18000, 54000, "USD", 750.00),
    ("Prospecting", "Display - Broad", 1, 600000, 600000, "USD", 7900.00),
    ("Prospecting", "Display - Broad", 2, 250000, 500000, "USD", 4800.00),
    ("Prospecting", "Display - Broad", 3, 65000, 195000, "USD", 1900.00),
    ("Prospecting", "Display - Broad", 4, 18000, 72000, "USD", 800.00),
    ("Prospecting", "Video - CTV", 1, 220000, 220000, "USD", 11000.00),
    ("Prospecting", "Video - CTV", 2, 100000, 200000, "USD", 7000.00),
    ("Prospecting", "Video - CTV", 3, 25000, 75000, "USD", 2500.00),
]

for rf in rf_data:
    conn.execute(
        "INSERT INTO reach_frequency VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, *rf],
    )

# ──────────────────────────────────────────────
# 4. Device Type metrics
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS device_metrics")
conn.execute("""
    CREATE TABLE device_metrics (
        advertiser_id VARCHAR,
        sub_campaign VARCHAR,
        plan_line_item VARCHAR,
        device_type VARCHAR,
        currency VARCHAR,
        spends DOUBLE,
        impressions BIGINT,
        clicks BIGINT,
        ctr DOUBLE,
        views BIGINT,
        vtr DOUBLE
    )
""")

devices = ["Desktop", "Mobile", "Tablet", "Connected TV", "Smart TV"]
sub_campaigns = [
    ("Brand Awareness", "Display - Premium"),
    ("Brand Awareness", "Video - YouTube"),
    ("Retargeting", "Display - Retarget"),
    ("Prospecting", "Display - Broad"),
    ("Prospecting", "Video - CTV"),
]

import random
random.seed(42)

for sc, pli in sub_campaigns:
    for dev in devices:
        # Weight distribution by device
        if dev == "Mobile":
            weight = 0.45
        elif dev == "Desktop":
            weight = 0.30
        elif dev == "Tablet":
            weight = 0.10
        elif dev == "Connected TV":
            weight = 0.10
        else:
            weight = 0.05

        base_spends = random.uniform(800, 4000) * weight
        base_imps = int(random.uniform(50000, 200000) * weight)
        base_clicks = int(base_imps * random.uniform(0.003, 0.02))
        ctr = round(base_clicks / base_imps * 100, 2) if base_imps > 0 else 0
        base_views = int(base_imps * random.uniform(0.1, 0.4)) if "Video" in pli else int(base_imps * 0.05)
        vtr = round(base_views / base_imps * 100, 2) if base_imps > 0 else 0

        conn.execute(
            "INSERT INTO device_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [ADVERTISER_ID, sc, pli, dev, "USD", round(base_spends, 2), base_imps, base_clicks, ctr, base_views, vtr],
        )

# ──────────────────────────────────────────────
# 5. Geo Trends — Region
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS geo_region_metrics")
conn.execute("""
    CREATE TABLE geo_region_metrics (
        advertiser_id VARCHAR,
        sub_campaign VARCHAR,
        plan_line_item VARCHAR,
        region VARCHAR,
        currency VARCHAR,
        spends DOUBLE,
        impressions BIGINT,
        cpm DOUBLE
    )
""")

regions = [
    ("California", 18500.00, 1250000),
    ("New York", 15200.00, 980000),
    ("Texas", 12800.00, 920000),
    ("Florida", 10500.00, 780000),
    ("Illinois", 8200.00, 620000),
    ("Pennsylvania", 6800.00, 520000),
    ("Ohio", 5400.00, 430000),
    ("Georgia", 4800.00, 380000),
    ("North Carolina", 4200.00, 340000),
    ("Michigan", 3600.00, 290000),
    ("New Jersey", 3200.00, 260000),
    ("Virginia", 2800.00, 230000),
    ("Washington", 2500.00, 210000),
    ("Arizona", 2200.00, 180000),
    ("Massachusetts", 2000.00, 170000),
]

for reg, spends, imps in regions:
    cpm = round(spends / imps * 1000, 2)
    conn.execute(
        "INSERT INTO geo_region_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, "Brand Awareness", "Display - Premium", reg, "USD", spends, imps, cpm],
    )
    # Add more sub_campaign data
    conn.execute(
        "INSERT INTO geo_region_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, "Retargeting", "Display - Retarget", reg, "USD", round(spends * 0.6, 2), int(imps * 0.5), round(spends * 0.6 / (imps * 0.5) * 1000, 2)],
    )

# ──────────────────────────────────────────────
# 6. Geo Trends — City
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS geo_city_metrics")
conn.execute("""
    CREATE TABLE geo_city_metrics (
        advertiser_id VARCHAR,
        sub_campaign VARCHAR,
        plan_line_item VARCHAR,
        city VARCHAR,
        currency VARCHAR,
        spends DOUBLE,
        impressions BIGINT,
        cpm DOUBLE
    )
""")

cities = [
    ("Los Angeles", 8200.00, 520000),
    ("New York City", 7800.00, 480000),
    ("Chicago", 5400.00, 380000),
    ("Houston", 4600.00, 340000),
    ("Phoenix", 3800.00, 280000),
    ("Philadelphia", 3200.00, 250000),
    ("San Antonio", 2800.00, 220000),
    ("San Diego", 2500.00, 200000),
    ("Dallas", 2200.00, 180000),
    ("San Jose", 2000.00, 160000),
    ("Austin", 1800.00, 150000),
    ("Jacksonville", 1500.00, 130000),
    ("San Francisco", 1400.00, 110000),
    ("Columbus", 1200.00, 100000),
    ("Indianapolis", 1100.00, 95000),
    ("Charlotte", 1000.00, 85000),
    ("Seattle", 950.00, 80000),
    ("Denver", 900.00, 75000),
    ("Boston", 850.00, 70000),
    ("Nashville", 800.00, 65000),
]

for city, spends, imps in cities:
    cpm = round(spends / imps * 1000, 2)
    conn.execute(
        "INSERT INTO geo_city_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, "Brand Awareness", "Display - Premium", city, "USD", spends, imps, cpm],
    )
    conn.execute(
        "INSERT INTO geo_city_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, "Retargeting", "Display - Retarget", city, "USD", round(spends * 0.5, 2), int(imps * 0.4), round(spends * 0.5 / (imps * 0.4) * 1000, 2)],
    )

# ──────────────────────────────────────────────
# 7. Placements
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS placement_metrics")
conn.execute("""
    CREATE TABLE placement_metrics (
        advertiser_id VARCHAR,
        placement VARCHAR,
        currency VARCHAR,
        spends DOUBLE,
        impressions BIGINT,
        clicks BIGINT,
        ctr DOUBLE,
        views BIGINT,
        vtr DOUBLE,
        cpm DOUBLE
    )
""")

placements = [
    ("YouTube - In-Stream", "USD", 22000.00, 820000, 4100, 0.50, 328000, 40.00, 26.83),
    ("Google Display Network", "USD", 18500.00, 1450000, 8700, 0.60, 72500, 5.00, 12.76),
    ("Facebook Feed", "USD", 12800.00, 640000, 9600, 1.50, 192000, 30.00, 20.00),
    ("Instagram Stories", "USD", 8400.00, 420000, 6300, 1.50, 126000, 30.00, 20.00),
    ("TikTok For You", "USD", 6200.00, 310000, 4650, 1.50, 93000, 30.00, 20.00),
    ("Programmatic - Premium", "USD", 15200.00, 950000, 4750, 0.50, 47500, 5.00, 16.00),
    ("Programmatic - Standard", "USD", 9800.00, 1200000, 6000, 0.50, 60000, 5.00, 8.17),
    ("Native - Content", "USD", 5600.00, 380000, 3800, 1.00, 19000, 5.00, 14.74),
    ("Connected TV", "USD", 14000.00, 280000, 1400, 0.50, 224000, 80.00, 50.00),
    ("Audio - Spotify", "USD", 3200.00, 160000, 800, 0.50, 128000, 80.00, 20.00),
]

for pl in placements:
    conn.execute(
        "INSERT INTO placement_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, *pl],
    )

# ──────────────────────────────────────────────
# 8. Creative Performance
# ──────────────────────────────────────────────
conn.execute("DROP TABLE IF EXISTS creative_metrics")
conn.execute("""
    CREATE TABLE creative_metrics (
        advertiser_id VARCHAR,
        sub_campaign VARCHAR,
        plan_line_item VARCHAR,
        creative VARCHAR,
        creative_name VARCHAR,
        format VARCHAR,
        concept VARCHAR,
        size VARCHAR,
        currency VARCHAR,
        spends DOUBLE,
        impressions BIGINT,
        cpm DOUBLE,
        clicks BIGINT,
        ctr DOUBLE
    )
""")

creatives = [
    ("Brand Awareness", "Display - Premium", "CR-001", "Spring Sale Banner A", "Display Banner", "Lifestyle", "300x250", "USD", 3200.00, 220000, 14.55, 1100, 0.50),
    ("Brand Awareness", "Display - Premium", "CR-002", "Spring Sale Banner B", "Display Banner", "Product", "728x90", "USD", 2800.00, 190000, 14.74, 950, 0.50),
    ("Brand Awareness", "Display - Premium", "CR-003", "Spring Sale Skyscraper", "Display Banner", "Lifestyle", "160x600", "USD", 1500.00, 105000, 14.29, 525, 0.50),
    ("Brand Awareness", "Video - YouTube", "CR-004", "Brand Story 30s", "Video Ad", "Brand Story", "1920x1080", "USD", 8500.00, 290000, 29.31, 1450, 0.50),
    ("Brand Awareness", "Video - YouTube", "CR-005", "Product Demo 15s", "Video Ad", "Product Demo", "1920x1080", "USD", 5200.00, 180000, 28.89, 900, 0.50),
    ("Brand Awareness", "Video - YouTube", "CR-006", "Bumper Ad 6s", "Bumper", "Brand Recall", "1920x1080", "USD", 4500.00, 150000, 30.00, 750, 0.50),
    ("Retargeting", "Display - Retarget", "CR-007", "Cart Reminder A", "Display Banner", "Retarget", "300x250", "USD", 3800.00, 180000, 21.11, 2700, 1.50),
    ("Retargeting", "Display - Retarget", "CR-008", "Cart Reminder B", "Display Banner", "Retarget", "300x600", "USD", 2900.00, 140000, 20.71, 2100, 1.50),
    ("Retargeting", "Display - Retarget", "CR-009", "Browse Abandonment", "Display Banner", "Retarget", "728x90", "USD", 2200.00, 100000, 22.00, 1500, 1.50),
    ("Retargeting", "Video - Social", "CR-010", "Social Retarget 15s", "Video Ad", "Social Proof", "1080x1080", "USD", 3500.00, 170000, 20.59, 2550, 1.50),
    ("Retargeting", "Video - Social", "CR-011", "UGC Retarget", "Video Ad", "UGC", "1080x1920", "USD", 3000.00, 140000, 21.43, 2100, 1.50),
    ("Prospecting", "Display - Broad", "CR-012", "Summer Collection A", "Display Banner", "Seasonal", "300x250", "USD", 5200.00, 400000, 13.00, 2000, 0.50),
    ("Prospecting", "Display - Broad", "CR-013", "Summer Collection B", "Display Banner", "Seasonal", "728x90", "USD", 4800.00, 360000, 13.33, 1800, 0.50),
    ("Prospecting", "Display - Broad", "CR-014", "Summer Native", "Native Ad", "Seasonal", "1200x627", "USD", 5800.00, 440000, 13.18, 2200, 0.50),
    ("Prospecting", "Video - CTV", "CR-015", "CTV Brand Film 30s", "CTV Ad", "Brand Film", "1920x1080", "USD", 12000.00, 240000, 50.00, 1200, 0.50),
    ("Prospecting", "Video - CTV", "CR-016", "CTV Product Spot 15s", "CTV Ad", "Product Spot", "1920x1080", "USD", 10000.00, 200000, 50.00, 1000, 0.50),
]

for cr in creatives:
    conn.execute(
        "INSERT INTO creative_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [ADVERTISER_ID, *cr],
    )

# ──────────────────────────────────────────────
# Verify
# ──────────────────────────────────────────────
tables = conn.execute("SHOW TABLES").fetchall()
print("Tables created:")
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"  {t[0]}: {count} rows")

conn.close()
print(f"\nDuckDB database saved to: {DB_PATH}")
