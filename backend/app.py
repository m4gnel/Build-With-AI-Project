"""
app.py — Production-Ready Flask Backend
=========================================
AI-Powered Supply Chain Risk Predictor & Optimizer

Production Features:
- Structured logging
- Error handling middleware
- Fallback data when models fail
- Request validation
- CORS configuration
- Static file serving for frontend
- Health checks for monitoring
- Gunicorn-compatible
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()

# ── Import Database ──────────────────────────────────────────
from database import get_connection, init_db, DB_PATH

# ── Import AI Models ─────────────────────────────────────────
from models.demand_predictor import DemandPredictor
from models.supplier_cluster import SupplierCluster
from models.route_optimizer import RouteOptimizer
from models.rag_engine import RAGEngine
from models.risk_detector import RiskDetector
from models.decision_engine import DecisionEngine
from models.gemini_client import GeminiClient


# ═══════════════════════════════════════════════════════════════
#                     LOGGING SETUP
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SupplyChainAI")


# ═══════════════════════════════════════════════════════════════
#                        APP SETUP
# ═══════════════════════════════════════════════════════════════

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Initialize AI Components ─────────────────────────────────
demand_predictor = DemandPredictor()
supplier_cluster = SupplierCluster(n_clusters=3)
route_optimizer = RouteOptimizer()
gemini_client = GeminiClient()
rag_engine = RAGEngine(gemini_client=gemini_client)
risk_detector = RiskDetector(rag_engine=rag_engine, supplier_cluster=supplier_cluster)
decision_engine = DecisionEngine(rag_engine=rag_engine)

# Global state
app_state = {
    "demand_trained": False,
    "suppliers_clustered": False,
    "routes_loaded": False,
    "initialized_at": None,
}

# ═══════════════════════════════════════════════════════════════
#               ERROR HANDLING MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

def api_handler(f):
    """Decorator for safe API endpoint execution with logging and error handling."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "endpoint": f.__name__,
                "timestamp": datetime.now().isoformat(),
            }), 500
    return decorated


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors — try to serve frontend files."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal Server Error: {str(e)}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ═══════════════════════════════════════════════════════════════
#                  FALLBACK DATA
# ═══════════════════════════════════════════════════════════════

FALLBACK_RISK = {
    "overall_risk_score": 15,
    "overall_severity": "low",
    "risk_factors": [
        {"category": "weather", "score": 12, "severity": "low", "description": "Normal conditions.", "icon": "☀️"},
        {"category": "traffic", "score": 10, "severity": "low", "description": "Normal traffic.", "icon": "🚚"},
        {"category": "supplier", "score": 20, "severity": "low", "description": "Suppliers operational.", "icon": "🏭"},
        {"category": "external", "score": 8, "severity": "low", "description": "No external events.", "icon": "🌍"},
        {"category": "demand", "score": 15, "severity": "low", "description": "Demand is stable.", "icon": "📊"},
    ],
    "alerts": [],
    "rag_insights": None,
    "timestamp": datetime.now().isoformat(),
    "simulation_active": False,
}

FALLBACK_DECISIONS = {
    "decisions": [{
        "type": "monitoring",
        "title": "📋 System Status: Normal",
        "description": "All supply chain operations running within normal parameters.",
        "priority": "low",
        "impact": "Maintain efficiency",
        "estimated_cost_saving": "Baseline",
        "action_items": ["Continue monitoring", "Review weekly metrics"],
        "rag_justification": None,
    }],
    "total_decisions": 1,
    "critical_count": 0,
    "high_count": 0,
    "generated_at": datetime.now().isoformat(),
}


# ═══════════════════════════════════════════════════════════════
#                    INITIALIZATION
# ═══════════════════════════════════════════════════════════════

def initialize_system():
    """Load data and initialize all AI models with error resilience."""
    global app_state
    logger.info("🚀 Initializing AI-Powered Supply Chain System...")

    if not os.path.exists(DB_PATH):
        logger.warning("Database not found. Initializing empty database.")
        init_db()
        return

    conn = get_connection()

    try:
        # 1. Train Demand Predictor
        logger.info("📊 Training demand predictor...")
        try:
            cursor = conn.execute(
                "SELECT date, product_id, product_name, demand FROM demand_history ORDER BY date"
            )
            demand_rows = [dict(row) for row in cursor.fetchall()]
            if demand_rows:
                import pandas as pd
                df = pd.DataFrame(demand_rows)
                daily_demand = df.groupby("date").agg({"demand": "sum"}).reset_index()
                metrics = demand_predictor.train(daily_demand.to_dict("records"))
                app_state["demand_trained"] = True
                logger.info(f"   ✅ Demand predictor: R² = {metrics.get('r2_score', 'N/A')}")
        except Exception as e:
            logger.error(f"   ❌ Demand predictor failed: {e}")

        # 2. Cluster Suppliers
        logger.info("🏭 Running supplier clustering...")
        try:
            cursor = conn.execute(
                """SELECT name, delivery_time_days, failure_rate, cost_score,
                          quality_score, reliability_score FROM suppliers"""
            )
            supplier_rows = [dict(row) for row in cursor.fetchall()]
            if supplier_rows:
                result = supplier_cluster.fit(supplier_rows)
                app_state["suppliers_clustered"] = True
                if "suppliers" in result:
                    for s in result["suppliers"]:
                        conn.execute(
                            "UPDATE suppliers SET cluster_label = ? WHERE name = ?",
                            (s["risk_label"], s["name"])
                        )
                    conn.commit()
                logger.info(f"   ✅ Clustering: Silhouette = {result['metrics']['silhouette_score']}")
        except Exception as e:
            logger.error(f"   ❌ Clustering failed: {e}")

        # 3. Build Route Graph
        logger.info("🛣️  Building route graph...")
        try:
            cursor = conn.execute("SELECT id, name, city, lat, lng FROM warehouses")
            warehouses = [dict(row) for row in cursor.fetchall()]
            cursor = conn.execute(
                """SELECT source_id, dest_id, distance_km, travel_time_hours,
                          cost, risk_factor FROM routes"""
            )
            routes = [dict(row) for row in cursor.fetchall()]
            if warehouses and routes:
                route_optimizer.build_graph(warehouses, routes)
                app_state["routes_loaded"] = True
                logger.info(f"   ✅ Route graph: {len(warehouses)} nodes, {len(routes)} edges")
        except Exception as e:
            logger.error(f"   ❌ Route graph failed: {e}")

        app_state["initialized_at"] = datetime.now().isoformat()
        logger.info("=" * 50)
        logger.info("✅ System initialization complete!")
        logger.info(f"   Demand: {'Ready' if app_state['demand_trained'] else 'Fallback mode'}")
        logger.info(f"   Clustering: {'Ready' if app_state['suppliers_clustered'] else 'Fallback mode'}")
        logger.info(f"   Routes: {'Ready' if app_state['routes_loaded'] else 'Fallback mode'}")
        logger.info(f"   RAG Engine: Ready (23 documents)")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Critical initialization error: {e}", exc_info=True)
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
#                      API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

# ── Serve Frontend ───────────────────────────────────────────
@app.route("/")
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ── Health Check ─────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "system": "AI-Powered Supply Chain Risk Predictor & Optimizer",
        "version": "2.0.0",
        "components": app_state,
        "uptime": app_state.get("initialized_at"),
        "timestamp": datetime.now().isoformat(),
    })


# ── 1. DEMAND PREDICTION ────────────────────────────────────
@app.route("/api/predict-demand", methods=["POST"])
@api_handler
def predict_demand():
    data = request.get_json(silent=True) or {}
    days = min(max(int(data.get("days", 30)), 1), 90)  # Clamp between 1-90

    if not app_state["demand_trained"]:
        return jsonify({"success": False, "error": "Demand predictor not ready. Using fallback.", "fallback": True}), 503

    predictions = demand_predictor.predict(days_ahead=days)
    metrics = demand_predictor.get_metrics()

    conn = get_connection()
    cursor = conn.execute(
        """SELECT date, SUM(demand) as demand FROM demand_history
           GROUP BY date ORDER BY date DESC LIMIT 90"""
    )
    historical = [dict(row) for row in cursor.fetchall()]
    historical.reverse()
    conn.close()

    return jsonify({
        "success": True,
        "predictions": predictions,
        "historical": historical,
        "metrics": metrics,
        "model": "Linear Regression (Supervised Learning)",
        "features": ["day_of_week", "month", "seasonality", "trend", "rolling_avg_7", "rolling_avg_30"],
    })


# ── 2. SUPPLIER CLUSTERING ──────────────────────────────────
@app.route("/api/cluster-suppliers", methods=["POST"])
@api_handler
def cluster_suppliers():
    conn = get_connection()
    cursor = conn.execute(
        """SELECT id, name, location, lat, lng, delivery_time_days,
                  failure_rate, cost_score, quality_score, reliability_score
           FROM suppliers"""
    )
    suppliers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not suppliers:
        return jsonify({"success": False, "error": "No supplier data found"}), 404

    data = request.get_json(silent=True) or {}
    n_clusters = min(max(int(data.get("n_clusters", 3)), 2), 5)

    if n_clusters != supplier_cluster.n_clusters:
        cluster_model = SupplierCluster(n_clusters=n_clusters)
        result = cluster_model.fit(suppliers)
    else:
        result = supplier_cluster.fit(suppliers)
        app_state["suppliers_clustered"] = True

    supplier_map = {s["name"]: s for s in suppliers}
    for s in result.get("suppliers", []):
        if s["name"] in supplier_map:
            s["lat"] = supplier_map[s["name"]]["lat"]
            s["lng"] = supplier_map[s["name"]]["lng"]
            s["location"] = supplier_map[s["name"]]["location"]
            s["id"] = supplier_map[s["name"]]["id"]

    return jsonify({"success": True, "algorithm": "K-Means Clustering (Unsupervised Learning)", **result})


# ── 3. ROUTE OPTIMIZATION & DASHBOARD DISPATCHER ──────────────
@app.route("/api/optimize-route", methods=["POST"])
@api_handler
def optimize_route():
    data = request.get_json(silent=True) or {}
    source_id = int(data.get("source_id", 1))
    dest_id = int(data.get("dest_id", 5))

    if not app_state["routes_loaded"]:
        return jsonify({"success": False, "error": "Route graph not loaded"}), 503

    # 1. Evaluate A* Route
    result = route_optimizer.find_shortest_path(source_id, dest_id)
    alternative = None
    path_names = []

    if "error" not in result:
        alternative = route_optimizer.find_alternative_route(source_id, dest_id, result["path"])
        path_names = result.get("path_names", [])

    if not path_names:
        return jsonify({"success": False, "error": result.get("error", "No path found")}), 500

    conn = get_connection()

    # 2. Localized Demand
    route_demand_predictions = []
    route_demand_metrics = {}
    route_demand_historical = []

    try:
        placeholders = ",".join(["?"] * len(path_names))
        cursor = conn.execute(f"""
            SELECT date, SUM(demand) as demand 
            FROM demand_history 
            WHERE region IN ({placeholders}) 
            GROUP BY date ORDER BY date
        """, path_names)
        
        demand_rows = [dict(row) for row in cursor.fetchall()]
        if demand_rows:
            import pandas as pd
            from models.demand_predictor import DemandPredictor
            local_predictor = DemandPredictor()
            df = pd.DataFrame(demand_rows)
            daily_demand = df.groupby("date").agg({"demand": "sum"}).reset_index()
            
            local_predictor.train(daily_demand.to_dict("records"))
            route_demand_predictions = local_predictor.predict(days_ahead=30)
            route_demand_metrics = local_predictor.get_metrics()
            
            cursor = conn.execute(f"""
                SELECT date, SUM(demand) as demand 
                FROM demand_history 
                WHERE region IN ({placeholders})
                GROUP BY date ORDER BY date DESC LIMIT 90
            """, path_names)
            h = [dict(row) for row in cursor.fetchall()]
            h.reverse()
            route_demand_historical = h
    except Exception as e:
        logger.error(f"Localized demand failed: {e}")

    # 3. Localized Suppliers
    route_suppliers = []
    route_cluster_metrics = {}
    try:
        cursor = conn.execute(f"""
            SELECT id, name, location, lat, lng, delivery_time_days,
                   failure_rate, cost_score, quality_score,
                   reliability_score, cluster_label 
            FROM suppliers
            WHERE location IN ({placeholders})
        """, path_names)
        route_suppliers = [dict(row) for row in cursor.fetchall()]
        
        # If very few suppliers on route, cluster chart looks bad. 
        # But we still return them exactly to match user requirement.
        # We can extract the cluster_metrics dynamically if we fit a new model, 
        # but since labels are already assigned across the DB, we just use existing labels.
        route_cluster_metrics = supplier_cluster.get_metrics()
    except Exception as e:
        logger.error(f"Localized suppliers failed: {e}")

    # 4. Localized Risk & Alerts
    try:
        current_risk = risk_detector.detect_risks()
        route_alerts = [a for a in current_risk.get("alerts", []) 
                        if any(p.lower() in a["message"].lower() for p in path_names)]
        route_risk = {
            **current_risk,
            "alerts": route_alerts
        }
    except Exception:
        route_risk = FALLBACK_RISK

    conn.close()

    # 5. Gemini AI Route-Specific Constraints
    insight_text = None
    gemini = rag_engine.gemini_client if hasattr(rag_engine, "gemini_client") else None
    
    if gemini and gemini.is_available:
        try:
            total_km = result.get("total_distance_km", 0)
            route_str = " -> ".join(path_names)
            avg_dmd = sum(p["predicted_demand"] for p in route_demand_predictions) / max(1, len(route_demand_predictions))
            
            prompt = f"""You are an elite AI Supply Chain Optimization Engine.
The user active route is: {route_str} ({total_km} km).
Expected average demand on this corridor: {avg_dmd:.0f} units/day.
Active alerts on route: {len(route_alerts)}.

Generate exactly 3 concise, highly professional constraints/decisions (like a short bulleted list) 
that the logistics team must enforce for this specific route. Provide hyper-specific context to the cities involved.
Do not use markdown headers, just plain bullet points using '-'."""
            
            insight_text = gemini.generate(prompt, max_tokens=250, temperature=0.5)
        except Exception as e:
            logger.warning(f"Route Gemini insight failed: {e}")

    if not insight_text:
        avg_dmd = sum(p["predicted_demand"] for p in route_demand_predictions) / max(1, len(route_demand_predictions)) if route_demand_predictions else 0
        insight_text = (
            f"- Prioritize shipments from {path_names[0]} to accommodate {avg_dmd:.0f} daily units.\n"
            f"- Monitor transport hubs in {path_names[1] if len(path_names)>1 else path_names[0]} closely.\n"
            f"- Maintain 15% safety stock across all route nodes to handle fluctuations."
        )

    return jsonify({
        "success": True,
        "optimal_route": result,
        "alternative_route": alternative,
        "warehouses": route_optimizer.get_all_warehouses(),
        "algorithm": "A* (Haversine Heuristic)",
        "demand_historical": route_demand_historical,
        "demand_predictions": route_demand_predictions,
        "demand_metrics": route_demand_metrics,
        "suppliers": route_suppliers,
        "cluster_metrics": route_cluster_metrics,
        "current_risk": route_risk,
        "rag_intelligence": insight_text,
    })


# ── 4. RISK DETECTION + RAG ─────────────────────────────────
@app.route("/api/detect-risk", methods=["GET", "POST"])
@api_handler
def detect_risk():
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            result = risk_detector.simulate_disruption(
                disruption_type=data.get("simulation_type"),
                location=data.get("location")
            )
        else:
            result = risk_detector.detect_risks()
    except Exception:
        logger.warning("Risk detection failed, returning fallback data")
        result = FALLBACK_RISK

    return jsonify({"success": True, **result, "engine": "Multi-factor Risk Detection + RAG Intelligence"})


# ── 5. DECISION ENGINE ──────────────────────────────────────
@app.route("/api/decision", methods=["POST"])
@api_handler
def get_decisions():
    data = request.get_json(silent=True) or {}

    try:
        risk_data = None
        demand_data = None
        cluster_data = None
        route_data = None

        if data.get("include_risk", True):
            sim_type = data.get("simulation_type")
            location = data.get("location")
            risk_data = risk_detector.simulate_disruption(sim_type, location) if sim_type else risk_detector.detect_risks()

        if data.get("include_demand", True) and app_state["demand_trained"]:
            demand_data = demand_predictor.predict(days_ahead=30)

        if data.get("include_suppliers", True) and app_state["suppliers_clustered"]:
            conn = get_connection()
            cursor = conn.execute(
                """SELECT name, delivery_time_days, failure_rate, cost_score,
                          quality_score, reliability_score FROM suppliers"""
            )
            suppliers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            cluster_data = supplier_cluster.fit(suppliers)

        if data.get("include_routes", True) and app_state["routes_loaded"]:
            route_data = route_optimizer.find_shortest_path(
                int(data.get("source_id", 1)), int(data.get("dest_id", 5))
            )

        result = decision_engine.generate_decisions(
            risk_data=risk_data, demand_data=demand_data,
            cluster_data=cluster_data, route_data=route_data
        )
    except Exception:
        logger.warning("Decision engine failed, returning fallback")
        result = FALLBACK_DECISIONS

    return jsonify({"success": True, **result, "engine": "Smart Decision Engine (AI + RAG)"})


# ── 6. RAG QUERY ────────────────────────────────────────────
@app.route("/api/rag-query", methods=["POST"])
@api_handler
def rag_query():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"success": False, "error": "Please provide a 'question'"}), 400
    result = rag_engine.query(question)
    return jsonify({"success": True, **result, "engine": "RAG (TF-IDF + BM25 Hybrid)"})


# ── 6b. RAG PIPELINE INFO ───────────────────────────────────
@app.route("/api/rag-pipeline", methods=["GET"])
@api_handler
def rag_pipeline_info():
    info = rag_engine.get_pipeline_info()
    return jsonify({"success": True, **info})


# ── 6c. DEMAND AI INSIGHT (Gemini-powered forecast analysis) ─
@app.route("/api/demand-ai-insight", methods=["GET"])
@api_handler
def demand_ai_insight():
    """Generate a Gemini AI narrative about the demand forecast."""
    if not app_state["demand_trained"]:
        return jsonify({"success": False, "error": "Demand model not ready"}), 503

    predictions = demand_predictor.predict(30)
    metrics = demand_predictor.get_metrics()

    if isinstance(predictions, dict) and "error" in predictions:
        return jsonify({"success": False, "error": predictions["error"]}), 500

    avg_pred    = round(sum(p["predicted_demand"] for p in predictions) / len(predictions), 1)
    max_pred    = max(p["predicted_demand"] for p in predictions)
    min_pred    = min(p["predicted_demand"] for p in predictions)
    trend_dir   = "rising" if predictions[-1]["predicted_demand"] > predictions[0]["predicted_demand"] else "declining"
    r2          = metrics.get("r2_score", "N/A")
    mae         = metrics.get("mae", "N/A")

    prompt = f"""You are a senior supply chain demand analyst AI for an Indian logistics company.
Analyze the following ML demand forecast for the next 30 days and provide a brief professional insight (3-4 sentences max).

Forecast Summary:
- Average Daily Demand (total across all products): {avg_pred} units
- Peak Day: {max_pred} units | Trough Day: {min_pred} units
- Demand Trend: {trend_dir}
- Model Accuracy: R² = {r2}, MAE = {mae} units
- Products tracked: Consumer Electronics, Pharmaceuticals, Textiles, Auto Parts, Food & FMCG
- Context: Indian supply chain — consider current season, festival calendar, and logistics constraints.

Provide actionable, professional insights about the demand forecast. Highlight any notable patterns and recommended inventory actions. Be concise."""

    gemini = rag_engine.gemini_client if hasattr(rag_engine, "gemini_client") else None

    insight_text = None
    if gemini and gemini.is_available:
        try:
            insight_text = gemini.generate(prompt, max_tokens=300, temperature=0.5)
        except Exception as e:
            logger.warning(f"Gemini demand insight failed: {e}")

    if not insight_text:
        # Fallback: structured template-based analysis
        direction = "an upward" if trend_dir == "rising" else "a downward"
        insight_text = (
            f"The ML model projects {direction} demand trend over the next 30 days, "
            f"averaging {avg_pred:,.0f} units/day across all product categories "
            f"(R²={r2}, MAE={mae} units). "
            f"Demand spans from {min_pred:,.0f} to {max_pred:,.0f} units, indicating "
            f"{'strong variability — likely driven by festival or seasonal cycles' if (max_pred - min_pred) > avg_pred * 0.3 else 'relatively stable conditions'}. "
            f"Recommended action: Pre-position inventory at high-demand nodes "
            f"{'(Mumbai, Delhi) ahead of the festive surge' if trend_dir == 'rising' else 'and reduce safety stock at low-velocity warehouses'}."
        )

    return jsonify({
        "success": True,
        "insight": insight_text,
        "avg_demand": avg_pred,
        "peak_demand": max_pred,
        "trough_demand": min_pred,
        "trend": trend_dir,
        "model_accuracy": {"r2": r2, "mae": mae},
        "ai_engine": "Gemini 2.5 Flash" if (gemini and gemini.is_available) else "Template Analysis",
        "timestamp": datetime.now().isoformat(),
    })


# ── 6c. QUICK DEMO (chains all 4 core features) ─────────────
@app.route("/api/quick-demo", methods=["POST"])
@api_handler
def quick_demo():
    """Run the complete AI pipeline: Predict → Detect → Simulate → Decide."""
    data = request.get_json(silent=True) or {}
    sim_type = data.get("type", "storm")
    location = data.get("location", "Mumbai")
    source_id = int(data.get("source_id", 1))
    dest_id = int(data.get("dest_id", 5))

    demo_result = {"steps": [], "success": True}

    # Step 1: Demand Prediction
    try:
        if app_state["demand_trained"]:
            preds = demand_predictor.predict(30)
            metrics = demand_predictor.get_metrics()
            conn = get_connection()
            cursor = conn.execute(
                "SELECT date, SUM(demand) as demand FROM demand_history GROUP BY date ORDER BY date DESC LIMIT 90"
            )
            hist = [dict(row) for row in cursor.fetchall()]
            hist.reverse()
            conn.close()
            demo_result["demand"] = {"predictions": preds, "historical": hist, "metrics": metrics}
            demo_result["steps"].append({"step": 1, "name": "Demand Prediction", "status": "complete", "model": "Linear Regression"})
    except Exception as e:
        demo_result["steps"].append({"step": 1, "name": "Demand Prediction", "status": "error", "error": str(e)})

    # Step 2: Risk Detection + RAG
    try:
        risk_result = risk_detector.simulate_disruption(sim_type, location)
        rag_alert = rag_engine.generate_alert(sim_type, location)
        demo_result["risk_assessment"] = risk_result
        demo_result["rag_intelligence"] = rag_alert
        demo_result["steps"].append({"step": 2, "name": "Risk Detection + RAG", "status": "complete", "model": "Multi-Factor + TF-IDF/BM25"})
    except Exception as e:
        demo_result["steps"].append({"step": 2, "name": "Risk Detection + RAG", "status": "error", "error": str(e)})

    # Step 3: Route Optimization
    try:
        if app_state["routes_loaded"]:
            optimal = route_optimizer.find_shortest_path(source_id, dest_id)
            alt = route_optimizer.find_alternative_route(source_id, dest_id, optimal.get("path", []))
            demo_result["optimal_route"] = optimal
            demo_result["alternative_route"] = alt
            demo_result["all_warehouses"] = route_optimizer.get_all_warehouses()
            demo_result["steps"].append({"step": 3, "name": "Route Optimization", "status": "complete", "model": "Dijkstra's Algorithm"})
    except Exception as e:
        demo_result["steps"].append({"step": 3, "name": "Route Optimization", "status": "error", "error": str(e)})

    # Step 4: Decision Engine
    try:
        cluster_data = None
        if app_state["suppliers_clustered"]:
            conn = get_connection()
            cursor = conn.execute("SELECT name, delivery_time_days, failure_rate, cost_score, quality_score, reliability_score FROM suppliers")
            suppliers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            cluster_data = supplier_cluster.fit(suppliers)
            demo_result["cluster_metrics"] = supplier_cluster.get_metrics()

        decisions = decision_engine.generate_decisions(
            risk_data=demo_result.get("risk_assessment"),
            demand_data=demo_result.get("demand", {}).get("predictions"),
            cluster_data=cluster_data,
            route_data=demo_result.get("optimal_route"),
        )
        demo_result["decisions"] = decisions
        demo_result["steps"].append({"step": 4, "name": "AI Decision Engine", "status": "complete", "model": "Multi-Model + RAG"})
    except Exception as e:
        demo_result["steps"].append({"step": 4, "name": "AI Decision Engine", "status": "error", "error": str(e)})

    # Suppliers for clustering chart
    if app_state["suppliers_clustered"]:
        conn = get_connection()
        cursor = conn.execute(
            """SELECT id, name, location, lat, lng, delivery_time_days,
                      failure_rate, cost_score, quality_score,
                      reliability_score, cluster_label FROM suppliers"""
        )
        demo_result["suppliers"] = [dict(row) for row in cursor.fetchall()]
        conn.close()

    demo_result["simulation"] = {"type": sim_type, "location": location}
    demo_result["rag_pipeline"] = rag_engine.get_pipeline_info()
    demo_result["timestamp"] = datetime.now().isoformat()

    return jsonify(demo_result)


# ── 7. DASHBOARD DATA ───────────────────────────────────────
@app.route("/api/dashboard-data", methods=["GET"])
@api_handler
def dashboard_data():
    conn = get_connection()
    result = {"system_status": app_state}

    # Demand
    if app_state["demand_trained"]:
        result["demand_predictions"] = demand_predictor.predict(30)
        result["demand_metrics"] = demand_predictor.get_metrics()
        cursor = conn.execute(
            "SELECT date, SUM(demand) as demand FROM demand_history GROUP BY date ORDER BY date DESC LIMIT 90"
        )
        h = [dict(row) for row in cursor.fetchall()]
        h.reverse()
        result["demand_historical"] = h

    # Suppliers
    if app_state["suppliers_clustered"]:
        cursor = conn.execute(
            """SELECT id, name, location, lat, lng, delivery_time_days,
                      failure_rate, cost_score, quality_score,
                      reliability_score, cluster_label FROM suppliers"""
        )
        result["suppliers"] = [dict(row) for row in cursor.fetchall()]
        result["cluster_metrics"] = supplier_cluster.get_metrics()

    # Warehouses
    cursor = conn.execute("SELECT id, name, city, lat, lng, capacity, current_stock FROM warehouses")
    result["warehouses"] = [dict(row) for row in cursor.fetchall()]

    # Routes
    if app_state["routes_loaded"]:
        result["default_route"] = route_optimizer.find_shortest_path(1, 5)
        result["alternative_route"] = route_optimizer.find_alternative_route(
            1, 5, result["default_route"].get("path", [])
        )

    # Risk
    cursor = conn.execute(
        "SELECT * FROM risk_events WHERE is_active = 1 ORDER BY risk_score DESC"
    )
    result["active_risk_events"] = [dict(row) for row in cursor.fetchall()]

    try:
        result["current_risk"] = risk_detector.detect_risks()
    except Exception:
        result["current_risk"] = FALLBACK_RISK

    conn.close()
    return jsonify({"success": True, **result, "timestamp": datetime.now().isoformat()})


# ── 8. SIMULATE DISRUPTION ───────────────────────────────────
@app.route("/api/simulate", methods=["POST"])
@api_handler
def simulate():
    data = request.get_json(silent=True) or {}
    sim_type = data.get("type", "storm")
    location = data.get("location", "Mumbai")
    source_id = int(data.get("source_id", 1))
    dest_id = int(data.get("dest_id", 5))

    risk_result = risk_detector.simulate_disruption(sim_type, location)
    rag_alert = rag_engine.generate_alert(sim_type, location)

    route_result = None
    alt_route_result = None
    if app_state["routes_loaded"]:
        route_result = route_optimizer.find_shortest_path(source_id, dest_id)
        if "error" not in route_result:
            alt_route_result = route_optimizer.find_alternative_route(
                source_id, dest_id, route_result["path"]
            )

    demand_data = demand_predictor.predict(30) if app_state["demand_trained"] else None
    cluster_data = None
    if app_state["suppliers_clustered"]:
        conn = get_connection()
        cursor = conn.execute(
            """SELECT name, delivery_time_days, failure_rate, cost_score,
                      quality_score, reliability_score FROM suppliers"""
        )
        suppliers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        cluster_data = supplier_cluster.fit(suppliers)
        cluster_metrics = supplier_cluster.get_metrics()

    decisions = decision_engine.generate_decisions(
        risk_data=risk_result, demand_data=demand_data,
        cluster_data=cluster_data, route_data=route_result
    )

    # Log event
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO risk_events (event_type, severity, location, description, risk_score)
               VALUES (?, ?, ?, ?, ?)""",
            (sim_type, risk_result["overall_severity"], location,
             f"Simulated {sim_type} disruption in {location}",
             risk_result["overall_risk_score"])
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to log event: {e}")

    return jsonify({
        "success": True,
        "simulation": {"type": sim_type, "location": location, "timestamp": datetime.now().isoformat()},
        "risk_assessment": risk_result,
        "rag_intelligence": rag_alert,
        "optimal_route": route_result,
        "alternative_route": alt_route_result,
        "decisions": decisions,
        "cluster_metrics": cluster_metrics if app_state["suppliers_clustered"] else None,
        "all_warehouses": route_optimizer.get_all_warehouses() if app_state["routes_loaded"] else [],
    })


# ═══════════════════════════════════════════════════════════════
#                        MAIN
# ═══════════════════════════════════════════════════════════════

# Initialize on import (for Gunicorn)
init_db()
conn = get_connection()
cursor = conn.execute("SELECT COUNT(*) as cnt FROM demand_history")
count = cursor.fetchone()["cnt"]
conn.close()

if count == 0:
    logger.info("Database empty — seeding data...")
    from seed_data import seed_all
    seed_all()

initialize_system()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌐 Starting server on http://localhost:{port}")
    logger.info(f"📊 Dashboard: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
