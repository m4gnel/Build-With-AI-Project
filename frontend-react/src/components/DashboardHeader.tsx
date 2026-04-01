import { ArrowLeft, RefreshCw, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface DashboardHeaderProps {
  data: any;
  loading: boolean;
  onRefresh: () => void;
}

export function DashboardHeader({ data, loading, onRefresh }: DashboardHeaderProps) {
  const navigate = useNavigate();
  const riskScore = data?.current_risk?.overall_risk_score || 0;

  return (
    <header className="flex w-full items-center justify-between border-b border-white/5 pb-4 mb-6">
      <div className="flex items-center space-x-4">
        <button 
          onClick={() => navigate('/')} 
          className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
          title="Back to Landing Page"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center space-x-2">
          <Zap className="w-6 h-6 text-primary animate-pulse" />
          <div>
            <h1 className="font-heading italic text-2xl tracking-tight text-white leading-none">SupplyChain AI</h1>
            <p className="text-xs text-gray-500 font-sans tracking-wide">Smart Risk Predictor & Optimizer</p>
          </div>
        </div>
      </div>

      <div className="hidden md:flex items-center space-x-1 glass px-1 py-1 rounded-full border border-white/10">
        <StatusPill label="Demand AI" active={data?.system_status?.demand_trained ?? true} />
        <StatusPill label="Clustering" active={data?.system_status?.suppliers_clustered ?? true} />
        <StatusPill label="Routes" active={data?.system_status?.routes_loaded ?? true} />
        <StatusPill label="RAG Engine" active={true} />
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center bg-gray-900/50 border border-white/10 rounded-lg px-4 py-2">
          <span className="text-gray-400 text-sm mr-3 font-sans">Overall Risk</span>
          <span className={`font-heading italic text-3xl leading-none ${riskScore > 50 ? 'text-rose-500' : 'text-primary'}`}>
            {Math.round(riskScore) || '--'}
          </span>
        </div>
        
        <button 
          onClick={onRefresh}
          className="p-3 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors"
          title="Refresh Dashboard"
        >
          <RefreshCw className={`w-5 h-5 text-gray-300 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </header>
  );
}

function StatusPill({ label, active }: { label: string; active: boolean }) {
  return (
    <div className={`flex items-center space-x-2 px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-colors ${active ? 'bg-primary/10 text-primary' : 'text-gray-600'}`}>
      <div className={`w-2 h-2 rounded-full ${active ? 'bg-primary shadow-[0_0_8px_rgba(0,245,255,0.6)]' : 'bg-gray-700'}`} />
      <span>{label}</span>
    </div>
  );
}
