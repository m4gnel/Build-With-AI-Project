import { useState, useEffect } from 'react';

export function useSupplyChainAPI() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = import.meta.env.VITE_API_BASE || '/api';

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/dashboard-data`);
      if (!res.ok) throw new Error('API failed');
      const json = await res.json();
      if (!json.success) throw new Error(json.error || 'Unknown error');
      setData(json);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch using default Chennai (4) to Mumbai (1) or vice versa to seed specific dashboard data.
    optimizeRoute(4, 1);
  }, []);

  const [isDemoRunning, setIsDemoRunning] = useState(false);

  const runQuickDemo = async () => {
    setIsDemoRunning(true);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/quick-demo`, { method: 'POST' });
      const json = await res.json();
      setData((prev: any) => ({
        ...prev,
        demand_predictions: json.demand?.predictions || prev?.demand_predictions,
        demand_metrics: json.demand?.metrics || prev?.demand_metrics,
        suppliers: json.suppliers || prev?.suppliers,
        cluster_metrics: json.cluster_metrics || prev?.cluster_metrics,
        current_risk: json.risk_assessment || prev?.current_risk,
        default_route: json.optimal_route || prev?.default_route,
        decisions: json.decisions || prev?.decisions,
        rag_info: json.rag_intelligence,
        system_status: {
          demand_trained: true,
          suppliers_clustered: true,
          routes_loaded: true
        }
      }));
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
      setIsDemoRunning(false);
    }
  };

  const simulateDisruption = async (type: string, location: string, sourceId: number = 1, destId: number = 5) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, location, source_id: sourceId, dest_id: destId })
      });
      await res.json();
      fetchDashboard();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const queryRAG = async (question: string) => {
    try {
      const res = await fetch(`${API_BASE}/rag-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      return await res.json();
    } catch (e) {
      console.error(e);
      return { success: false, error: 'Failed to contact AI Engine.' };
    }
  };

  const optimizeRoute = async (sourceId: number, destId: number) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/optimize-route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_id: sourceId, dest_id: destId })
      });
      const json = await res.json();
      if (json.success) {
        setData((prev: any) => ({
          ...prev,
          default_route: json.optimal_route,
          alternative_route: json.alternative_route || prev?.alternative_route,
          demand_historical: json.demand_historical || prev?.demand_historical,
          demand_predictions: json.demand_predictions || prev?.demand_predictions,
          demand_metrics: json.demand_metrics || prev?.demand_metrics,
          suppliers: json.suppliers || prev?.suppliers,
          cluster_metrics: json.cluster_metrics || prev?.cluster_metrics,
          current_risk: json.current_risk || prev?.current_risk,
          rag_info: json.rag_intelligence ? { analysis: json.rag_intelligence } : prev?.rag_info,
          system_status: {
            demand_trained: true,
            suppliers_clustered: true,
            routes_loaded: true
          }
        }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, isDemoRunning, runQuickDemo, simulateDisruption, optimizeRoute, fetchDashboard, queryRAG };
}
