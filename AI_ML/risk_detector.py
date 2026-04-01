"""
risk_detector.py — Supply Chain Risk Detection Engine
======================================================
Combines multiple risk signals to calculate overall risk scores:
- Weather disruptions (simulated)
- Traffic / transport issues
- Supplier risk (from K-Means clustering)
- External events (from RAG engine)

Generates contextual alerts with severity levels and actionable insights.
"""

import random
from datetime import datetime


class RiskDetector:
    """Multi-factor risk detection engine for supply chain disruptions."""

    def __init__(self, rag_engine=None, supplier_cluster=None):
        self.rag_engine = rag_engine
        self.supplier_cluster = supplier_cluster
        self.active_risks = []
        self.risk_history = []

    def detect_risks(self, location=None, include_simulation=False, simulation_type=None):
        """
        Detect and score all active risks.

        Args:
            location: optional location to check for location-specific risks
            include_simulation: whether to include simulated disruptions
            simulation_type: type of disruption to simulate

        Returns:
            dict with overall risk score, individual risk factors, and alerts
        """
        risk_factors = []

        # ── 1. Weather Risk ──────────────────────────────────
        weather_risk = self._assess_weather_risk(location, simulation_type)
        risk_factors.append(weather_risk)

        # ── 2. Traffic/Transport Risk ────────────────────────
        traffic_risk = self._assess_traffic_risk(location, simulation_type)
        risk_factors.append(traffic_risk)

        # ── 3. Supplier Risk (from clustering) ───────────────
        supplier_risk = self._assess_supplier_risk()
        risk_factors.append(supplier_risk)

        # ── 4. External Events Risk (from RAG) ───────────────
        external_risk = self._assess_external_risk(location, simulation_type)
        risk_factors.append(external_risk)

        # ── 5. Demand Risk ───────────────────────────────────
        demand_risk = self._assess_demand_risk(simulation_type)
        risk_factors.append(demand_risk)

        # ── Calculate Overall Risk Score ─────────────────────
        weights = {
            "weather": 0.25,
            "traffic": 0.20,
            "supplier": 0.20,
            "external": 0.20,
            "demand": 0.15,
        }

        overall_score = sum(
            rf["score"] * weights.get(rf["category"], 0.2)
            for rf in risk_factors
        )
        overall_score = min(100, round(overall_score, 1))

        # Determine overall severity
        if overall_score >= 75:
            overall_severity = "critical"
        elif overall_score >= 50:
            overall_severity = "high"
        elif overall_score >= 25:
            overall_severity = "medium"
        else:
            overall_severity = "low"

        # Generate alerts for high-risk factors
        alerts = self._generate_alerts(risk_factors, overall_severity)

        # Get RAG intelligence if available
        rag_insights = None
        if self.rag_engine and simulation_type:
            rag_insights = self.rag_engine.generate_alert(
                disruption_type=simulation_type,
                location=location,
                severity=overall_severity
            )

        result = {
            "overall_risk_score": overall_score,
            "overall_severity": overall_severity,
            "risk_factors": risk_factors,
            "alerts": alerts,
            "rag_insights": rag_insights,
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "simulation_active": include_simulation,
        }

        # Store in history
        self.risk_history.append({
            "score": overall_score,
            "severity": overall_severity,
            "timestamp": result["timestamp"]
        })

        self.active_risks = risk_factors

        return result

    def _assess_weather_risk(self, location=None, simulation_type=None):
        """Assess weather-related risk."""
        base_score = random.uniform(10, 30)  # Background weather risk

        if simulation_type in ["storm", "monsoon", "cyclone", "flood", "weather"]:
            base_score = random.uniform(65, 95)
        elif simulation_type == "heat_wave":
            base_score = random.uniform(50, 75)
        elif simulation_type == "fog":
            base_score = random.uniform(40, 60)

        description = self._get_weather_description(base_score, location)

        return {
            "category": "weather",
            "score": round(base_score, 1),
            "severity": self._score_to_severity(base_score),
            "description": description,
            "icon": "🌧️" if base_score > 50 else "☀️",
        }

    def _assess_traffic_risk(self, location=None, simulation_type=None):
        """Assess traffic and transportation risk."""
        base_score = random.uniform(5, 25)

        if simulation_type in ["strike", "traffic", "road_block"]:
            base_score = random.uniform(60, 90)
        elif simulation_type == "construction":
            base_score = random.uniform(35, 55)

        descriptions = {
            "low": "Normal traffic conditions. All routes operational.",
            "medium": "Moderate congestion detected on key corridors. Minor delays expected.",
            "high": "Significant transport disruption detected. Major route delays of 6-12 hours.",
            "critical": "Transport network severely disrupted. Multiple routes blocked or impassable.",
        }

        severity = self._score_to_severity(base_score)

        return {
            "category": "traffic",
            "score": round(base_score, 1),
            "severity": severity,
            "description": descriptions.get(severity, descriptions["low"]),
            "icon": "🚚" if base_score <= 50 else "🚫",
        }

    def _assess_supplier_risk(self):
        """Assess supplier risk based on clustering results."""
        # Use cluster metrics if available
        base_score = random.uniform(15, 35)

        if self.supplier_cluster and hasattr(self.supplier_cluster, 'metrics') and self.supplier_cluster.metrics:
            cluster_sizes = self.supplier_cluster.metrics.get("cluster_sizes", {})
            high_risk_count = cluster_sizes.get("High Risk", 0)
            total = self.supplier_cluster.metrics.get("total_suppliers", 1)
            high_risk_ratio = high_risk_count / max(total, 1)
            base_score = max(15, min(85, high_risk_ratio * 200))

        severity = self._score_to_severity(base_score)
        descriptions = {
            "low": "All key suppliers operating normally. Supply chain stable.",
            "medium": "Some suppliers showing elevated risk indicators. Monitoring closely.",
            "high": "Multiple high-risk suppliers detected. Consider activating alternates.",
            "critical": "Critical supplier failures imminent. Emergency procurement needed.",
        }

        return {
            "category": "supplier",
            "score": round(base_score, 1),
            "severity": severity,
            "description": descriptions.get(severity, descriptions["low"]),
            "icon": "🏭",
        }

    def _assess_external_risk(self, location=None, simulation_type=None):
        """Assess external event risk using RAG engine."""
        base_score = random.uniform(5, 20)

        if simulation_type in ["earthquake", "pandemic", "political", "sanctions"]:
            base_score = random.uniform(70, 95)
        elif simulation_type in ["regulation", "policy"]:
            base_score = random.uniform(30, 50)

        severity = self._score_to_severity(base_score)

        # Get RAG context if available
        description = "No significant external events detected."
        if self.rag_engine and simulation_type:
            query = f"{simulation_type} supply chain impact"
            docs = self.rag_engine.retrieve(query, top_k=1)
            if docs:
                description = docs[0]["chunk_text"][:200]

        return {
            "category": "external",
            "score": round(base_score, 1),
            "severity": severity,
            "description": description,
            "icon": "🌍",
        }

    def _assess_demand_risk(self, simulation_type=None):
        """Assess demand-related risk."""
        base_score = random.uniform(10, 30)

        if simulation_type == "demand_spike":
            base_score = random.uniform(60, 85)
        elif simulation_type == "demand_drop":
            base_score = random.uniform(40, 60)

        severity = self._score_to_severity(base_score)
        descriptions = {
            "low": "Demand patterns within normal range. No anomalies detected.",
            "medium": "Slight demand fluctuations detected. Monitor for trends.",
            "high": "Significant demand anomaly detected. Inventory adjustment recommended.",
            "critical": "Extreme demand spike/drop. Emergency inventory action required.",
        }

        return {
            "category": "demand",
            "score": round(base_score, 1),
            "severity": severity,
            "description": descriptions.get(severity, descriptions["low"]),
            "icon": "📊",
        }

    def _score_to_severity(self, score):
        """Convert numeric score to severity label."""
        if score >= 75:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        else:
            return "low"

    def _get_weather_description(self, score, location=None):
        """Generate weather risk description based on score."""
        loc_text = f" in {location}" if location else ""
        if score >= 75:
            return f"Severe weather event detected{loc_text}. Major disruption to logistics operations expected. Activate emergency protocols."
        elif score >= 50:
            return f"Significant weather disruption{loc_text}. Delays of 24-48 hours likely on affected routes."
        elif score >= 25:
            return f"Moderate weather conditions{loc_text}. Minor delays possible. Monitor forecasts."
        else:
            return f"Normal weather conditions{loc_text}. No impact on operations."

    def _generate_alerts(self, risk_factors, overall_severity):
        """Generate actionable alerts from risk factors."""
        alerts = []
        severity_priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        for rf in sorted(risk_factors, key=lambda x: severity_priority.get(x["severity"], 3)):
            if rf["severity"] in ["high", "critical"]:
                severity_icons = {"high": "🚨", "critical": "🔴"}
                alerts.append({
                    "title": f"{severity_icons.get(rf['severity'], '⚠️')} {rf['category'].title()} Risk Alert",
                    "message": rf["description"],
                    "severity": rf["severity"],
                    "score": rf["score"],
                    "category": rf["category"],
                    "timestamp": datetime.now().isoformat(),
                })
            elif rf["severity"] == "medium":
                alerts.append({
                    "title": f"⚠️ {rf['category'].title()} Advisory",
                    "message": rf["description"],
                    "severity": rf["severity"],
                    "score": rf["score"],
                    "category": rf["category"],
                    "timestamp": datetime.now().isoformat(),
                })

        return alerts

    def simulate_disruption(self, disruption_type, location=None):
        """
        Simulate a specific disruption scenario.

        Args:
            disruption_type: one of 'storm', 'strike', 'earthquake', 'supplier_failure',
                           'demand_spike', 'pandemic', 'construction'
            location: optional location context

        Returns:
            Full risk assessment with simulation active
        """
        return self.detect_risks(
            location=location,
            include_simulation=True,
            simulation_type=disruption_type
        )

    def get_risk_history(self):
        """Return risk score history."""
        return self.risk_history[-50:]  # Last 50 readings
