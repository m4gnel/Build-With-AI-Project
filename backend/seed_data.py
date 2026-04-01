"""
seed_data.py — Realistic Indian Supply Chain Demand Generator
=============================================================
Generates highly realistic supply chain simulation data with:
- India-specific festival demand spikes (Diwali, Navratri, Eid, Christmas)
- Monsoon season impacts on logistics demand
- Product-specific seasonality and demand curves
- Q1/Q4 Indian fiscal year effects
- Supply disruption simulation events
"""

import sqlite3
import os
import random
import math
from datetime import datetime, timedelta
from database import get_connection, init_db, reset_db


# ── Indian Festival Calendar (fixed/approximate) ──────────────────────────────
FESTIVAL_PEAKS = {
    # (month, day): multiplier
    (10, 20): 1.95,  # Diwali window start
    (10, 21): 2.10,  # Diwali
    (10, 22): 2.20,  # Diwali peak
    (10, 23): 2.05,  # day after
    (10, 24): 1.80,
    (10, 5):  1.55,  # Navratri
    (10, 6):  1.60,
    (10, 7):  1.55,
    (4, 14):  1.45,  # Baisakhi / Tamil New Year
    (3, 25):  1.50,  # Holi pre-spike
    (3, 26):  1.70,  # Holi
    (3, 27):  1.40,
    (8, 15):  1.60,  # Independence Day
    (12, 24): 1.75,  # Christmas Eve
    (12, 25): 1.80,  # Christmas
    (12, 31): 1.85,  # New Year Eve
    (1, 1):   1.70,  # New Year
    (1, 14):  1.45,  # Makar Sankranti / Pongal
    (9, 7):   1.55,  # Ganesh Chaturthi
    (9, 8):   1.65,
    (9, 9):   1.60,
}

# Hindu fiscal year Q4 (Jan–Mar) and pre-Diwali quarter (Oct) boost
def fiscal_multiplier(date: datetime) -> float:
    m = date.month
    if m in (1, 2, 3):    return 1.15  # Q4 India fiscal close surge
    if m in (10, 11):     return 1.20  # Festive quarter
    if m in (6, 7, 8, 9): return 0.90  # Monsoon slowdown
    return 1.0

# Monsoon logistics disruption (demand dip June–Sept)
def monsoon_factor(date: datetime) -> float:
    m = date.month
    if m == 6:  return 0.88
    if m == 7:  return 0.82
    if m == 8:  return 0.85
    if m == 9:  return 0.92
    return 1.0

def seed_demand_history(cursor):
    """Generate 12 months of highly realistic daily demand data for 5 product categories."""
    products = [
        ("ELEC001", "Consumer Electronics",   750,  100),   # base, variance
        ("PHRM002", "Pharmaceutical Supplies", 580,   60),
        ("TXTL003", "Textile & Apparel",       620,   85),
        ("AUTO004", "Auto & Industrial Parts",  490,   70),
        ("FOOD005", "Food & FMCG",             820,   90),
    ]

    start_date = datetime(2025, 4, 1)
    days = 365
    records = []

    for day_offset in range(days):
        d = start_date + timedelta(days=day_offset)
        date_str = d.strftime("%Y-%m-%d")

        for prod_id, prod_name, base_demand, variance in products:
            # Long-term upward trend
            trend = day_offset * 0.08

            # Seasonal sine wave (annual cycle)
            seasonal = variance * 0.4 * math.sin(2 * math.pi * day_offset / 365 - 1.0)

            # Weekly rhythm — weekends lower
            dow = d.weekday()
            weekly = -base_demand * 0.12 if dow >= 5 else base_demand * 0.04

            # Festival spikes
            fest_mult = FESTIVAL_PEAKS.get((d.month, d.day), 1.0)

            # Fiscal & monsoon effects
            fiscal = fiscal_multiplier(d)
            monsoon = monsoon_factor(d)

            # Product-specific modifiers
            if prod_id == "ELEC001":
                # Electronics spikes heavily during Diwali and year-end
                if d.month in (10, 11, 12): fiscal *= 1.18
            elif prod_id == "TXTL003":
                # Textiles spike during festivals and winters (Nov–Jan)
                if d.month in (11, 12, 1): fiscal *= 1.15
                if d.month in (3, 4): fiscal *= 1.10  # Summer fashion
            elif prod_id == "FOOD005":
                # FMCG less affected by monsoon
                monsoon = max(monsoon, 0.95)

            # Gaussian noise
            noise = random.gauss(0, variance * 0.15)

            raw = (base_demand + trend + seasonal + weekly + noise) * fiscal * monsoon * fest_mult
            demand = max(100, round(raw))

            # Distribute demand specifically per major warehouse city to enable route-based filtering
            cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Lucknow"]

            for city in cities:
                city_variance = random.uniform(0.8, 1.2)  # vary slightly per city
                city_demand = max(10, round((demand / len(cities)) * city_variance))
                records.append((date_str, prod_id, prod_name, city_demand, city))

    cursor.executemany(
        "INSERT INTO demand_history (date, product_id, product_name, demand, region) VALUES (?, ?, ?, ?, ?)",
        records
    )
    print(f"  📊 Inserted {len(records)} realistic demand records")


def seed_suppliers(cursor):
    """Generate 20 suppliers across India with realistic risk profiles."""
    suppliers = [
        # Low risk — large, reliable enterprises
        ("TechCorp India",     "Mumbai",    19.076, 72.8777, 2.5, 0.02, 7.5, 9.2, 9.5),
        ("SteelWorks Ltd",     "Jamshedpur",22.804, 86.202,  3.0, 0.03, 6.8, 9.0, 9.0),
        ("MediSupply Co",      "Hyderabad", 17.385, 78.487,  2.0, 0.01, 8.0, 9.5, 9.8),
        ("Premium Parts Inc",  "Pune",      18.520, 73.856,  2.8, 0.02, 7.2, 9.1, 9.3),
        ("QualityFirst Ltd",   "Bangalore", 12.971, 77.594,  2.2, 0.015,7.8, 9.4, 9.6),
        ("ReliableGoods Co",   "Chennai",   13.082, 80.270,  2.6, 0.025,7.0, 9.0, 9.2),
        ("TopTier Supplies",   "Delhi",     28.704, 77.102,  3.2, 0.030,6.5, 8.8, 8.9),
        # Medium risk — regional mid-tier
        ("BudgetMaterials",    "Kolkata",   22.572, 88.363,  5.0, 0.08, 5.0, 7.0, 7.2),
        ("QuickShip Ltd",      "Ahmedabad", 23.022, 72.571,  4.5, 0.10, 5.5, 7.5, 6.8),
        ("ValueParts Co",      "Lucknow",   26.846, 80.946,  4.8, 0.09, 4.8, 6.8, 7.0),
        ("CostSaver Inc",      "Nagpur",    21.145, 79.088,  5.2, 0.07, 4.5, 7.2, 7.5),
        ("MidRange Supply",    "Indore",    22.719, 75.857,  4.2, 0.085,5.2, 7.0, 7.0),
        ("StandardParts",      "Bhopal",    23.259, 77.412,  4.6, 0.095,5.0, 6.5, 6.8),
        ("EconoShip Co",       "Jaipur",    26.912, 75.787,  5.5, 0.11, 4.2, 6.0, 6.5),
        # High risk — small/unreliable vendors
        ("CheapGoods Ltd",     "Kanpur",    26.449, 80.331,  8.0, 0.20, 3.0, 4.5, 4.0),
        ("DiscountAll Co",     "Patna",     25.609, 85.137,  9.5, 0.25, 2.5, 3.8, 3.5),
        ("BargainBin Inc",     "Varanasi",  25.317, 82.973,  7.5, 0.18, 3.5, 5.0, 4.5),
        ("LastResort Ltd",     "Ranchi",    23.344, 85.309, 10.0, 0.30, 2.0, 3.0, 3.0),
        ("RiskyShip Co",       "Guwahati",  26.144, 91.736,  8.5, 0.22, 2.8, 4.0, 3.8),
        ("UnstableSupply",     "Srinagar",  34.083, 74.797, 11.0, 0.35, 1.8, 2.5, 2.5),
    ]
    cursor.executemany(
        """INSERT INTO suppliers (name, location, lat, lng, delivery_time_days,
           failure_rate, cost_score, quality_score, reliability_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        suppliers
    )
    print(f"  🏭 Inserted {len(suppliers)} suppliers")


def seed_warehouses(cursor):
    warehouses = [
        ("WH-Mumbai",    "Mumbai",    19.076, 72.877, 5000, 3200),
        ("WH-Delhi",     "Delhi",     28.704, 77.102, 8000, 5500),
        ("WH-Bangalore", "Bangalore", 12.971, 77.594, 4000, 2800),
        ("WH-Chennai",   "Chennai",   13.082, 80.270, 3500, 2100),
        ("WH-Kolkata",   "Kolkata",   22.572, 88.363, 4500, 3000),
        ("WH-Hyderabad", "Hyderabad", 17.385, 78.487, 3800, 2500),
        ("WH-Ahmedabad", "Ahmedabad", 23.022, 72.571, 3000, 1800),
        ("WH-Pune",      "Pune",      18.520, 73.856, 3200, 2200),
        ("WH-Jaipur",    "Jaipur",    26.912, 75.787, 2500, 1500),
        ("WH-Lucknow",   "Lucknow",   26.847, 80.946, 2800, 1900),
    ]
    cursor.executemany(
        "INSERT INTO warehouses (name, city, lat, lng, capacity, current_stock) VALUES (?, ?, ?, ?, ?, ?)",
        warehouses
    )
    print(f"  🏢 Inserted {len(warehouses)} warehouses")


def seed_routes(cursor):
    routes = [
        (1, 2, 1400, 24, 15000, 0.10),
        (1, 3,  980, 18, 10000, 0.05),
        (1, 6,  710, 12,  8000, 0.08),
        (1, 8,  150,  3,  2000, 0.02),
        (1, 7,  530,  9,  6000, 0.06),
        (2, 9,  270,  5,  3000, 0.04),
        (2, 10, 500,  8,  5500, 0.07),
        (2, 5, 1500, 26, 16000, 0.15),
        (2, 7,  950, 16, 10500, 0.09),
        (3, 4,  350,  6,  4000, 0.03),
        (3, 6,  570, 10,  6500, 0.05),
        (4, 6,  630, 11,  7000, 0.06),
        (4, 5, 1660, 28, 18000, 0.18),
        (5, 10,1000, 17, 11000, 0.12),
        (6, 8,  560, 10,  6000, 0.05),
        (7, 9,  670, 11,  7500, 0.07),
        (9, 10, 580, 10,  6500, 0.08),
        # Reverse edges
        (2, 1, 1400, 24, 15000, 0.10),
        (3, 1,  980, 18, 10000, 0.05),
        (6, 1,  710, 12,  8000, 0.08),
        (8, 1,  150,  3,  2000, 0.02),
        (7, 1,  530,  9,  6000, 0.06),
        (9, 2,  270,  5,  3000, 0.04),
        (10,2,  500,  8,  5500, 0.07),
        (5, 2, 1500, 26, 16000, 0.15),
        (7, 2,  950, 16, 10500, 0.09),
        (4, 3,  350,  6,  4000, 0.03),
        (6, 3,  570, 10,  6500, 0.05),
        (6, 4,  630, 11,  7000, 0.06),
        (5, 4, 1660, 28, 18000, 0.18),
        (10,5, 1000, 17, 11000, 0.12),
        (8, 6,  560, 10,  6000, 0.05),
        (9, 7,  670, 11,  7500, 0.07),
        (10,9,  580, 10,  6500, 0.08),
    ]
    cursor.executemany(
        "INSERT INTO routes (source_id, dest_id, distance_km, travel_time_hours, cost, risk_factor) VALUES (?, ?, ?, ?, ?, ?)",
        routes
    )
    print(f"  🛣️  Inserted {len(routes)} route connections")


def seed_risk_events(cursor):
    events = [
        ("weather",        "high",     "Mumbai",    "Heavy monsoon rainfall causing flooding in Mumbai port area", 78.5),
        ("traffic",        "medium",   "Delhi",     "Highway construction delays on NH-48 corridor",               55.0),
        ("supplier",       "critical", "Kanpur",    "Major supplier CheapGoods Ltd reported manufacturing halt",   92.0),
        ("weather",        "medium",   "Chennai",   "Cyclone warning issued for Bay of Bengal coastal region",     65.0),
        ("political",      "low",      "Kolkata",   "Minor transportation strike affecting local deliveries",      35.0),
        ("weather",        "high",     "Ahmedabad", "Extreme heat wave affecting warehouse cooling systems",       72.0),
        ("supplier",       "medium",   "Patna",     "Quality issues reported from DiscountAll Co shipments",       58.0),
        ("infrastructure", "high",     "Lucknow",   "Bridge collapse on key supply route causing major detour",    85.0),
    ]
    cursor.executemany(
        "INSERT INTO risk_events (event_type, severity, location, description, risk_score) VALUES (?, ?, ?, ?, ?)",
        events
    )
    print(f"  ⚠️  Inserted {len(events)} risk events")


def seed_all():
    print("\n🌱 Seeding database with realistic Indian supply chain data...\n")
    reset_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        seed_demand_history(cursor)
        seed_suppliers(cursor)
        seed_warehouses(cursor)
        seed_routes(cursor)
        seed_risk_events(cursor)
        conn.commit()
        print("\n✅ All data seeded successfully!")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_all()
