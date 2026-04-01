/**
 * app.js — SupplyChain AI v3.0 Production Frontend
 * ===================================================
 * Handles:
 * - Scrollytelling landing page animations
 * - Dashboard API integration + Chart.js + Leaflet.js
 * - Quick Demo (one-click guided flow)
 * - Toast notifications + Demo progress tracker
 * - RAG provenance display with retrieval scores
 * - Animated metric transitions
 * - Offline detection & fallback data
 * - Robust error handling
 */

// ═══════════════════════════════════════════════════════════════
//                     CONFIGURATION
// ═══════════════════════════════════════════════════════════════

const API_BASE = window.location.origin + "/api";
let demandChart = null;
let clusterChart = null;
let riskChart = null;
let routeMap = null;
let mapLayers = { markers: [], routes: [], altRoutes: [] };
let isOnline = navigator.onLine;
let isDemoRunning = false;

// ═══════════════════════════════════════════════════════════════
//                    INITIALIZATION
// ═══════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initScrollObserver();
    initStatCounters();
    initOfflineDetection();
});

// ═══════════════════════════════════════════════════════════════
//               SCROLLYTELLING ANIMATIONS
// ═══════════════════════════════════════════════════════════════

function initParticles() {
    const field = document.getElementById("particle-field");
    if (!field) return;

    for (let i = 0; i < 40; i++) {
        const p = document.createElement("div");
        p.className = "particle";
        p.style.left = Math.random() * 100 + "%";
        p.style.animationDuration = (8 + Math.random() * 12) + "s";
        p.style.animationDelay = Math.random() * 8 + "s";
        p.style.width = (2 + Math.random() * 3) + "px";
        p.style.height = p.style.width;
        p.style.opacity = 0.2 + Math.random() * 0.4;
        if (Math.random() > 0.5) p.style.background = "rgba(139, 92, 246, 0.4)";
        field.appendChild(p);
    }
}

function initScrollObserver() {
    const sections = document.querySelectorAll(".scroll-section");
    if (!sections.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
            }
        });
    }, { threshold: 0.15, rootMargin: "0px 0px -50px 0px" });

    sections.forEach(section => observer.observe(section));
}

function initStatCounters() {
    const counters = document.querySelectorAll(".stat-number[data-target]");
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => observer.observe(c));
}

function animateCounter(el) {
    const target = parseInt(el.getAttribute("data-target"));
    const duration = 2000;
    const start = performance.now();
    const step = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(target * eased);
        if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

function scrollToSection(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
}

// ═══════════════════════════════════════════════════════════════
//              PAGE TRANSITIONS
// ═══════════════════════════════════════════════════════════════

function enterDashboard() {
    const landing = document.getElementById("landing-page");
    const dashboard = document.getElementById("dashboard-page");

    landing.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    landing.style.opacity = "0";
    landing.style.transform = "scale(0.98)";

    setTimeout(() => {
        landing.style.display = "none";
        dashboard.style.display = "block";
        dashboard.style.opacity = "0";
        dashboard.style.transition = "opacity 0.5s ease";

        requestAnimationFrame(() => {
            dashboard.style.opacity = "1";
            initMap();
            loadDashboard();
        });
    }, 500);
}

function exitDashboard() {
    const landing = document.getElementById("landing-page");
    const dashboard = document.getElementById("dashboard-page");

    dashboard.style.opacity = "0";
    setTimeout(() => {
        dashboard.style.display = "none";
        landing.style.display = "block";
        landing.style.opacity = "0";
        landing.style.transform = "scale(0.98)";
        requestAnimationFrame(() => {
            landing.style.opacity = "1";
            landing.style.transform = "scale(1)";
        });
    }, 400);
}

// ═══════════════════════════════════════════════════════════════
//              OFFLINE DETECTION
// ═══════════════════════════════════════════════════════════════

function initOfflineDetection() {
    const banner = document.getElementById("offline-banner");
    window.addEventListener("online", () => {
        isOnline = true;
        if (banner) banner.classList.add("hidden");
        showToast("success", "Back online! Connection restored.");
    });
    window.addEventListener("offline", () => {
        isOnline = false;
        if (banner) banner.classList.remove("hidden");
        showToast("error", "You are offline. Some features may be unavailable.");
    });
}

// ═══════════════════════════════════════════════════════════════
//                    MAP INITIALIZATION
// ═══════════════════════════════════════════════════════════════

function initMap() {
    if (routeMap) return;

    const container = document.getElementById("route-map");
    if (!container) return;

    routeMap = L.map("route-map", { zoomControl: true, attributionControl: false }).setView([22.0, 78.0], 5);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 18 }).addTo(routeMap);

    setTimeout(() => routeMap.invalidateSize(), 400);
}

// ═══════════════════════════════════════════════════════════════
//                   SAFE API FETCH
// ═══════════════════════════════════════════════════════════════

async function safeFetch(url, options = {}) {
    if (!isOnline) throw new Error("You are offline");

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    try {
        const response = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(timeout);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        clearTimeout(timeout);
        if (error.name === "AbortError") throw new Error("Request timed out");
        throw error;
    }
}

// ═══════════════════════════════════════════════════════════════
//                   TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════

function showToast(type, message, duration = 4000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const icons = { success: "✅", error: "❌", info: "ℹ️" };
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || "ℹ️"}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-out");
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ═══════════════════════════════════════════════════════════════
//                 ANIMATED METRIC UPDATE
// ═══════════════════════════════════════════════════════════════

function animateMetricValue(id, newValue) {
    const el = document.getElementById(id);
    if (!el) return;

    const numeric = parseInt(String(newValue).replace(/[,]/g, ""));
    if (isNaN(numeric)) {
        el.textContent = newValue;
        return;
    }

    const currentValue = parseInt(el.textContent.replace(/[,]/g, "")) || 0;
    const duration = 800;
    const start = performance.now();

    const step = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(currentValue + (numeric - currentValue) * eased);
        el.textContent = current.toLocaleString();
        if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

// ═══════════════════════════════════════════════════════════════
//                   DASHBOARD LOADING
// ═══════════════════════════════════════════════════════════════

async function loadDashboard() {
    showLoading("Loading AI dashboard data...");

    try {
        const data = await safeFetch(`${API_BASE}/dashboard-data`);

        if (!data.success) throw new Error(data.error || "Unknown error");

        updateSystemStatus(data.system_status);
        updateMetrics(data);
        updateDemandChart(data.demand_historical, data.demand_predictions);
        updateDemandMetrics(data.demand_metrics);
        updateSupplierClusters(data.suppliers);
        if (data.cluster_metrics) updateClusterMetrics(data.cluster_metrics);
        updateRouteMap(data.warehouses, data.default_route, data.alternative_route);
        updateRiskAlerts(data.current_risk);
        updateRiskChart(data.current_risk);
        updateOverallRisk(data.current_risk);

        document.getElementById("footer-timestamp").textContent =
            `Last updated: ${new Date().toLocaleTimeString()}`;

        hideLoading();
        showToast("success", "Dashboard loaded — all AI systems online");
    } catch (error) {
        console.error("Dashboard load error:", error);
        hideLoading();
        showErrorAlert("Failed to connect to backend. " + error.message);
        showToast("error", "Dashboard load failed: " + error.message);
    }
}

// ═══════════════════════════════════════════════════════════════
//                  SYSTEM STATUS
// ═══════════════════════════════════════════════════════════════

function updateSystemStatus(status) {
    const indicators = {
        "status-demand": status?.demand_trained,
        "status-cluster": status?.suppliers_clustered,
        "status-route": status?.routes_loaded,
        "status-rag": true,
    };
    for (const [id, active] of Object.entries(indicators)) {
        const el = document.getElementById(id);
        if (el) el.classList.toggle("active", !!active);
    }
}

// ═══════════════════════════════════════════════════════════════
//                    METRICS CARDS
// ═══════════════════════════════════════════════════════════════

function updateMetrics(data) {
    const riskScore = data.current_risk?.overall_risk_score || 0;
    animateMetricValue("metric-risk-value", Math.round(riskScore));
    setMetricTrend("metric-risk-trend", riskScore > 50 ? "↑ High" : "✓ Normal", riskScore > 50 ? "trend-down" : "trend-up");

    if (data.demand_predictions?.length > 0) {
        const avgDemand = Math.round(data.demand_predictions.reduce((s, d) => s + d.predicted_demand, 0) / data.demand_predictions.length);
        animateMetricValue("metric-demand-value", avgDemand);
        setMetricTrend("metric-demand-trend", "📈 Predicted", "trend-neutral");
    }

    if (data.suppliers) {
        animateMetricValue("metric-suppliers-value", data.suppliers.length);
        const low = data.suppliers.filter(s => s.cluster_label === "Low Risk").length;
        setMetricTrend("metric-suppliers-trend", `${low} Low Risk`, "trend-up");
    }

    if (data.default_route && !data.default_route.error) {
        animateMetricValue("metric-route-value", data.default_route.total_distance_km);
        setMetricTrend("metric-route-trend", `${data.default_route.total_time_hours}h`, "trend-neutral");
    }

    const alertCount = data.current_risk?.alerts?.length || 0;
    animateMetricValue("metric-alerts-value", alertCount);
    setMetricTrend("metric-alerts-trend", alertCount > 0 ? `${alertCount} Active` : "✓ Clear", alertCount > 0 ? "trend-down" : "trend-up");
}

function setMetric(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function setMetricTrend(id, text, cls) {
    const el = document.getElementById(id);
    if (el) { el.textContent = text; el.className = "metric-trend " + cls; }
}

// ═══════════════════════════════════════════════════════════════
//                 DEMAND PREDICTION CHART
// ═══════════════════════════════════════════════════════════════

function updateDemandChart(historical, predictions) {
    const canvas = document.getElementById("demand-chart");
    if (!canvas) return;

    const histLabels = (historical || []).map(d => d.date);
    const histValues = (historical || []).map(d => d.demand);
    const predLabels = (predictions || []).map(d => d.date);
    const predValues = (predictions || []).map(d => d.predicted_demand);

    const allLabels = [...histLabels, ...predLabels];
    const displayLabels = allLabels.map(d => {
        const date = new Date(d);
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    });

    const histData = [...histValues, ...new Array(predLabels.length).fill(null)];
    const predData = [
        ...new Array(Math.max(0, histLabels.length - 1)).fill(null),
        histValues.length > 0 ? histValues[histValues.length - 1] : null,
        ...predValues
    ];

    if (demandChart) demandChart.destroy();

    demandChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: displayLabels,
            datasets: [
                { label: "Historical Demand", data: histData, borderColor: "#3b82f6", backgroundColor: "rgba(59,130,246,0.1)", borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0, pointHoverRadius: 4 },
                { label: "AI Predicted Demand", data: predData, borderColor: "#8b5cf6", backgroundColor: "rgba(139,92,246,0.1)", borderWidth: 2, borderDash: [6, 3], fill: true, tension: 0.4, pointRadius: 0, pointHoverRadius: 4 },
            ],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "#94a3b8", font: { family: "Inter", size: 11 }, usePointStyle: true, pointStyle: "circle" } },
                tooltip: { backgroundColor: "rgba(17,24,39,0.95)", titleColor: "#f0f4ff", bodyColor: "#94a3b8", borderColor: "rgba(255,255,255,0.1)", borderWidth: 1, cornerRadius: 8 },
            },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#64748b", font: { family: "Inter", size: 10 }, maxTicksLimit: 12 } },
                y: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#64748b", font: { family: "Inter", size: 10 } } },
            },
        },
    });
}

function updateDemandMetrics(metrics) {
    if (!metrics) return;
    document.getElementById("demand-r2").textContent = metrics.r2_score ?? "--";
    document.getElementById("demand-mae").textContent = metrics.mae ?? "--";
    document.getElementById("demand-samples").textContent = metrics.total_samples ?? "--";
}

// ═══════════════════════════════════════════════════════════════
//              SUPPLIER CLUSTERING CHART
// ═══════════════════════════════════════════════════════════════

function updateSupplierClusters(suppliers) {
    if (!suppliers?.length) return;

    const canvas = document.getElementById("cluster-chart");
    if (!canvas) return;

    const clusters = {};
    const colors = {
        "Low Risk": { bg: "rgba(16,185,129,0.6)", border: "#10b981" },
        "Medium Risk": { bg: "rgba(245,158,11,0.6)", border: "#f59e0b" },
        "High Risk": { bg: "rgba(244,63,94,0.6)", border: "#f43f5e" },
    };

    suppliers.forEach(s => {
        const label = s.cluster_label || "Unknown";
        if (!clusters[label]) clusters[label] = [];
        clusters[label].push(s);
    });

    const datasets = Object.entries(clusters).map(([label, items]) => ({
        label, data: items.map(s => ({ x: s.failure_rate * 100, y: s.delivery_time_days, name: s.name })),
        backgroundColor: colors[label]?.bg || "rgba(100,116,139,0.6)",
        borderColor: colors[label]?.border || "#64748b",
        borderWidth: 2, pointRadius: 8, pointHoverRadius: 12,
    }));

    if (clusterChart) clusterChart.destroy();

    clusterChart = new Chart(canvas, {
        type: "scatter",
        data: { datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "#94a3b8", font: { family: "Inter", size: 11 }, usePointStyle: true } },
                tooltip: {
                    backgroundColor: "rgba(17,24,39,0.95)", titleColor: "#f0f4ff", bodyColor: "#94a3b8", borderColor: "rgba(255,255,255,0.1)", borderWidth: 1, cornerRadius: 8,
                    callbacks: { title: (items) => items[0]?.raw?.name || "", label: (item) => `Failure: ${item.raw.x.toFixed(1)}% | Delivery: ${item.raw.y.toFixed(1)}d` },
                },
            },
            scales: {
                x: { title: { display: true, text: "Failure Rate (%)", color: "#64748b", font: { family: "Inter", size: 11 } }, grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#64748b", font: { family: "Inter", size: 10 } } },
                y: { title: { display: true, text: "Delivery Time (days)", color: "#64748b", font: { family: "Inter", size: 11 } }, grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#64748b", font: { family: "Inter", size: 10 } } },
            },
        },
    });

    updateClusterLegend(clusters);
}

function updateClusterLegend(clusters) {
    const container = document.getElementById("cluster-legend");
    if (!container) return;
    container.innerHTML = "";

    const order = ["Low Risk", "Medium Risk", "High Risk"];
    const dotClass = { "Low Risk": "low", "Medium Risk": "medium", "High Risk": "high" };

    for (const label of order) {
        const items = clusters[label];
        if (!items) continue;
        const avgFail = (items.reduce((s, i) => s + i.failure_rate, 0) / items.length * 100).toFixed(1);
        const avgDel = (items.reduce((s, i) => s + i.delivery_time_days, 0) / items.length).toFixed(1);

        const div = document.createElement("div");
        div.className = "cluster-item";
        div.innerHTML = `<span class="cluster-dot ${dotClass[label] || ''}"></span><div class="cluster-info"><span class="cluster-name">${label}</span><span class="cluster-detail">Fail: ${avgFail}% | Del: ${avgDel}d</span></div><span class="cluster-count">${items.length}</span>`;
        container.appendChild(div);
    }
}

function updateClusterMetrics(metrics) {
    if (!metrics) return;
    const silEl = document.getElementById("cluster-silhouette");
    if (silEl) silEl.textContent = metrics.silhouette_score ? metrics.silhouette_score.toFixed(3) : "--";
    const countEl = document.getElementById("cluster-count");
    if (countEl && metrics.n_clusters) countEl.textContent = metrics.n_clusters;
}

// ═══════════════════════════════════════════════════════════════
//                    ROUTE MAP
// ═══════════════════════════════════════════════════════════════

function updateRouteMap(warehouses, optimalRoute, altRoute) {
    if (!routeMap) return;

    mapLayers.markers.forEach(m => routeMap.removeLayer(m));
    mapLayers.routes.forEach(r => routeMap.removeLayer(r));
    mapLayers.altRoutes.forEach(r => routeMap.removeLayer(r));
    mapLayers = { markers: [], routes: [], altRoutes: [] };

    if (warehouses) {
        warehouses.forEach(wh => {
            const isSource = optimalRoute?.path?.[0] === wh.id;
            const isDest = optimalRoute?.path?.[optimalRoute.path.length - 1] === wh.id;
            let cls = "warehouse-marker";
            if (isSource) cls += " warehouse-marker-source";
            else if (isDest) cls += " warehouse-marker-dest";

            const icon = L.divIcon({ className: cls, iconSize: isSource || isDest ? [16, 16] : [12, 12], iconAnchor: isSource || isDest ? [8, 8] : [6, 6] });
            const marker = L.marker([wh.lat, wh.lng], { icon }).addTo(routeMap)
                .bindPopup(`<div class="popup-title">${wh.name}</div><div class="popup-detail">📍 ${wh.city}</div>${wh.capacity ? `<div class="popup-detail">📦 Capacity: ${wh.capacity}</div>` : ''}${isSource ? '<div class="popup-detail" style="color:#10b981">🟢 SOURCE</div>' : ''}${isDest ? '<div class="popup-detail" style="color:#f43f5e">🔴 DESTINATION</div>' : ''}`);
            mapLayers.markers.push(marker);
        });
    }

    if (altRoute?.path_coordinates && !altRoute.error) {
        const coords = altRoute.path_coordinates.map(p => [p.lat, p.lng]);
        const line = L.polyline(coords, { color: "#f59e0b", weight: 3, opacity: 0.5, dashArray: "8, 8" }).addTo(routeMap)
            .bindPopup(`<div class="popup-title">🟡 Alternative</div><div class="popup-detail">Dist: ${altRoute.total_distance_km} km | Time: ${altRoute.total_time_hours}h</div>`);
        mapLayers.altRoutes.push(line);
    }

    if (optimalRoute?.path_coordinates && !optimalRoute.error) {
        const coords = optimalRoute.path_coordinates.map(p => [p.lat, p.lng]);
        const glow = L.polyline(coords, { color: "#3b82f6", weight: 10, opacity: 0.2 }).addTo(routeMap);
        const line = L.polyline(coords, { color: "#3b82f6", weight: 4, opacity: 0.9 }).addTo(routeMap)
            .bindPopup(`<div class="popup-title">🔵 Optimal Route</div><div class="popup-detail">Path: ${optimalRoute.path_names?.join(" → ")}</div><div class="popup-detail">Dist: ${optimalRoute.total_distance_km} km | Time: ${optimalRoute.total_time_hours}h</div><div class="popup-detail">Cost: ₹${optimalRoute.total_cost?.toLocaleString()}</div>`);
        mapLayers.routes.push(line, glow);

        document.getElementById("route-distance").textContent = `${optimalRoute.total_distance_km} km`;
        document.getElementById("route-time").textContent = `${optimalRoute.total_time_hours} hrs`;
        document.getElementById("route-cost").textContent = `₹${optimalRoute.total_cost?.toLocaleString()}`;
        document.getElementById("route-stops").textContent = optimalRoute.num_stops;

        routeMap.fitBounds(L.latLngBounds(coords).pad(0.15));
    }
}

// ═══════════════════════════════════════════════════════════════
//                  RISK ALERTS + RAG PROVENANCE
// ═══════════════════════════════════════════════════════════════

function updateRiskAlerts(riskData) {
    const container = document.getElementById("alerts-container");
    if (!container || !riskData) return;
    container.innerHTML = "";

    const alerts = riskData.alerts || [];

    if (alerts.length === 0) {
        container.innerHTML = `<div class="alert-card alert-info"><div class="alert-header"><span class="alert-icon">✅</span><span class="alert-title">All Systems Normal</span></div><p class="alert-message">No significant risks detected. Supply chain operating within normal parameters.</p></div>`;
        return;
    }

    alerts.forEach(alert => {
        const card = document.createElement("div");
        card.className = `alert-card alert-${alert.severity}`;
        card.innerHTML = `<div class="alert-header"><span class="alert-icon">${getSeverityIcon(alert.severity)}</span><span class="alert-title">${alert.title}</span></div><p class="alert-message">${alert.message}</p><div class="alert-meta"><span class="alert-severity severity-${alert.severity}">${alert.severity}</span><span>Score: ${alert.score}/100</span><span>${alert.category}</span></div>`;
        container.appendChild(card);
    });

    if (riskData.rag_insights) addRAGInsightCard(container, riskData.rag_insights);
}

function addRAGInsightCard(container, ragInsight) {
    const card = document.createElement("div");
    card.className = "alert-card alert-info";

    let recsHtml = "";
    if (ragInsight.recommendations?.length) {
        recsHtml = `<ul class="alert-recommendations">${ragInsight.recommendations.map(r => `<li>${r}</li>`).join("")}</ul>`;
    }

    // Build RAG provenance section showing retrieval sources with scores
    let provenanceHtml = "";
    if (ragInsight.retrieved_context?.length) {
        const sourcesHtml = ragInsight.retrieved_context.map(ctx => {
            const hasScores = ctx.cosine_score !== undefined;
            const scoreDisplay = hasScores
                ? `<div class="rag-source-scores">
                     <span class="score-cosine">cos: ${ctx.cosine_score}</span>
                     <span class="score-bm25">bm25: ${ctx.bm25_score || "–"}</span>
                     <span class="score-hybrid">${ctx.hybrid_score || ctx.cosine_score}</span>
                   </div>`
                : `<span class="score-hybrid">${ctx.relevance || "–"}</span>`;

            const title = ctx.doc_title || ctx.category;
            const docId = ctx.doc_id || "";

            return `<div class="rag-source-item">
                <span class="rag-source-name">${docId ? docId + ": " : ""}${title}</span>
                ${scoreDisplay}
            </div>`;
        }).join("");

        provenanceHtml = `
            <div class="rag-provenance">
                <div class="rag-provenance-title">📄 Retrieval Sources (${ragInsight.sources_used} documents)</div>
                ${sourcesHtml}
            </div>`;
    }

    // Pipeline info badge
    let pipelineBadge = "";
    if (ragInsight.retrieval_pipeline) {
        const rp = ragInsight.retrieval_pipeline;
        pipelineBadge = `<div class="rag-pipeline-badge">⚙️ ${rp.vectorizer || "TF-IDF"} → ${rp.reranker || "BM25"} → ${rp.scoring || "Hybrid"} | ${rp.chunks_searched || "?"} chunks searched</div>`;
    }

    card.innerHTML = `
        <div class="alert-rag-section">
            <div class="alert-rag-title">🤖 RAG Intelligence Report</div>
            <p class="alert-rag-text">${ragInsight.analysis || ragInsight.alert}</p>
            ${recsHtml}
            <div class="alert-meta" style="margin-top:8px">
                <span>Confidence: ${(ragInsight.confidence * 100).toFixed(0)}%</span>
                <span>Sources: ${ragInsight.sources_used}</span>
                <span>Impact: ${ragInsight.impact_type || "N/A"}</span>
            </div>
            ${provenanceHtml}
            ${pipelineBadge}
        </div>`;
    container.appendChild(card);
}

function getSeverityIcon(sev) {
    return { critical: "🔴", high: "🚨", medium: "⚠️", low: "ℹ️" }[sev] || "ℹ️";
}

// ═══════════════════════════════════════════════════════════════
//                   RISK CHART
// ═══════════════════════════════════════════════════════════════

function updateRiskChart(riskData) {
    const canvas = document.getElementById("risk-chart");
    if (!canvas || !riskData) return;

    const factors = riskData.risk_factors || [];
    const labels = factors.map(f => f.category.charAt(0).toUpperCase() + f.category.slice(1));
    const scores = factors.map(f => f.score);
    const bgColors = factors.map(f => f.score >= 75 ? "rgba(220,38,38,0.8)" : f.score >= 50 ? "rgba(244,63,94,0.8)" : f.score >= 25 ? "rgba(245,158,11,0.8)" : "rgba(16,185,129,0.8)");
    const borderColors = factors.map(f => f.score >= 75 ? "#dc2626" : f.score >= 50 ? "#f43f5e" : f.score >= 25 ? "#f59e0b" : "#10b981");

    if (riskChart) riskChart.destroy();

    riskChart = new Chart(canvas, {
        type: "bar",
        data: { labels, datasets: [{ label: "Risk Score", data: scores, backgroundColor: bgColors, borderColor: borderColors, borderWidth: 2, borderRadius: 6, barPercentage: 0.6 }] },
        options: {
            responsive: true, maintainAspectRatio: false, indexAxis: "y",
            plugins: { legend: { display: false }, tooltip: { backgroundColor: "rgba(17,24,39,0.95)", titleColor: "#f0f4ff", bodyColor: "#94a3b8", borderColor: "rgba(255,255,255,0.1)", borderWidth: 1, cornerRadius: 8, callbacks: { label: (item) => `Risk Score: ${item.raw}/100` } } },
            scales: {
                x: { max: 100, grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#64748b", font: { family: "Inter", size: 10 } } },
                y: { grid: { display: false }, ticks: { color: "#94a3b8", font: { family: "Inter", size: 11, weight: "bold" } } },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════
//                 OVERALL RISK BADGE
// ═══════════════════════════════════════════════════════════════

function updateOverallRisk(riskData) {
    if (!riskData) return;
    const score = riskData.overall_risk_score || 0;
    const severity = riskData.overall_severity || "low";
    const badge = document.getElementById("overall-risk-badge");
    const value = document.getElementById("overall-risk-value");
    if (badge) badge.className = `risk-badge risk-${severity}`;
    if (value) {
        animateMetricValue("overall-risk-value", Math.round(score));
        value.className = `risk-value risk-${severity}`;
    }
}

// ═══════════════════════════════════════════════════════════════
//              DISRUPTION SIMULATION
// ═══════════════════════════════════════════════════════════════

async function simulateDisruption(type, location) {
    const sourceId = parseInt(document.getElementById("route-source").value) || 1;
    const destId = parseInt(document.getElementById("route-dest").value) || 5;

    const btn = document.querySelector(`[onclick*="${type}"]`);
    if (btn) btn.classList.add("simulating");

    showLoading(`Simulating ${type} disruption in ${location}...`);

    try {
        const data = await safeFetch(`${API_BASE}/simulate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type, location, source_id: sourceId, dest_id: destId }),
        });

        if (!data.success) throw new Error(data.error || "Simulation failed");

        updateRiskAlerts(data.risk_assessment);
        updateRiskChart(data.risk_assessment);
        updateOverallRisk(data.risk_assessment);
        updateMetricsFromSimulation(data);

        if (data.all_warehouses) updateRouteMap(data.all_warehouses, data.optimal_route, data.alternative_route);
        if (data.decisions) updateDecisions(data.decisions);
        if (data.cluster_metrics) updateClusterMetrics(data.cluster_metrics);

        if (data.rag_intelligence) {
            const container = document.getElementById("alerts-container");
            if (container) addRAGInsightCard(container, data.rag_intelligence);
        }

        document.getElementById("footer-timestamp").textContent = `Simulation: ${type} @ ${location} — ${new Date().toLocaleTimeString()}`;
        hideLoading();
        showToast("success", `${type.charAt(0).toUpperCase() + type.slice(1)} simulation complete — ${data.risk_assessment?.alerts?.length || 0} alerts generated`);
    } catch (error) {
        console.error("Simulation error:", error);
        hideLoading();
        showErrorAlert(`Simulation failed: ${error.message}`);
        showToast("error", `Simulation failed: ${error.message}`);
    } finally {
        if (btn) btn.classList.remove("simulating");
    }
}

function updateMetricsFromSimulation(data) {
    if (data.risk_assessment) {
        const score = data.risk_assessment.overall_risk_score || 0;
        animateMetricValue("metric-risk-value", Math.round(score));
        setMetricTrend("metric-risk-trend", score >= 50 ? "⚠️ Elevated" : "✓ Normal", score >= 50 ? "trend-down" : "trend-up");
        const count = data.risk_assessment.alerts?.length || 0;
        animateMetricValue("metric-alerts-value", count);
        setMetricTrend("metric-alerts-trend", `${count} Active`, count > 2 ? "trend-down" : "trend-neutral");
    }
    if (data.optimal_route && !data.optimal_route.error) {
        animateMetricValue("metric-route-value", data.optimal_route.total_distance_km);
        setMetricTrend("metric-route-trend", `${data.optimal_route.total_time_hours}h`, "trend-neutral");
    }
}

// ═══════════════════════════════════════════════════════════════
//                🎯 QUICK DEMO (chains all 4 features)
// ═══════════════════════════════════════════════════════════════

async function runQuickDemo() {
    if (isDemoRunning) return;
    isDemoRunning = true;

    const demoBtn = document.getElementById("btn-quick-demo");
    if (demoBtn) demoBtn.classList.add("running");

    const progressBar = document.getElementById("demo-progress");
    if (progressBar) progressBar.classList.remove("hidden");

    // Reset all steps
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`demo-step-${i}`);
        if (step) step.className = "demo-step";
    }

    showLoading("Running Quick Demo — AI Pipeline executing...");

    try {
        // Animate steps sequentially
        setDemoStep(1, "active");
        showLoading("Step 1/4: Demand Prediction (Linear Regression)...");
        await sleep(400);

        setDemoStep(1, "complete");
        setDemoStep(2, "active");
        showLoading("Step 2/4: Risk Detection + RAG Intelligence...");
        await sleep(400);

        setDemoStep(2, "complete");
        setDemoStep(3, "active");
        showLoading("Step 3/4: Route Optimization (Dijkstra)...");
        await sleep(300);

        setDemoStep(3, "complete");
        setDemoStep(4, "active");
        showLoading("Step 4/4: AI Decision Engine...");

        // Fire the actual API call
        const data = await safeFetch(`${API_BASE}/quick-demo`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                type: "storm",
                location: "Mumbai",
                source_id: 1,
                dest_id: 5,
            }),
        });

        if (!data.success) throw new Error("Quick Demo failed");

        // Update step statuses from actual results
        if (data.steps) {
            data.steps.forEach(step => {
                setDemoStep(step.step, step.status === "complete" ? "complete" : "error");
            });
        } else {
            setDemoStep(4, "complete");
        }

        // Update all dashboard panels with demo results
        if (data.demand) {
            updateDemandChart(data.demand.historical, data.demand.predictions);
            updateDemandMetrics(data.demand.metrics);
            if (data.demand.predictions?.length > 0) {
                const avgDemand = Math.round(data.demand.predictions.reduce((s, d) => s + d.predicted_demand, 0) / data.demand.predictions.length);
                animateMetricValue("metric-demand-value", avgDemand);
            }
        }

        if (data.suppliers) {
            updateSupplierClusters(data.suppliers);
            animateMetricValue("metric-suppliers-value", data.suppliers.length);
        }
        if (data.cluster_metrics) {
            updateClusterMetrics(data.cluster_metrics);
        }

        if (data.risk_assessment) {
            updateRiskAlerts(data.risk_assessment);
            updateRiskChart(data.risk_assessment);
            updateOverallRisk(data.risk_assessment);
            const riskScore = data.risk_assessment.overall_risk_score || 0;
            animateMetricValue("metric-risk-value", Math.round(riskScore));
            setMetricTrend("metric-risk-trend", riskScore >= 50 ? "⚠️ Elevated" : "✓ Normal", riskScore >= 50 ? "trend-down" : "trend-up");
            const alertCount = data.risk_assessment.alerts?.length || 0;
            animateMetricValue("metric-alerts-value", alertCount);
            setMetricTrend("metric-alerts-trend", `${alertCount} Active`, alertCount > 2 ? "trend-down" : "trend-neutral");
        }

        if (data.rag_intelligence) {
            const container = document.getElementById("alerts-container");
            if (container) addRAGInsightCard(container, data.rag_intelligence);
        }

        if (data.all_warehouses) {
            updateRouteMap(data.all_warehouses, data.optimal_route, data.alternative_route);
            if (data.optimal_route && !data.optimal_route.error) {
                animateMetricValue("metric-route-value", data.optimal_route.total_distance_km);
                setMetricTrend("metric-route-trend", `${data.optimal_route.total_time_hours}h`, "trend-neutral");
            }
        }

        if (data.decisions) updateDecisions(data.decisions);

        document.getElementById("footer-timestamp").textContent = `Quick Demo — Storm @ Mumbai — ${new Date().toLocaleTimeString()}`;

        hideLoading();

        const completedSteps = (data.steps || []).filter(s => s.status === "complete").length;
        showToast("success", `Quick Demo complete — ${completedSteps}/4 AI models executed successfully`);

    } catch (error) {
        console.error("Quick Demo error:", error);
        hideLoading();
        showErrorAlert("Quick Demo failed: " + error.message);
        showToast("error", "Quick Demo failed: " + error.message);

        for (let i = 1; i <= 4; i++) {
            const step = document.getElementById(`demo-step-${i}`);
            if (step && !step.classList.contains("complete")) {
                step.className = "demo-step error";
            }
        }
    } finally {
        isDemoRunning = false;
        if (demoBtn) demoBtn.classList.remove("running");
    }
}

function setDemoStep(stepNum, status) {
    const el = document.getElementById(`demo-step-${stepNum}`);
    if (el) el.className = `demo-step ${status}`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ═══════════════════════════════════════════════════════════════
//             ROUTE OPTIMIZATION
// ═══════════════════════════════════════════════════════════════

async function optimizeRoute() {
    const sourceId = parseInt(document.getElementById("route-source").value);
    const destId = parseInt(document.getElementById("route-dest").value);
    if (sourceId === destId) { showErrorAlert("Source and destination must be different!"); return; }

    showLoading("Optimizing route with Dijkstra's algorithm...");

    try {
        const data = await safeFetch(`${API_BASE}/optimize-route`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source_id: sourceId, dest_id: destId, find_alternative: true }),
        });

        if (!data.success) throw new Error(data.error || "Route optimization failed");

        updateRouteMap(data.warehouses, data.optimal_route, data.alternative_route);

        if (data.optimal_route && !data.optimal_route.error) {
            animateMetricValue("metric-route-value", data.optimal_route.total_distance_km);
            setMetricTrend("metric-route-trend", `${data.optimal_route.total_time_hours}h`, "trend-neutral");
        }

        hideLoading();
        showToast("success", `Route optimized: ${data.optimal_route?.path_names?.join(" → ")}`);
    } catch (error) {
        console.error("Route error:", error);
        hideLoading();
        showErrorAlert(`Route optimization failed: ${error.message}`);
        showToast("error", "Route optimization failed");
    }
}

// ═══════════════════════════════════════════════════════════════
//               DECISION ENGINE UI
// ═══════════════════════════════════════════════════════════════

function updateDecisions(decisionsData) {
    const container = document.getElementById("decisions-container");
    if (!container || !decisionsData) return;
    container.innerHTML = "";

    const decisions = decisionsData.decisions || [];

    if (decisions.length === 0) {
        container.innerHTML = `<div class="decision-card decision-info"><div class="decision-header"><span class="decision-icon">✅</span><h3 class="decision-title">No Action Required</h3><span class="decision-priority priority-low">low</span></div><p class="decision-description">All supply chain operations are within normal parameters.</p></div>`;
        return;
    }

    decisions.forEach((d, i) => {
        const card = document.createElement("div");
        card.className = "decision-card";
        card.style.animationDelay = `${i * 0.1}s`;

        let actionsHtml = "";
        if (d.action_items?.length) actionsHtml = `<ul class="decision-actions">${d.action_items.map(a => `<li>${a}</li>`).join("")}</ul>`;

        let ragHtml = "";
        if (d.rag_justification?.supporting_evidence) ragHtml = `<div class="decision-rag"><strong>🤖 RAG Evidence (Confidence: ${(d.rag_justification.confidence * 100).toFixed(0)}%)</strong><br>${d.rag_justification.supporting_evidence[0]?.substring(0, 150)}...</div>`;

        card.innerHTML = `<div class="decision-header"><span class="decision-icon">${getDecisionIcon(d.type)}</span><h3 class="decision-title">${d.title}</h3><span class="decision-priority priority-${d.priority}">${d.priority}</span></div><p class="decision-description">${d.description}</p><div class="decision-impact">💡 Impact: ${d.impact}</div>${actionsHtml}<div class="decision-savings">💰 ${d.estimated_cost_saving}</div>${ragHtml}`;
        container.appendChild(card);
    });
}

function getDecisionIcon(type) {
    return { emergency_protocol: "🔴", route_change: "🗺️", supplier_switch: "🏭", transport_mode_change: "🚚", inventory_increase: "📈", inventory_reduction: "📉", supplier_diversification: "⚠️", supplier_consolidation: "✅", route_optimization: "🗺️", steady_state: "📊", monitoring: "📋" }[type] || "📋";
}

// ═══════════════════════════════════════════════════════════════
//                 UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════

function showLoading(message) {
    const overlay = document.getElementById("loading-overlay");
    const sub = document.getElementById("loading-sub-text");
    if (overlay) overlay.classList.remove("hidden");
    if (sub) sub.textContent = message || "Processing...";
}

function hideLoading() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.classList.add("hidden");
}

function showErrorAlert(message) {
    const container = document.getElementById("alerts-container");
    if (!container) {
        console.error("Alert:", message);
        return;
    }
    const card = document.createElement("div");
    card.className = "alert-card alert-critical";
    card.innerHTML = `<div class="alert-header"><span class="alert-icon">❌</span><span class="alert-title">Error</span></div><p class="alert-message">${message}</p>`;
    container.prepend(card);
    setTimeout(() => { if (card.parentNode) card.remove(); }, 10000);
}
