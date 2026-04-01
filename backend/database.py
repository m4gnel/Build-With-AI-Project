"""
database.py — SQLite Database Setup & Management
=================================================
Creates and manages the SQLite database with tables for:
- demand_history: Historical product demand data
- suppliers: Supplier information with risk factors
- warehouses: Warehouse/node locations for routing
- routes: Connections between warehouses
- risk_events: Logged risk events and disruptions
- decisions: AI-generated decision log
"""

import sqlite3
import os

# Database file path (same directory as this script)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supply_chain.db")


def get_connection():
    """Get a database connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
    return conn


def init_db():
    """Initialize the database with all required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Demand History Table ──────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demand_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            demand INTEGER NOT NULL,
            region TEXT DEFAULT 'Global',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Suppliers Table ───────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            delivery_time_days REAL NOT NULL,
            failure_rate REAL NOT NULL,
            cost_score REAL NOT NULL,
            quality_score REAL NOT NULL,
            reliability_score REAL NOT NULL,
            cluster_label TEXT DEFAULT 'Unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Warehouses Table ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            capacity INTEGER DEFAULT 1000,
            current_stock INTEGER DEFAULT 500
        )
    """)

    # ── Routes Table (edges in the graph) ─────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            dest_id INTEGER NOT NULL,
            distance_km REAL NOT NULL,
            travel_time_hours REAL NOT NULL,
            cost REAL NOT NULL,
            risk_factor REAL DEFAULT 0.0,
            FOREIGN KEY (source_id) REFERENCES warehouses(id),
            FOREIGN KEY (dest_id) REFERENCES warehouses(id)
        )
    """)

    # ── Risk Events Table ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            location TEXT,
            description TEXT,
            risk_score REAL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Decisions Log Table ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            justification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


def reset_db():
    """Drop all tables and reinitialize (for development)."""
    conn = get_connection()
    cursor = conn.cursor()
    tables = ["demand_history", "suppliers", "warehouses", "routes", "risk_events", "decisions"]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()
    init_db()
    print("✅ Database reset complete!")


if __name__ == "__main__":
    init_db()
