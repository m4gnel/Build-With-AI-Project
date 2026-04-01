"""
demand_predictor.py — Supervised Learning: Demand Prediction
=============================================================
Uses Linear Regression to predict future product demand based on
historical data with feature engineering for:
- Day of week patterns
- Monthly seasonality
- Long-term trend
- Rolling averages
- Festival/monsoon impact awareness
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from datetime import datetime, timedelta
import math


# ── Indian Festival Calendar for annotations ─────────────────────
FESTIVAL_ANNOTATIONS = [
    {"name": "Makar Sankranti", "month": 1, "day": 14, "impact": "medium", "category": "festival"},
    {"name": "Republic Day", "month": 1, "day": 26, "impact": "low", "category": "national"},
    {"name": "Holi", "month": 3, "day": 26, "impact": "high", "category": "festival"},
    {"name": "Baisakhi", "month": 4, "day": 14, "impact": "medium", "category": "festival"},
    {"name": "Independence Day", "month": 8, "day": 15, "impact": "medium", "category": "national"},
    {"name": "Ganesh Chaturthi", "month": 9, "day": 8, "impact": "high", "category": "festival"},
    {"name": "Navratri Start", "month": 10, "day": 5, "impact": "high", "category": "festival"},
    {"name": "Diwali", "month": 10, "day": 22, "impact": "very_high", "category": "festival"},
    {"name": "Christmas", "month": 12, "day": 25, "impact": "high", "category": "festival"},
    {"name": "New Year Eve", "month": 12, "day": 31, "impact": "high", "category": "festival"},
]

MONSOON_MONTHS = [6, 7, 8, 9]
FISCAL_Q4_MONTHS = [1, 2, 3]
FESTIVE_QUARTER_MONTHS = [10, 11]


class DemandPredictor:
    """Supervised Learning model for demand prediction using Linear Regression."""

    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.metrics = {}
        self._residual_std = 0
        self._last_date = None
        self._last_trend = 0
        self._last_rolling_7 = 0
        self._last_rolling_30 = 0
        self._mean_demand = 0
        self._product_models = {}  # per-product models

    def _engineer_features(self, df):
        """
        Create features from date and demand data.
        Features: day_of_week, month, day_of_month, is_weekend, trend, sin/cos seasonality
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # Time-based features
        df["day_of_week"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month
        df["day_of_month"] = df["date"].dt.day
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        # Trend feature (days since start)
        df["trend"] = (df["date"] - df["date"].min()).dt.days

        # Cyclical encoding for month (captures seasonality smoothly)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

        # Cyclical encoding for day of week
        df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

        # Rolling average (7-day) — use shift to avoid data leakage
        df["rolling_avg_7"] = df["demand"].shift(1).rolling(window=7, min_periods=1).mean()
        df["rolling_avg_7"] = df["rolling_avg_7"].fillna(df["demand"].mean())

        # Rolling average (30-day)
        df["rolling_avg_30"] = df["demand"].shift(1).rolling(window=30, min_periods=1).mean()
        df["rolling_avg_30"] = df["rolling_avg_30"].fillna(df["demand"].mean())

        feature_cols = [
            "day_of_week", "month", "day_of_month", "is_weekend",
            "trend", "month_sin", "month_cos", "dow_sin", "dow_cos",
            "rolling_avg_7", "rolling_avg_30"
        ]

        return df, feature_cols

    def train(self, data):
        """
        Train the demand prediction model.

        Args:
            data: list of dicts with keys 'date', 'demand'
                  OR a pandas DataFrame

        Returns:
            dict with training metrics
        """
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if len(df) < 14:
            return {"error": "Need at least 14 data points to train"}

        df, feature_cols = self._engineer_features(df)

        X = df[feature_cols].values
        y = df["demand"].values

        # Split: use last 20% as validation
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True

        # Generate predictions for metrics
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_val = self.model.predict(X_val_scaled)

        # Residual std on validation set for confidence intervals
        val_residuals = y_val - y_pred_val
        self._residual_std = float(np.std(val_residuals))

        self.metrics = {
            "r2_score":       round(r2_score(y_val, y_pred_val), 4),
            "mae":            round(mean_absolute_error(y_val, y_pred_val), 2),
            "rmse":           round(math.sqrt(mean_squared_error(y_val, y_pred_val)), 2),
            "train_r2":       round(r2_score(y_train, y_pred_train), 4),
            "train_samples":  len(X_train),
            "val_samples":    len(X_val),
            "total_samples":  len(X),
            "residual_std":   round(self._residual_std, 2),
        }

        # Store last known values for prediction
        self._last_date     = df["date"].max()
        self._last_trend    = df["trend"].max()
        self._last_rolling_7  = df["rolling_avg_7"].iloc[-1]
        self._last_rolling_30 = df["rolling_avg_30"].iloc[-1]
        self._mean_demand   = df["demand"].mean()

        return self.metrics

    def train_per_product(self, product_data):
        """
        Train individual models for each product category.

        Args:
            product_data: list of dicts with keys 'date', 'product_id', 'product_name', 'demand'

        Returns:
            dict with per-product metrics
        """
        df = pd.DataFrame(product_data)
        df["date"] = pd.to_datetime(df["date"])

        product_metrics = {}
        products = df.groupby(["product_id", "product_name"])

        for (pid, pname), group in products:
            daily = group.groupby("date").agg({"demand": "sum"}).reset_index()
            daily = daily.sort_values("date").reset_index(drop=True)

            if len(daily) < 14:
                continue

            model = LinearRegression()
            scaler = StandardScaler()

            engineered, feature_cols = self._engineer_features(daily)
            X = engineered[feature_cols].values
            y = engineered["demand"].values

            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)

            model.fit(X_train_scaled, y_train)
            y_pred_val = model.predict(X_val_scaled)

            val_residuals = y_val - y_pred_val
            residual_std = float(np.std(val_residuals))

            self._product_models[pid] = {
                "model": model,
                "scaler": scaler,
                "last_date": engineered["date"].max(),
                "last_trend": engineered["trend"].max(),
                "last_rolling_7": engineered["rolling_avg_7"].iloc[-1],
                "last_rolling_30": engineered["rolling_avg_30"].iloc[-1],
                "mean_demand": daily["demand"].mean(),
                "residual_std": residual_std,
                "product_name": pname,
            }

            product_metrics[pid] = {
                "product_name": pname,
                "r2_score": round(r2_score(y_val, y_pred_val), 4),
                "mae": round(mean_absolute_error(y_val, y_pred_val), 2),
                "rmse": round(math.sqrt(mean_squared_error(y_val, y_pred_val)), 2),
                "samples": len(X),
                "mean_demand": round(float(daily["demand"].mean()), 1),
                "latest_demand": int(daily["demand"].iloc[-1]),
            }

        return product_metrics

    def predict_by_product(self, days_ahead=30):
        """
        Predict demand per product for the next N days.

        Returns:
            dict mapping product_id to list of predictions
        """
        if not self._product_models:
            return {"error": "Per-product models not trained. Call train_per_product() first."}

        result = {}

        for pid, pm in self._product_models.items():
            model = pm["model"]
            scaler = pm["scaler"]
            predictions = []
            rolling_7_buffer = [pm["last_rolling_7"]] * 7
            rolling_30_buffer = [pm["last_rolling_30"]] * 30
            sigma = pm["residual_std"] if pm["residual_std"] > 0 else pm["mean_demand"] * 0.08

            for i in range(1, days_ahead + 1):
                future_date = pm["last_date"] + timedelta(days=i)
                day_of_week = future_date.weekday()
                month = future_date.month
                day_of_month = future_date.day
                is_weekend = 1 if day_of_week >= 5 else 0
                trend = pm["last_trend"] + i

                month_sin = np.sin(2 * np.pi * month / 12)
                month_cos = np.cos(2 * np.pi * month / 12)
                dow_sin = np.sin(2 * np.pi * day_of_week / 7)
                dow_cos = np.cos(2 * np.pi * day_of_week / 7)

                rolling_avg_7 = np.mean(rolling_7_buffer[-7:])
                rolling_avg_30 = np.mean(rolling_30_buffer[-30:])

                features = np.array([[
                    day_of_week, month, day_of_month, is_weekend,
                    trend, month_sin, month_cos, dow_sin, dow_cos,
                    rolling_avg_7, rolling_avg_30
                ]])

                pred = max(0, round(float(model.predict(scaler.transform(features))[0]), 1))
                ci_width = sigma * (1.0 + i * 0.03)

                predictions.append({
                    "date": future_date.strftime("%Y-%m-%d"),
                    "predicted_demand": pred,
                    "upper": round(pred + ci_width, 1),
                    "lower": round(max(0, pred - ci_width), 1),
                    "day_of_week": future_date.strftime("%A"),
                })

                rolling_7_buffer.append(pred)
                rolling_30_buffer.append(pred)

            result[pid] = {
                "product_name": pm["product_name"],
                "predictions": predictions,
            }

        return result

    def predict(self, days_ahead=30):
        """
        Predict demand for the next N days.

        Returns:
            list of dicts with 'date', 'predicted_demand', 'upper', 'lower'
        """
        if not self.is_trained:
            return {"error": "Model not trained yet. Call train() first."}

        predictions = []
        rolling_7_buffer  = [self._last_rolling_7]  * 7
        rolling_30_buffer = [self._last_rolling_30] * 30
        sigma = self._residual_std if self._residual_std > 0 else self._mean_demand * 0.08

        for i in range(1, days_ahead + 1):
            future_date  = self._last_date + timedelta(days=i)
            day_of_week  = future_date.weekday()
            month        = future_date.month
            day_of_month = future_date.day
            is_weekend   = 1 if day_of_week >= 5 else 0
            trend        = self._last_trend + i

            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            dow_sin   = np.sin(2 * np.pi * day_of_week / 7)
            dow_cos   = np.cos(2 * np.pi * day_of_week / 7)

            rolling_avg_7  = np.mean(rolling_7_buffer[-7:])
            rolling_avg_30 = np.mean(rolling_30_buffer[-30:])

            features = np.array([[
                day_of_week, month, day_of_month, is_weekend,
                trend, month_sin, month_cos, dow_sin, dow_cos,
                rolling_avg_7, rolling_avg_30
            ]])

            pred = max(0, round(float(self.model.predict(self.scaler.transform(features))[0]), 1))

            # Widen confidence interval gradually as we forecast further out
            ci_width = sigma * (1.0 + i * 0.03)

            predictions.append({
                "date":             future_date.strftime("%Y-%m-%d"),
                "predicted_demand": pred,
                "upper":            round(pred + ci_width, 1),
                "lower":            round(max(0, pred - ci_width), 1),
                "day_of_week":      future_date.strftime("%A"),
            })

            rolling_7_buffer.append(pred)
            rolling_30_buffer.append(pred)

        return predictions

    def get_metrics(self):
        """Return current model metrics."""
        return self.metrics if self.metrics else {"error": "Model not trained yet"}

    def get_festival_annotations(self, start_date=None, end_date=None):
        """Return festival annotations within a date range for chart overlays."""
        annotations = []
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=365)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # Check both years in range
        for year in range(start_date.year, end_date.year + 1):
            for fest in FESTIVAL_ANNOTATIONS:
                try:
                    fest_date = datetime(year, fest["month"], fest["day"])
                    if start_date <= fest_date <= end_date:
                        annotations.append({
                            "date": fest_date.strftime("%Y-%m-%d"),
                            "name": fest["name"],
                            "impact": fest["impact"],
                            "category": fest["category"],
                        })
                except ValueError:
                    continue

        # Add monsoon period markers
        for year in range(start_date.year, end_date.year + 1):
            monsoon_start = datetime(year, 6, 1)
            monsoon_end = datetime(year, 9, 30)
            if monsoon_start <= end_date and monsoon_end >= start_date:
                annotations.append({
                    "date": monsoon_start.strftime("%Y-%m-%d"),
                    "name": "Monsoon Season Start",
                    "impact": "high",
                    "category": "weather",
                    "end_date": monsoon_end.strftime("%Y-%m-%d"),
                })

        return sorted(annotations, key=lambda x: x["date"])

    def get_seasonal_context(self):
        """Return current seasonal context for India supply chain."""
        now = datetime.now()
        month = now.month

        season = "normal"
        season_label = "Normal Operations"
        impact = "none"

        if month in MONSOON_MONTHS:
            season = "monsoon"
            season_label = "Monsoon Season (Jun-Sep)"
            impact = "high"
        elif month in FESTIVE_QUARTER_MONTHS:
            season = "festive"
            season_label = "Festive Quarter (Oct-Nov)"
            impact = "very_high"
        elif month in FISCAL_Q4_MONTHS:
            season = "fiscal_q4"
            season_label = "Fiscal Q4 Surge (Jan-Mar)"
            impact = "medium"
        elif month in [4, 5]:
            season = "summer"
            season_label = "Summer Peak (Apr-May)"
            impact = "low"
        elif month == 12:
            season = "year_end"
            season_label = "Year-End / Holiday Season"
            impact = "high"

        # Find upcoming festivals
        upcoming = []
        for fest in FESTIVAL_ANNOTATIONS:
            try:
                fest_date = datetime(now.year, fest["month"], fest["day"])
                if fest_date < now:
                    fest_date = datetime(now.year + 1, fest["month"], fest["day"])
                days_until = (fest_date - now).days
                if days_until <= 60:
                    upcoming.append({
                        "name": fest["name"],
                        "date": fest_date.strftime("%Y-%m-%d"),
                        "days_until": days_until,
                        "impact": fest["impact"],
                    })
            except ValueError:
                continue

        upcoming.sort(key=lambda x: x["days_until"])

        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S"),
            "season": season,
            "season_label": season_label,
            "impact": impact,
            "month": month,
            "quarter": f"Q{(month - 1) // 3 + 1}",
            "fiscal_quarter": f"FY Q{((month - 4) % 12) // 3 + 1}",
            "upcoming_festivals": upcoming[:5],
            "is_monsoon": month in MONSOON_MONTHS,
            "is_festive": month in FESTIVE_QUARTER_MONTHS,
            "is_fiscal_q4": month in FISCAL_Q4_MONTHS,
        }
