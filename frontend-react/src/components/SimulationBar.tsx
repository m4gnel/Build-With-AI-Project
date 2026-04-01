import { Play, CloudLightning, Construction, Activity, AlertTriangle, TrendingUp, ShieldAlert, Route } from 'lucide-react';
import { Button } from './ui/Button';

interface SimulationBarProps {
  onQuickDemo: () => void;
  onSimulate: (type: string, location: string) => void;
  onOptimizeRoute: (src: number, dest: number) => void;
  loading: boolean;
}

const WAREHOUSES = [
  { id: 1, name: "Mumbai" },
  { id: 2, name: "Delhi" },
  { id: 3, name: "Bangalore" },
  { id: 4, name: "Chennai" },
  { id: 5, name: "Kolkata" },
  { id: 6, name: "Hyderabad" },
  { id: 7, name: "Ahmedabad" },
  { id: 8, name: "Pune" },
  { id: 9, name: "Jaipur" },
  { id: 10, name: "Lucknow" }
];

export function SimulationBar({ onQuickDemo, onSimulate, onOptimizeRoute, loading }: SimulationBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between bg-black border-y border-white/5 py-4 mb-6 shadow-xl relative z-20">
      <div className="flex items-center space-x-4 mb-4 xl:mb-0">
        <Button 
          variant="glass" 
          onClick={onQuickDemo} 
          disabled={loading}
          className="font-sans px-6"
        >
          <Play className="w-4 h-4 mr-2" /> Quick Demo
        </Button>
        <div className="w-px h-8 bg-white/10 mx-2" />
        <span className="text-gray-500 font-sans text-sm flex items-center">
          <Activity className="w-4 h-4 mr-2" /> Simulate:
        </span>
      </div>

      <div className="flex flex-wrap gap-2 mb-4 xl:mb-0 hidden sm:flex">
        <Button variant="outline" size="sm" onClick={() => onSimulate('storm', 'Mumbai')} disabled={loading} className="text-cyan-400 border-cyan-900/50 hover:bg-cyan-900/20">
          <CloudLightning className="w-3 h-3 mr-2" /> Storm (Mumbai)
        </Button>
        <Button variant="outline" size="sm" onClick={() => onSimulate('strike', 'Delhi')} disabled={loading} className="text-pink-400 border-pink-900/50 hover:bg-pink-900/20">
          <Construction className="w-3 h-3 mr-2" /> Strike (Delhi)
        </Button>
        <Button variant="outline" size="sm" onClick={() => onSimulate('earthquake', 'Guwahati')} disabled={loading} className="text-amber-400 border-amber-900/50 hover:bg-amber-900/20">
          <Activity className="w-3 h-3 mr-2" /> Earthquake (Guwahati)
        </Button>
        <Button variant="outline" size="sm" onClick={() => onSimulate('supplier', 'Kanpur')} disabled={loading} className="text-rose-400 border-rose-900/50 hover:bg-rose-900/20">
          <AlertTriangle className="w-3 h-3 mr-2" /> Supplier Fail (Kanpur)
        </Button>
        <Button variant="outline" size="sm" onClick={() => onSimulate('demand_spike', 'National')} disabled={loading} className="text-purple-400 border-purple-900/50 hover:bg-purple-900/20">
          <TrendingUp className="w-3 h-3 mr-2" /> Demand Spike
        </Button>
        <Button variant="outline" size="sm" onClick={() => onSimulate('pandemic', 'National')} disabled={loading} className="text-red-500 border-red-900/50 hover:bg-red-900/20">
          <ShieldAlert className="w-3 h-3 mr-2" /> Pandemic
        </Button>
      </div>

      <div className="flex items-center space-x-2 bg-white/5 border border-white/10 px-4 py-2 rounded-lg">
        <Route className="w-4 h-4 text-gray-400 mr-2" />
        <select id="routeSrc" defaultValue="4" className="bg-transparent text-sm text-white focus:outline-none border-b border-white/20 pb-1">
          {WAREHOUSES.map(w => <option key={`src-${w.id}`} value={w.id} className="bg-black text-white">{w.name}</option>)}
        </select>
        <span className="text-gray-500 mx-2">→</span>
        <select id="routeDest" defaultValue="1" className="bg-transparent text-sm text-white focus:outline-none border-b border-white/20 pb-1 mr-4">
          {WAREHOUSES.map(w => <option key={`dest-${w.id}`} value={w.id} className="bg-black text-white">{w.name}</option>)}
        </select>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => {
            const src = parseInt((document.getElementById('routeSrc') as HTMLSelectElement).value);
            const dest = parseInt((document.getElementById('routeDest') as HTMLSelectElement).value);
            onOptimizeRoute(src, dest);
          }}
          disabled={loading}
          className="bg-primary/10 text-primary border-primary/20 hover:bg-primary/20"
        >
          Optimize Path
        </Button>
      </div>
    </div>
  );
}
