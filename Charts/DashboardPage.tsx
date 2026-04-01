import React, { useState } from 'react';
import { useSupplyChainAPI } from '@/hooks/useSupplyChainAPI';
import { Card } from '@/components/ui/card';
import { Activity, Zap } from 'lucide-react';
import { Line, Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { MapVisualization } from '@/components/MapVisualization';

import { DashboardHeader } from '@/components/DashboardHeader';
import { SimulationBar } from '@/components/SimulationBar';
import { DemoOverlay } from '@/components/DemoOverlay';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const CITY_COORDS: Record<string, [number, number]> = {
  "Mumbai": [19.0760, 72.8777],
  "Delhi": [28.7041, 77.1025],
  "Bangalore": [12.9716, 77.5946],
  "Chennai": [13.0827, 80.2707],
  "Kolkata": [22.5726, 88.3639],
  "Hyderabad": [17.3850, 78.4867],
  "Pune": [18.5204, 73.8567],
  "Ahmedabad": [23.0225, 72.5714],
  "Jaipur": [26.9124, 75.7873],
  "Lucknow": [26.8467, 80.9462],
  "Kanpur": [26.4499, 80.3319],
  "Nagpur": [21.1458, 79.0882],
  "Indore": [22.7196, 75.8577],
  "Thane": [19.2183, 72.9781],
  "Bhopal": [23.2599, 77.4126],
  "Visakhapatnam": [17.6868, 83.2185],
  "Surat": [21.1702, 72.8311],
  "Patna": [25.5941, 85.1376],
  "Vadodara": [22.3072, 73.1812],
  "Varanasi": [25.3176, 82.9739]
};

export default function DashboardPage() {
  const { data, loading, isDemoRunning, runQuickDemo, simulateDisruption, optimizeRoute, fetchDashboard, queryRAG } = useSupplyChainAPI();
  const [chatInput, setChatInput] = useState('');
  const [chatResponse, setChatResponse] = useState<any>(null);
  const [isChatting, setIsChatting] = useState(false);
  const [predictionDate, setPredictionDate] = useState('');

  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    setIsChatting(true);
    const result = await queryRAG(chatInput);
    if (result && result.success) {
      setChatResponse(result);
    } else {
      setChatResponse({ text: "Agent unavailable. Check GEMINI_API_KEY.", error: true });
    }
    setChatInput('');
    setIsChatting(false);
  };

  const handleRoutePrediction = async () => {
    if (!data?.default_route?.path_names) return;
    setIsChatting(true);
    const pathString = data.default_route.path_names.join(" -> ");
    const dateContext = predictionDate ? ` specifically occurring around ${new Date(predictionDate).toLocaleString()}` : '';
    const query = `Based on global supply chain logistics, predict potential future risks and problems${dateContext} for the optimized delivery route travelling exactly through: ${pathString}. Provide a crisp, professional predictive analysis regarding exactly this route.`;
    
    // Simulate typing indicator in the input briefly
    setChatInput(`Analyzing Route: ${pathString}...`);
    
    const result = await queryRAG(query);
    if (result && result.success) {
      setChatResponse(result);
    } else {
      setChatResponse({ text: "Prediction Agent unavailable. Check GEMINI_API_KEY.", error: true });
    }
    setChatInput(''); // Clear simulated input
    setIsChatting(false);
  };

  if (loading && !data && !isDemoRunning) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-primary font-heading animate-pulse">
        <Activity className="w-12 h-12 mr-4" /> Initiating Neural Link...
      </div>
    );
  }

  // ── Demand Chart Data & Options ──────────────────────────────
  const historicalLabels = data?.demand_historical?.map((h: any) => h.date) || [];
  const predictionLabels = data?.demand_predictions?.map((p: any) => p.date) || [];
  const allDemandLabels = [...historicalLabels, ...predictionLabels];
  const historicalLen = historicalLabels.length;

  const demandData = {
    labels: allDemandLabels,
    datasets: [
      {
        label: 'Historical Demand',
        data: [...(data?.demand_historical?.map((h: any) => h.demand) || []), ...Array(predictionLabels.length).fill(null)],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.08)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 1.5,
      },
      {
        label: 'AI Predicted Demand',
        data: [...Array(historicalLen).fill(null), ...(data?.demand_predictions?.map((p: any) => p.predicted_demand) || [])],
        borderColor: '#a855f7',
        backgroundColor: 'rgba(168, 85, 247, 0.05)',
        borderDash: [6, 4],
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2,
      }
    ]
  };

  const demandOptions: any = {
    maintainAspectRatio: false,
    animation: { duration: 600 },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        align: 'start' as const,
        labels: {
          color: 'rgba(255,255,255,0.7)',
          usePointStyle: true,
          pointStyle: 'circle',
          boxWidth: 8,
          font: { size: 11 },
          padding: 20,
        }
      },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#fff',
        bodyColor: 'rgba(255,255,255,0.7)',
      }
    },
    scales: {
      x: {
        ticks: { color: 'rgba(255,255,255,0.35)', maxTicksLimit: 10, font: { size: 10 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        ticks: { color: 'rgba(255,255,255,0.35)', font: { size: 10 } },
        grid: { color: 'rgba(255,255,255,0.06)' },
      }
    }
  };

  // ── Cluster Chart Data & Options ─────────────────────────────
  const CLUSTER_COLORS: Record<string, string> = {
    "Low Risk":    "#10b981",
    "Medium Risk": "#f59e0b",
    "High Risk":   "#f43f5e",
  };

  const mapClusters = () => {
    if (!data?.suppliers) return { datasets: [] };
    const clusters: Record<string, any[]> = {};
    data.suppliers.forEach((s: any) => {
      const label = s.cluster_label || "Unknown";
      if (!clusters[label]) clusters[label] = [];
      clusters[label].push({
        x: parseFloat((s.failure_rate * 100).toFixed(2)),
        y: parseFloat(s.delivery_time_days)
      });
    });
    return {
      datasets: Object.entries(clusters).map(([label, items]) => ({
        label,
        data: items,
        backgroundColor: CLUSTER_COLORS[label] || '#64748b',
        pointRadius: 10,
        pointHoverRadius: 13,
      }))
    };
  };

  // Compute per-cluster summary for the sidebar legend
  const clusterSummary = (() => {
    if (!data?.suppliers) return [];
    const map: Record<string, { failRates: number[], deliveries: number[] }> = {};
    data.suppliers.forEach((s: any) => {
      const label = s.cluster_label || "Unknown";
      if (!map[label]) map[label] = { failRates: [], deliveries: [] };
      map[label].failRates.push(s.failure_rate * 100);
      map[label].deliveries.push(s.delivery_time_days);
    });
    return Object.entries(map).map(([label, vals]) => ({
      label,
      count: vals.failRates.length,
      avgFail: (vals.failRates.reduce((a, b) => a + b, 0) / vals.failRates.length).toFixed(1),
      avgDel:  (vals.deliveries.reduce((a, b) => a + b, 0) / vals.deliveries.length).toFixed(1),
      color: CLUSTER_COLORS[label] || '#64748b',
    }));
  })();

  const scatterOptions: any = {
    maintainAspectRatio: false,
    animation: { duration: 600 },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        align: 'start' as const,
        labels: {
          color: 'rgba(255,255,255,0.7)',
          usePointStyle: true,
          pointStyle: 'circle',
          boxWidth: 8,
          font: { size: 11 },
          padding: 16,
        }
      },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#fff',
        bodyColor: 'rgba(255,255,255,0.7)',
        callbacks: {
          label: (ctx: any) => `Fail: ${ctx.parsed.x.toFixed(1)}%  Del: ${ctx.parsed.y}d`
        }
      }
    },
    scales: {
      x: {
        title: { display: true, text: 'Failure Rate (%)', color: 'rgba(255,255,255,0.4)', font: { size: 11 } },
        ticks: { color: 'rgba(255,255,255,0.35)', font: { size: 10 } },
        grid:  { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        title: { display: true, text: 'Delivery Time (days)', color: 'rgba(255,255,255,0.4)', font: { size: 11 } },
        ticks: { color: 'rgba(255,255,255,0.35)', font: { size: 10 } },
        grid:  { color: 'rgba(255,255,255,0.05)' },
      }
    }
  };

  const routePath = (data?.default_route?.path_names || data?.default_route?.path || [])
    .map((node: any) => CITY_COORDS[node])
    .filter(Boolean);
  
  const altPath = (data?.alternative_route?.path_names || data?.alternative_route?.path || [])
    .map((node: any) => CITY_COORDS[node])
    .filter(Boolean);

  return (
    <div className="min-h-screen bg-black text-white p-6 font-sans relative">
      <DemoOverlay isDemoRunning={isDemoRunning} />
      
      <DashboardHeader data={data} loading={loading} onRefresh={fetchDashboard} />
      
      <SimulationBar 
        onQuickDemo={runQuickDemo} 
        onSimulate={simulateDisruption} 
        onOptimizeRoute={optimizeRoute} 
        loading={loading} 
      />

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
        <Card>
          <div className="p-6">
            <h4 className="text-white/50 text-sm mb-2 uppercase tracking-wider flex justify-between">
              Overall Risk 
              <span className={`text-xs ${(data?.current_risk?.overall_risk_score || 0) > 50 ? 'text-rose-500' : 'text-primary'}`}>
                {(data?.current_risk?.overall_risk_score || 0) > 50 ? '↑ High' : '✓ Normal'}
              </span>
            </h4>
            <div className={`text-5xl font-heading font-bold italic ${(data?.current_risk?.overall_risk_score || 0) > 50 ? 'text-rose-500' : 'text-primary'}`}>
              {Math.round(data?.current_risk?.overall_risk_score || 0)}
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h4 className="text-white/50 text-sm mb-2 uppercase tracking-wider flex justify-between">
              Avg Demand/Day
              <span className="text-xs text-white/50">↑ Predicted</span>
            </h4>
            <div className="text-5xl font-heading font-bold italic text-white line-clamp-1">
              {data?.demand_predictions ? Math.round(data.demand_predictions.reduce((s:number,d:any)=>s+d.predicted_demand,0)/data.demand_predictions.length) : '--'}
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h4 className="text-white/50 text-sm mb-2 uppercase tracking-wider flex justify-between">
              Active Suppliers
              <span className="text-xs text-primary">↑ Low Risk</span>
            </h4>
            <div className="text-5xl font-heading font-bold italic text-white line-clamp-1">
              {data?.suppliers?.length || '--'}
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6 break-words">
            <h4 className="text-white/50 text-sm mb-2 uppercase tracking-wider flex justify-between">
              Route KM 
              <span className="text-xs text-white/50">Optimal</span>
            </h4>
            <div className="text-5xl font-heading font-bold italic text-white">
              {data?.default_route ? data.default_route.total_distance_km : '--'}
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h4 className="text-white/50 text-sm mb-2 uppercase tracking-wider flex justify-between">
              Active Alerts
              <span className={`text-xs ${(data?.current_risk?.alerts?.length || 0) > 0 ? 'text-amber-500' : 'text-primary'}`}>
                {(data?.current_risk?.alerts?.length || 0) > 0 ? '↓ Active' : '✓ Clear'}
              </span>
            </h4>
            <div className={`text-5xl font-heading font-bold italic ${(data?.current_risk?.alerts?.length || 0) > 0 ? 'text-amber-500' : 'text-green-500'}`}>
              {data?.current_risk?.alerts?.length || 0}
            </div>
          </div>
        </Card>
      </div>

      {/* ── Charts Row ──────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

        {/* Demand Forecast Card */}
        <Card className="flex flex-col p-0 overflow-hidden border border-white/8" style={{ minHeight: 380 }}>
          {/* Card Header */}
          <div className="flex items-center gap-3 px-5 pt-5 pb-3 border-b border-white/5">
            <span className="text-lg">📈</span>
            <span className="font-bold text-white text-base tracking-tight">Demand Forecast</span>
            <span className="ml-auto text-[10px] font-semibold tracking-widest uppercase px-2 py-1 rounded border border-blue-500/30 text-blue-400 bg-blue-500/10">
              Supervised Learning
            </span>
          </div>

          {/* Chart */}
          <div className="flex-1 relative px-4 pt-2" style={{ minHeight: 260 }}>
            <Line data={demandData} options={demandOptions} />
          </div>

          {/* Bottom Metrics */}
          <div className="flex gap-6 px-5 py-3 border-t border-white/5 text-xs">
            <span className="text-white/40">R² Score: <span className="text-blue-400 font-bold">{data?.demand_metrics?.r2_score?.toFixed(4) ?? '—'}</span></span>
            <span className="text-white/40">MAE: <span className="text-blue-400 font-bold">{data?.demand_metrics?.mae?.toFixed(2) ?? '—'}</span></span>
            <span className="text-white/40">Samples: <span className="text-blue-400 font-bold">{(data?.demand_historical?.length ?? 0) + (data?.demand_predictions?.length ?? 0)}</span></span>
          </div>
        </Card>

        {/* Supplier Risk Clusters Card */}
        <Card className="flex flex-col p-0 overflow-hidden border border-white/8" style={{ minHeight: 380 }}>
          {/* Card Header */}
          <div className="flex items-center gap-3 px-5 pt-5 pb-3 border-b border-white/5">
            <span className="text-lg">📊</span>
            <span className="font-bold text-white text-base tracking-tight">Supplier Risk Clusters</span>
            <span className="ml-auto text-[10px] font-semibold tracking-widest uppercase px-2 py-1 rounded border border-emerald-500/30 text-emerald-400 bg-emerald-500/10">
              Unsupervised Learning
            </span>
          </div>

          {/* Chart + Legend Sidebar */}
          <div className="flex flex-1 gap-0" style={{ minHeight: 260 }}>
            {/* Scatter Chart */}
            <div className="flex-1 relative px-3 pt-2">
              <Scatter data={mapClusters()} options={scatterOptions} />
            </div>

            {/* Cluster Summary Legend */}
            <div className="flex flex-col gap-2 justify-center pr-4 pl-2 min-w-[140px]">
              {clusterSummary.map((c) => (
                <div key={c.label} className="bg-white/5 border border-white/8 rounded-lg px-3 py-2 flex items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: c.color }} />
                      <span className="text-xs font-semibold text-white">{c.label}</span>
                    </div>
                    <div className="text-[10px] text-white/40">
                      Fail: {c.avgFail}% | Del: {c.avgDel}d
                    </div>
                  </div>
                  <span className="text-xl font-bold" style={{ color: c.color }}>{c.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Metrics */}
          <div className="flex gap-6 px-5 py-3 border-t border-white/5 text-xs">
            <span className="text-white/40">Silhouette: <span className="text-emerald-400 font-bold">{data?.cluster_metrics?.silhouette_score?.toFixed(3) ?? '—'}</span></span>
            <span className="text-white/40">Clusters: <span className="text-emerald-400 font-bold">{data?.cluster_metrics?.n_clusters ?? clusterSummary.length}</span></span>
          </div>
        </Card>

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <Card className="col-span-1 lg:col-span-2 h-[500px] p-0 flex flex-col border border-white/10 relative overflow-hidden bg-[#0a0a0a]">
          {/* Map Header Badge */}
          <div className="absolute top-4 left-4 z-[400] flex items-center gap-3">
            <span className="text-white text-xl font-bold font-sans flex items-center gap-2">
              🗺️ Route Optimization
            </span>
            <span className="text-[#00F5FF] border border-[#00F5FF]/30 px-3 py-1 bg-black/50 rounded-full text-[11px] uppercase font-bold tracking-wider">
              A* Algorithm
            </span>
          </div>

          {/* Responsive 2D Map Container */}
          <div className="flex-1 w-full bg-[#0a0a0a] z-[1]">
             <MapVisualization 
               warehouses={data?.warehouses || []} 
               routePath={routePath} 
               altPath={altPath} 
               activeRisk={data?.simulation} 
             />
          </div>

          {/* Exactly Restored Legacy Route Footer with Time AI Predictor */}
          {data?.default_route && (
            <div className="w-full bg-[#0f172a] border-t border-white/10 px-6 py-4 flex flex-col xl:flex-row items-start xl:items-center justify-between z-[400] gap-4">
              <div className="flex flex-wrap gap-6 text-[15px] font-sans text-white/60">
                <div>Distance: <span className="text-[#00F5FF] font-bold">{data.default_route.total_distance_km} km</span></div>
                <div>Time: <span className="text-[#00F5FF] font-bold">{data.default_route.total_time_hours} hrs</span></div>
                <div>Cost: <span className="text-[#00F5FF] font-bold">₹{data.default_route.total_cost?.toLocaleString()}</span></div>
                <div>Stops: <span className="text-[#00F5FF] font-bold">{data.default_route.path?.length}</span></div>
              </div>
              <div className="flex items-center gap-3">
                <input 
                  type="datetime-local" 
                  value={predictionDate}
                  onChange={(e) => setPredictionDate(e.target.value)}
                  className="bg-black/50 border border-white/20 text-white/80 text-sm px-3 py-1.5 rounded focus:outline-none focus:border-[#00F5FF]"
                />
                <button
                  onClick={handleRoutePrediction}
                  disabled={isChatting}
                  className="flex items-center gap-2 bg-[#3b82f6] hover:bg-[#2563eb] text-white px-4 py-1.5 rounded font-bold text-sm transition-colors disabled:opacity-50"
                >
                  {isChatting ? <Activity className="w-4 h-4 animate-spin"/> : <Zap className="w-4 h-4"/>}
                  AI Future Predict
                </button>
              </div>
            </div>
          )}
        </Card>

        {/* Decisions / RAG Panel */}
        <Card className="col-span-1 h-[500px] p-6 flex flex-col overflow-y-auto">
          <h3 className="font-heading text-2xl italic font-bold mb-4 flex items-center justify-between text-primary">
            <div className="flex items-center gap-2"><Zap className="text-primary"/> AI Decision Engine & RAG</div>
          </h3>

          {/* Ask AI Input */}
          <form onSubmit={handleChat} className="mb-4 relative">
            <input 
              type="text" 
              value={chatInput} 
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask the AI about future risks..."
              className="w-full bg-black/50 border border-primary/30 rounded-full py-2 px-4 text-sm text-white focus:outline-none focus:border-primary transition-all"
              disabled={isChatting}
            />
            {isChatting && <Activity className="absolute right-3 top-2.5 w-4 h-4 text-primary animate-spin" />}
          </form>

          {/* Chat Response Overlay */}
          {chatResponse && (
            <div className={`p-4 mb-4 rounded-lg border ${chatResponse.error ? 'border-red-500/50 bg-red-900/20' : 'border-purple-500/50 bg-purple-900/20'}`}>
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-bold text-purple-400 flex items-center text-sm">
                  ✨ AI Prediction
                </h4>
                <button type="button" onClick={() => setChatResponse(null)} className="text-white/50 hover:text-white text-xs">✕</button>
              </div>
              <p className="text-sm text-white/80 whitespace-pre-wrap leading-relaxed">{chatResponse.text || chatResponse.answer}</p>
            </div>
          )}

          <div className="space-y-4 font-sans">
            {/* RAG Insights & Provenance (If any) */}
            {data?.current_risk?.rag_insights && (
              <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
                <h4 className="font-bold text-primary mb-2 flex items-center">
                  <Activity className="w-4 h-4 mr-2"/> Generative Insights
                </h4>
                {/* Recommendations */}
                {data.current_risk.rag_insights.recommendations?.length > 0 && (
                  <ul className="list-disc list-inside text-sm text-white/80 mb-4 space-y-1">
                    {data.current_risk.rag_insights.recommendations.map((r: string, i: number) => (
                      <li key={`rec-${i}`}>{r}</li>
                    ))}
                  </ul>
                )}
                
                {/* Document Provenance */}
                {data.current_risk.rag_insights.retrieved_context?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-primary/20">
                    <h5 className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wider">Retrieval Provenance</h5>
                    <div className="space-y-2">
                      {data.current_risk.rag_insights.retrieved_context.map((ctx: any, i: number) => (
                        <div key={`rag-${i}`} className="flex justify-between items-center bg-black/40 p-2 rounded text-xs border border-white/5">
                          <span className="text-white/70 line-clamp-1 flex-1 mr-2" title={ctx.doc_title || ctx.category}>
                            {ctx.doc_id ? `${ctx.doc_id}: ` : ''}{ctx.doc_title || ctx.category}
                          </span>
                          <div className="flex gap-2 text-[10px] uppercase font-mono tracking-tighter">
                            {ctx.cosine_score !== undefined ? (
                              <>
                                <span className="text-blue-400 bg-blue-900/30 px-1 rounded">cos:{ctx.cosine_score}</span>
                                <span className="text-purple-400 bg-purple-900/30 px-1 rounded">bm25:{ctx.bm25_score || '-'}</span>
                                <span className="text-primary bg-primary/20 px-1 rounded font-bold">hyb:{ctx.hybrid_score || ctx.cosine_score}</span>
                              </>
                            ) : (
                              <span className="text-green-400 bg-green-900/40 px-1 rounded">{ctx.relevance || 'Rel'}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Generative AI Route Constraints */}
            {data?.rag_info?.analysis && (
              <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
                <h4 className="font-bold text-primary mb-2 flex items-center">
                  <span className="text-xl mr-2 mb-0.5">🧠</span> 
                  AI Decision Engine Insight
                </h4>
                <div className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap font-sans">
                  {data.rag_info.analysis}
                </div>
              </div>
            )}

            {/* Smart Active Alerts */}
            {data?.current_risk?.alerts && data.current_risk.alerts.map((a: any, i: number) => (
              <div key={`a-${i}`} className={`p-4 border rounded-lg ${
                a.severity === 'critical' ? 'bg-red-900/20 border-red-500/50' :
                a.severity === 'high' ? 'bg-orange-900/20 border-orange-500/50' :
                'bg-yellow-900/20 border-yellow-500/50'
              }`}>
                <div className="flex justify-between items-start mb-1">
                  <h4 className={`font-bold ${
                    a.severity === 'critical' ? 'text-red-400' :
                    a.severity === 'high' ? 'text-orange-400' : 'text-yellow-400'
                  }`}>{a.title || a.type}</h4>
                  <span className="text-xs bg-white/10 px-2 py-0.5 rounded font-mono">{a.score}/100</span>
                </div>
                <p className="text-sm text-white/70 leading-snug mb-2">{a.message}</p>
                <div className="flex gap-2">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider font-bold ${
                    a.severity === 'critical' ? 'bg-red-500/20 text-red-300' :
                    a.severity === 'high' ? 'bg-orange-500/20 text-orange-300' : 'bg-yellow-500/20 text-yellow-300'
                  }`}>{a.severity}</span>
                  {a.category && <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-white/50 border border-white/10">{a.category}</span>}
                </div>
              </div>
            ))}

            {/* Decisions */}
            {data?.decisions?.length > 0 && data.decisions.map((d: any, i: number) => (
              <div key={`d-${i}`} className="p-4 bg-white/5 border border-white/10 rounded-lg">
                <h4 className="font-bold text-white mb-1 flex items-center">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-2"/>
                  {d.action}
                </h4>
                <p className="text-sm text-white/60 pl-3.5 border-l border-white/10 ml-0.5">{d.justification}</p>
              </div>
            ))}

            {(!data?.current_risk?.alerts?.length && !data?.decisions?.length && !data?.current_risk?.rag_insights && !data?.rag_info?.analysis) && (
              <div className="p-4 bg-green-900/10 border border-green-500/20 rounded-lg h-full flex flex-col items-center justify-center text-center">
                 <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center mb-2">
                   <span className="text-green-500 text-lg">✓</span>
                 </div>
                 <h4 className="font-bold text-green-400 mb-1">System Standby</h4>
                 <p className="text-sm text-green-200/50">Awaiting simulation data or active disruptions to deploy AI decision engine.</p>
              </div>
            )}
          </div>
        </Card>
      </div>

    </div>
  )
}
