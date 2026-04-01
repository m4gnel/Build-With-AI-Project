import { useEffect, useRef, useState } from 'react';
import Globe from 'react-globe.gl';

interface GlobeProps {
  warehouses: any[];
  routePath: [number, number][];
  altPath?: [number, number][];
  activeRisk?: { location?: string, type?: string };
}

const CITY_COORDS: Record<string, [number, number]> = {
  "Mumbai": [19.0760, 72.8777],
  "Delhi": [28.7041, 77.1025],
  "Bangalore": [12.9716, 77.5946],
  "Chennai": [13.0827, 80.2707],
  "Kolkata": [22.5726, 88.3639]
};

export function GlobeVisualization({ warehouses, routePath, altPath, activeRisk }: GlobeProps) {
  const globeEl = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [countries, setCountries] = useState<any>({ features: [] });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load high-res country boundaries and detailed Indian state boundaries
    Promise.all([
      fetch('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson').then(r => r.json()),
      fetch('https://raw.githubusercontent.com/geohacker/india/master/state/india_telengana.geojson').then(r => r.json()).catch(() => ({ features: [] }))
    ]).then(([world, indiaStates]) => {
      setCountries({
        features: [...(world.features || []), ...(indiaStates.features || [])]
      });
    }).catch(console.error);
  }, []);

  useEffect(() => {
    // Handle container resizing
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    window.addEventListener('resize', updateSize);
    updateSize();

    // Auto-rotate setup
    if (globeEl.current) {
      globeEl.current.controls().autoRotate = true;
      globeEl.current.controls().autoRotateSpeed = 0.5;
      globeEl.current.pointOfView({ lat: 20, lng: 80, altitude: 1.5 });
    }

    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Intelligent Camera Tracking
  useEffect(() => {
    if (!globeEl.current) return;

    if (routePath && routePath.length > 0) {
      // Track the Optimal Path by centering on its midpoint
      const midIndex = Math.floor(routePath.length / 2);
      const targetLat = routePath[midIndex][0];
      const targetLng = routePath[midIndex][1];
      globeEl.current.pointOfView({ lat: targetLat, lng: targetLng, altitude: 1.2 }, 2000);
    } else if (activeRisk && activeRisk.location) {
      // Snap to disruption event if no route is explicitly prioritized
      const coords = CITY_COORDS[activeRisk.location];
      if (coords) {
        globeEl.current.pointOfView({ lat: coords[0], lng: coords[1], altitude: 1.2 }, 2000);
      }
    }
  }, [routePath, activeRisk]);

  // Process Arcs from pathways
  const arcsData: any[] = [];

  // Faint background network (all small roots connecting warehouses)
  if (warehouses && warehouses.length > 0) {
    warehouses.forEach((w, i) => {
      // Connect each warehouse to its 2 nearest/next neighbors in array to form a faint mesh
      for (let j = 1; j <= 2; j++) {
        const target = warehouses[(i + j) % warehouses.length];
        if (target && w.lat !== target.lat) {
          arcsData.push({
            startLat: w.lat,
            startLng: w.lng,
            endLat: target.lat,
            endLng: target.lng,
            color: ['rgba(0, 245, 255, 0.1)', 'rgba(138, 43, 226, 0.05)'], // Faint glowing thread
            type: 'network'
          });
        }
      }
    });
  }
  
  if (routePath && routePath.length > 1) {
    for (let i = 0; i < routePath.length - 1; i++) {
      arcsData.push({
        startLat: routePath[i][0],
        startLng: routePath[i][1],
        endLat: routePath[i+1][0],
        endLng: routePath[i+1][1],
        color: ['#00F5FF', '#00FFFF'],
        type: 'optimal' // Optimal path is bright cyan
      });
    }
  }

  if (altPath && altPath.length > 1) {
    for (let i = 0; i < altPath.length - 1; i++) {
      arcsData.push({
        startLat: altPath[i][0],
        startLng: altPath[i][1],
        endLat: altPath[i+1][0],
        endLng: altPath[i+1][1],
        color: ['#f59e0b', '#dc2626'],
        type: 'alternative' // Alt path is orange/red
      });
    }
  }

  // Rings for disruptions
  const ringsData: any[] = [];
  if (activeRisk && activeRisk.location) {
    // Determine coordinates for risk location (fuzzy match or specific)
    const riskCoords = CITY_COORDS[activeRisk.location];
    if (riskCoords) {
      ringsData.push({
        lat: riskCoords[0],
        lng: riskCoords[1],
        maxR: 5,
        propagationSpeed: 2,
        repeatPeriod: 700
      });
    }
  }

  // Ensure warehouses render
  const mappedWarehouses = (warehouses || []).map(w => ({
    lat: w.lat,
    lng: w.lng,
    name: w.name,
    size: 0.1
  }));

  // Prepare City Labels
  const labelsData = Object.entries(CITY_COORDS).map(([name, coords]) => ({
    lat: coords[0],
    lng: coords[1],
    text: name,
    size: 1.2,
    dotRadius: 0.3,
    color: 'rgba(255, 255, 255, 0.9)'
  }));

  return (
    <div ref={containerRef} className="w-full h-full relative" style={{ borderRadius: '0.75rem', overflow: 'hidden' }}>
      {/* Space gradient background */}
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#080b15] to-[#010204]" />
      
      <div className="absolute inset-0 z-10">
        <Globe
          ref={globeEl}
          width={dimensions.width}
          height={dimensions.height}
          // High-resolution NASA night-time realistic earth texture
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
          
          // Warehouses as Hexagons
          hexBinPointsData={mappedWarehouses}
          hexBinPointWeight="size"
          hexAltitude={(d: any) => d.sumWeight * 0.5}
          hexBinResolution={4}
          hexMargin={0.2}
          hexTopColor={() => '#00F5FF'}
          hexSideColor={() => 'rgba(0, 245, 255, 0.2)'}
          hexBinMerge={true}
          
          // Routes as intensely highlighted arcs (Optimal vs Alt vs Network)
          arcsData={arcsData}
          arcColor="color"
          // Directional flow particles
          arcDashLength={(d: any) => d.type === 'optimal' ? 0.6 : (d.type === 'alternative' ? 0.3 : 0.1)}
          arcDashGap={(d: any) => d.type === 'network' ? 4 : 1}
          arcDashInitialGap={() => Math.random()}
          arcDashAnimateTime={(d: any) => d.type === 'optimal' ? 1500 : (d.type === 'alternative' ? 3000 : 8000)}
          arcStroke={(d: any) => d.type === 'optimal' ? 3 : (d.type === 'alternative' ? 1.2 : 0.2)}
          arcAltitudeAutoScale={(d: any) => d.type === 'optimal' ? 0.3 : (d.type === 'alternative' ? 0.2 : 0.1)}

          // Political Map Boundaries
          polygonsData={countries.features}
          polygonCapColor={() => 'rgba(10, 15, 30, 0.1)'}
          polygonSideColor={() => 'rgba(0, 0, 0, 0.05)'}
          polygonStrokeColor={() => 'rgba(0, 245, 255, 0.15)'}

          // Crystal Clear HTML Labels that scale and track perfectly
          htmlElementsData={labelsData}
          htmlElement={(d: any) => {
            const el = document.createElement('div');
            el.innerHTML = `
              <div style="color: #ffffff; font-weight: 800; background: rgba(0, 0, 0, 0.6); padding: 4px 8px; border: 1px solid rgba(0,245,255,0.4); border-radius: 6px; font-family: 'Barlow', sans-serif; pointer-events: none; font-size: 14px; box-shadow: 0 0 10px rgba(0,245,255,0.2), inset 0 0 5px rgba(255,255,255,0.1); backdrop-filter: blur(4px); white-space: nowrap; transform: translate(-50%, -50%); display: flex; align-items: center; gap: 4px;">
                <span style="display:block; width:6px; height:6px; background:#00F5FF; border-radius:50%; box-shadow: 0 0 5px #00F5FF;"></span>
                ${d.text}
              </div>
            `;
            return el;
          }}

          // Disruptions as Rings
          ringsData={ringsData}
          ringColor={() => (t: number) => `rgba(255,100,50,${1-t})`}
          ringMaxRadius="maxR"
          ringPropagationSpeed="propagationSpeed"
          ringRepeatPeriod="repeatPeriod"

          // Atmospheric glow for realism
          atmosphereColor="#00F5FF"
          atmosphereAltitude={0.2}
        />
      </div>
      
      {/* Legend Override */}
      <div className="absolute bottom-4 left-4 z-20 flex gap-4 text-xs font-mono bg-black/50 p-3 rounded-lg border border-white/10 backdrop-blur-md">
        <div className="flex items-center gap-2"><div className="w-4 h-1 bg-[#00F5FF] shadow-[0_0_8px_#00F5FF]"></div> Optimal Path (Highlighted)</div>
        <div className="flex items-center gap-2"><div className="w-3 h-0.5 bg-[#f59e0b]"></div> Alternative</div>
        <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full border border-red-500 bg-red-500/30"></div> Disruption</div>
      </div>
    </div>
  );
}
