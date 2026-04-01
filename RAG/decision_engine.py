"""
decision_engine.py — Smart AI Decision Engine
===============================================
Generates intelligent supply chain decisions based on:
- Demand prediction results
- Supplier clustering (risk levels)
- Route optimization data
- Risk detection scores
- RAG insights

Each decision includes: action, justification, priority, and impact estimate.
"""

from datetime import datetime


class DecisionEngine:
    """AI-powered decision engine for supply chain optimization."""

    def __init__(self, rag_engine=None):
        self.rag_engine = rag_engine
        self.decision_history = []

    def generate_decisions(self, risk_data=None, demand_data=None,
                           cluster_data=None, route_data=None):
        """
        Generate smart decisions based on all available AI data.

        Args:
            risk_data: output from RiskDetector.detect_risks()
            demand_data: output from DemandPredictor.predict()
            cluster_data: output from SupplierCluster.fit()
            route_data: output from RouteOptimizer.find_shortest_path()

        Returns:
            dict with prioritized decisions and justifications
        """
        decisions = []

        # ── 1. Risk-Based Decisions ──────────────────────────
        if risk_data:
            decisions.extend(self._risk_decisions(risk_data))

        # ── 2. Demand-Based Decisions ────────────────────────
        if demand_data:
            decisions.extend(self._demand_decisions(demand_data))

        # ── 3. Supplier-Based Decisions ──────────────────────
        if cluster_data:
            decisions.extend(self._supplier_decisions(cluster_data))

        # ── 4. Route-Based Decisions ─────────────────────────
        if route_data:
            decisions.extend(self._route_decisions(route_data))

        # If no specific data, provide general decisions
        if not decisions:
            decisions = self._general_decisions()

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        decisions.sort(key=lambda d: priority_order.get(d["priority"], 3))

        # Add RAG justifications
        if self.rag_engine:
            for decision in decisions:
                self._add_rag_justification(decision)

        # Store in history
        result = {
            "decisions": decisions,
            "total_decisions": len(decisions),
            "critical_count": sum(1 for d in decisions if d["priority"] == "critical"),
            "high_count": sum(1 for d in decisions if d["priority"] == "high"),
            "generated_at": datetime.now().isoformat(),
        }

        self.decision_history.append(result)
        return result

    def _risk_decisions(self, risk_data):
        """Generate decisions based on risk assessment."""
        decisions = []
        overall_score = risk_data.get("overall_risk_score", 0)
        risk_factors = risk_data.get("risk_factors", [])

        # Overall high risk
        if overall_score >= 70:
            decisions.append({
                "type": "emergency_protocol",
                "title": "🔴 Activate Emergency Supply Chain Protocol",
                "description": (
                    f"Overall risk score is {overall_score}/100 (critical level). "
                    f"Activate emergency protocols: switch to backup suppliers, "
                    f"reroute active shipments, and increase safety stock at all warehouses."
                ),
                "priority": "critical",
                "impact": "Prevents potential supply chain breakdown",
                "estimated_cost_saving": "$50,000 - $200,000 in avoided losses",
                "action_items": [
                    "Activate all backup supplier contracts",
                    "Reroute in-transit shipments via safe corridors",
                    "Increase safety stock by 50% at unaffected warehouses",
                    "Alert all stakeholders and customers",
                ],
            })

        # Weather-specific decisions
        for rf in risk_factors:
            if rf["category"] == "weather" and rf["score"] >= 50:
                decisions.append({
                    "type": "route_change",
                    "title": "🌧️ Reroute Shipments Away from Weather Zone",
                    "description": (
                        f"Weather risk score: {rf['score']}/100. {rf['description']} "
                        f"Recommend rerouting all active shipments through unaffected corridors."
                    ),
                    "priority": "high",
                    "impact": "Avoids weather-related delays of 24-72 hours",
                    "estimated_cost_saving": "$10,000 - $30,000 per rerouted shipment",
                    "action_items": [
                        "Calculate alternative routes avoiding affected region",
                        "Contact carriers for route change",
                        "Update delivery ETAs for affected orders",
                    ],
                })

            # Supplier-specific decisions
            if rf["category"] == "supplier" and rf["score"] >= 50:
                decisions.append({
                    "type": "supplier_switch",
                    "title": "🏭 Switch to Backup Suppliers",
                    "description": (
                        f"Supplier risk score: {rf['score']}/100. {rf['description']} "
                        f"Activate orders with low-risk cluster suppliers."
                    ),
                    "priority": "high",
                    "impact": "Ensures supply continuity",
                    "estimated_cost_saving": "$20,000 - $80,000 in avoided stockouts",
                    "action_items": [
                        "Identify low-risk suppliers from clustering analysis",
                        "Place emergency orders with backup suppliers",
                        "Negotiate expedited delivery terms",
                    ],
                })

            # Traffic decisions
            if rf["category"] == "traffic" and rf["score"] >= 50:
                decisions.append({
                    "type": "transport_mode_change",
                    "title": "🚚 Switch Transport Mode",
                    "description": (
                        f"Traffic risk score: {rf['score']}/100. {rf['description']} "
                        f"Consider switching from road to rail transport where available."
                    ),
                    "priority": "medium",
                    "impact": "Reduces transit time by 30-50%",
                    "estimated_cost_saving": "$5,000 - $15,000 per route",
                    "action_items": [
                        "Identify rail-connected warehouses",
                        "Book rail freight capacity",
                        "Update logistics plan",
                    ],
                })

        return decisions

    def _demand_decisions(self, demand_data):
        """Generate decisions based on demand predictions."""
        decisions = []

        if isinstance(demand_data, list) and len(demand_data) > 0:
            # Calculate demand trend
            demands = [d.get("predicted_demand", 0) for d in demand_data]
            if len(demands) >= 7:
                first_week_avg = sum(demands[:7]) / 7
                last_week_avg = sum(demands[-7:]) / 7

                if last_week_avg > first_week_avg * 1.3:  # 30% increase
                    decisions.append({
                        "type": "inventory_increase",
                        "title": "📈 Increase Inventory — Demand Surge Predicted",
                        "description": (
                            f"AI demand prediction shows {round((last_week_avg/first_week_avg - 1) * 100, 1)}% "
                            f"increase in demand over the forecast period. "
                            f"Average predicted demand: {round(sum(demands)/len(demands), 1)} units/day."
                        ),
                        "priority": "high",
                        "impact": "Prevents stockouts during demand surge",
                        "estimated_cost_saving": "$30,000 - $100,000 in captured sales",
                        "action_items": [
                            "Increase purchase orders by 30-50%",
                            "Expedite pending supplier deliveries",
                            "Reserve additional warehouse space",
                            "Alert sales team to expected availability",
                        ],
                    })
                elif last_week_avg < first_week_avg * 0.7:  # 30% decrease
                    decisions.append({
                        "type": "inventory_reduction",
                        "title": "📉 Reduce Procurement — Demand Decline Predicted",
                        "description": (
                            f"AI forecasts {round((1 - last_week_avg/first_week_avg) * 100, 1)}% "
                            f"decrease in demand. Reduce new orders to prevent excess inventory."
                        ),
                        "priority": "medium",
                        "impact": "Avoids excess inventory carrying costs",
                        "estimated_cost_saving": "$15,000 - $40,000 in reduced holding costs",
                        "action_items": [
                            "Reduce purchase orders by 20-30%",
                            "Defer non-urgent deliveries",
                            "Consider promotional pricing to clear stock",
                        ],
                    })
                else:
                    decisions.append({
                        "type": "steady_state",
                        "title": "📊 Maintain Current Inventory Levels",
                        "description": (
                            f"Demand forecast shows stable patterns. Average predicted demand: "
                            f"{round(sum(demands)/len(demands), 1)} units/day. "
                            f"Current procurement levels are appropriate."
                        ),
                        "priority": "low",
                        "impact": "Continued efficient operations",
                        "estimated_cost_saving": "Optimal cost baseline maintained",
                        "action_items": [
                            "Continue normal procurement cycles",
                            "Monitor for anomalous demand patterns",
                        ],
                    })

        return decisions

    def _supplier_decisions(self, cluster_data):
        """Generate decisions based on supplier clustering."""
        decisions = []

        if "cluster_summaries" in cluster_data:
            summaries = cluster_data["cluster_summaries"]

            # Check high risk cluster
            if "High Risk" in summaries:
                hr = summaries["High Risk"]
                decisions.append({
                    "type": "supplier_diversification",
                    "title": "⚠️ Diversify Away from High-Risk Suppliers",
                    "description": (
                        f"K-Means clustering identified {hr['count']} high-risk suppliers "
                        f"with average failure rate of {hr['avg_failure_rate']*100:.1f}% "
                        f"and delivery time of {hr['avg_delivery_time']:.1f} days. "
                        f"Suppliers: {', '.join(hr['suppliers'][:3])}."
                    ),
                    "priority": "medium",
                    "impact": "Reduces supply chain vulnerability by 40%",
                    "estimated_cost_saving": "$25,000 - $75,000 annually",
                    "action_items": [
                        f"Reduce order volume from: {', '.join(hr['suppliers'][:3])}",
                        "Onboard 2-3 new low-risk suppliers",
                        "Implement supplier performance monitoring",
                    ],
                })

            # Highlight low risk suppliers
            if "Low Risk" in summaries:
                lr = summaries["Low Risk"]
                decisions.append({
                    "type": "supplier_consolidation",
                    "title": "✅ Consolidate with Top-Performing Suppliers",
                    "description": (
                        f"Clustering identifies {lr['count']} high-reliability suppliers "
                        f"with {lr['avg_failure_rate']*100:.1f}% failure rate "
                        f"and {lr['avg_delivery_time']:.1f} day delivery average. "
                        f"Consider increasing order volumes with these partners."
                    ),
                    "priority": "low",
                    "impact": "Improves overall supply reliability",
                    "estimated_cost_saving": "$10,000 - $30,000 from reduced failures",
                    "action_items": [
                        f"Negotiate volume discounts with: {', '.join(lr['suppliers'][:3])}",
                        "Establish preferred supplier agreements",
                    ],
                })

        return decisions

    def _route_decisions(self, route_data):
        """Generate decisions based on route optimization."""
        decisions = []

        if "error" not in route_data:
            avg_risk = route_data.get("average_risk_factor", 0)

            if avg_risk > 0.1:
                decisions.append({
                    "type": "route_optimization",
                    "title": "🗺️ Consider Alternative Lower-Risk Route",
                    "description": (
                        f"Current optimal route ({' → '.join(route_data.get('path_names', []))}) "
                        f"has average risk factor of {avg_risk:.2f}. "
                        f"Total distance: {route_data.get('total_distance_km', 0)} km, "
                        f"estimated time: {route_data.get('total_time_hours', 0)} hours."
                    ),
                    "priority": "medium",
                    "impact": "Reduces in-transit risk exposure",
                    "estimated_cost_saving": "$5,000 - $20,000 per disrupted route",
                    "action_items": [
                        "Evaluate alternative routes with lower risk factors",
                        "Pre-plan backup routes for critical shipments",
                        "Consider splitting shipments across multiple routes",
                    ],
                })

        return decisions

    def _general_decisions(self):
        """Generate general supply chain optimization decisions."""
        return [
            {
                "type": "monitoring",
                "title": "📋 Supply Chain Status: Normal Operations",
                "description": (
                    "No significant risks detected. All supply chain operations "
                    "running within normal parameters. Continue standard monitoring."
                ),
                "priority": "low",
                "impact": "Maintain operational efficiency",
                "estimated_cost_saving": "Baseline operations",
                "action_items": [
                    "Continue regular supply chain monitoring",
                    "Review supplier performance metrics weekly",
                    "Update demand forecasts with latest data",
                ],
            }
        ]

    def _add_rag_justification(self, decision):
        """Add RAG-based justification to a decision."""
        if not self.rag_engine:
            decision["rag_justification"] = None
            return

        # Query RAG for relevant context
        query = f"{decision['type']} {decision['title']} supply chain"
        docs = self.rag_engine.retrieve(query, top_k=2)

        if docs:
            excerpts = [d["chunk_text"][:150] for d in docs]
            decision["rag_justification"] = {
                "supporting_evidence": excerpts,
                "confidence": round(
                    sum(d["hybrid_score"] for d in docs) / len(docs), 2
                ),
                "sources_consulted": len(docs),
            }
        else:
            decision["rag_justification"] = {
                "supporting_evidence": ["General supply chain best practices"],
                "confidence": 0.5,
                "sources_consulted": 0,
            }

    def get_decision_summary(self):
        """Return a summary of recent decisions."""
        if not self.decision_history:
            return {"message": "No decisions generated yet"}

        latest = self.decision_history[-1]
        return {
            "total_decisions_generated": sum(
                d["total_decisions"] for d in self.decision_history
            ),
            "latest_batch": latest["total_decisions"],
            "latest_critical": latest["critical_count"],
            "latest_high": latest["high_count"],
            "history_length": len(self.decision_history)
        }
