"""
supplier_cluster.py — Unsupervised Learning: Supplier Risk Clustering
======================================================================
Uses K-Means Clustering to group suppliers into risk categories:
- Cluster 0: Low Risk (reliable, high quality)
- Cluster 1: Medium Risk (average performance)
- Cluster 2: High Risk (unreliable, low quality)

Features used: delivery_time, failure_rate, cost_score, quality_score, reliability_score
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


class SupplierCluster:
    """Unsupervised Learning model for supplier risk clustering using K-Means."""

    def __init__(self, n_clusters=3):
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.metrics = {}
        self.cluster_labels_map = {}  # maps cluster number → risk label

    def fit(self, suppliers_data):
        """
        Cluster suppliers into risk groups.

        Args:
            suppliers_data: list of dicts with keys:
                - name, delivery_time_days, failure_rate, cost_score,
                  quality_score, reliability_score

        Returns:
            dict with cluster assignments and metrics
        """
        if len(suppliers_data) < self.n_clusters:
            return {"error": f"Need at least {self.n_clusters} suppliers to cluster"}

        # Extract features
        names = [s["name"] for s in suppliers_data]
        features = np.array([
            [
                s["delivery_time_days"],
                s["failure_rate"],
                10 - s["cost_score"],       # Invert: higher cost = higher risk
                10 - s["quality_score"],     # Invert: lower quality = higher risk
                10 - s["reliability_score"]  # Invert: lower reliability = higher risk
            ]
            for s in suppliers_data
        ])

        # Scale features
        features_scaled = self.scaler.fit_transform(features)

        # Fit K-Means
        cluster_labels = self.model.fit_predict(features_scaled)
        self.is_fitted = True

        # Calculate cluster centers and determine risk levels
        # Higher center values = higher risk
        centers = self.model.cluster_centers_
        center_magnitudes = np.linalg.norm(centers, axis=1)
        sorted_indices = np.argsort(center_magnitudes)

        risk_labels = ["Low Risk", "Medium Risk", "High Risk"]
        self.cluster_labels_map = {
            int(sorted_indices[i]): risk_labels[i]
            for i in range(self.n_clusters)
        }

        # Calculate silhouette score
        sil_score = silhouette_score(features_scaled, cluster_labels)

        # Build result
        results = []
        for i, name in enumerate(names):
            cluster_num = int(cluster_labels[i])
            risk_label = self.cluster_labels_map[cluster_num]
            results.append({
                "name": name,
                "cluster": cluster_num,
                "risk_label": risk_label,
                "delivery_time_days": suppliers_data[i]["delivery_time_days"],
                "failure_rate": suppliers_data[i]["failure_rate"],
                "cost_score": suppliers_data[i]["cost_score"],
                "quality_score": suppliers_data[i]["quality_score"],
                "reliability_score": suppliers_data[i]["reliability_score"],
            })

        # Cluster summaries
        cluster_summaries = {}
        for label_num, risk_label in self.cluster_labels_map.items():
            cluster_members = [r for r in results if r["cluster"] == label_num]
            if cluster_members:
                cluster_summaries[risk_label] = {
                    "count": len(cluster_members),
                    "avg_delivery_time": round(np.mean([m["delivery_time_days"] for m in cluster_members]), 2),
                    "avg_failure_rate": round(np.mean([m["failure_rate"] for m in cluster_members]), 4),
                    "avg_quality_score": round(np.mean([m["quality_score"] for m in cluster_members]), 2),
                    "suppliers": [m["name"] for m in cluster_members],
                }

        self.metrics = {
            "silhouette_score": round(sil_score, 4),
            "n_clusters": self.n_clusters,
            "total_suppliers": len(suppliers_data),
            "cluster_sizes": {
                self.cluster_labels_map[k]: int(v)
                for k, v in zip(*np.unique(cluster_labels, return_counts=True))
            }
        }

        return {
            "suppliers": results,
            "metrics": self.metrics,
            "cluster_summaries": cluster_summaries,
        }

    def predict_risk(self, supplier_data):
        """
        Predict risk category for a new supplier.

        Args:
            supplier_data: dict with delivery_time_days, failure_rate,
                          cost_score, quality_score, reliability_score

        Returns:
            dict with predicted risk label
        """
        if not self.is_fitted:
            return {"error": "Model not fitted yet. Call fit() first."}

        features = np.array([[
            supplier_data["delivery_time_days"],
            supplier_data["failure_rate"],
            10 - supplier_data["cost_score"],
            10 - supplier_data["quality_score"],
            10 - supplier_data["reliability_score"],
        ]])

        features_scaled = self.scaler.transform(features)
        cluster = int(self.model.predict(features_scaled)[0])
        risk_label = self.cluster_labels_map[cluster]

        return {
            "cluster": cluster,
            "risk_label": risk_label,
            "name": supplier_data.get("name", "Unknown"),
        }

    def get_metrics(self):
        """Return clustering metrics."""
        return self.metrics if self.metrics else {"error": "Model not fitted yet"}
