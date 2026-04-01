import { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface MapProps {
  warehouses: any[];
  routePath: [number, number][];
  altPath?: [number, number][];
  activeRisk?: { location?: string; type?: string };
}

// ── Land-waypoint table ────────────────────────────────────────────────────
// Any direct polyline between these city-pairs would cross a sea or bay.
// We inject intermediate land coordinates so the route stays on land.
// Key format: "CityA|CityB" (canonically sorted alphabetically).
const SEA_WAYPOINTS: Record<string, [number, number][]> = {
  // Chennai ↔ Kolkata  (Bay of Bengal shortcut)
  "Chennai|Kolkata":       [[14.5, 80.2], [17.0, 81.8], [19.5, 84.8], [21.5, 86.5]],
  // Chennai ↔ Hyderabad (minor gulf bend – slight correction)
  // Mumbai  ↔ Chennai   (Arabian Sea + Palk Strait)
  "Chennai|Mumbai":        [[13.08, 80.27], [12.97, 77.59], [18.52, 73.85]],
  // Mumbai  ↔ Kolkata   (direct oversea line)
  "Kolkata|Mumbai":        [[22.57, 88.36], [24.5, 87.0], [25.59, 85.14],
                            [26.45, 80.33], [26.85, 77.49], [23.02, 72.57]],
  // Visakhapatnam ↔ Mumbai
  "Mumbai|Visakhapatnam":  [[19.07, 72.88], [17.38, 78.49], [17.69, 83.22]],
  // Kolkata ↔ Chennai (same as above reversed, handled by sort)
};

/** Return the intermediate land waypoints for a given city-to-city segment. */
function landWaypoints(cityA: string, cityB: string): [number, number][] {
  const key = [cityA, cityB].sort().join("|");
  return SEA_WAYPOINTS[key] || [];
}

// ── City → Coordinates lookup ──────────────────────────────────────────────
const CITY_COORDS: Record<string, [number, number]> = {
  "Mumbai":         [19.0760, 72.8777],
  "Delhi":          [28.7041, 77.1025],
  "Bangalore":      [12.9716, 77.5946],
  "Chennai":        [13.0827, 80.2707],
  "Kolkata":        [22.5726, 88.3639],
  "Hyderabad":      [17.3850, 78.4867],
  "Pune":           [18.5204, 73.8567],
  "Ahmedabad":      [23.0225, 72.5714],
  "Jaipur":         [26.9124, 75.7873],
  "Lucknow":        [26.8467, 80.9462],
  "Kanpur":         [26.4499, 80.3319],
  "Nagpur":         [21.1458, 79.0882],
  "Indore":         [22.7196, 75.8577],
  "Bhopal":         [23.2599, 77.4126],
  "Visakhapatnam":  [17.6868, 83.2185],
  "Surat":          [21.1702, 72.8311],
  "Patna":          [25.5941, 85.1376],
  "Varanasi":       [25.3176, 82.9739],
};

/**
 * Given a sequence of [lat,lng] stops, return a full polyline coordinate list
 * that injects land-waypoints for any segment that would otherwise cross water.
 *
 * We use the warehouse `city` names extracted from the routePath augmented data
 * passed via `cityNames` to look up sea-crossing pairs.
 */
function buildLandLine(
  stops: [number, number][],
  cityNames: string[]
): [number, number][] {
  if (stops.length < 2) return stops;
  const result: [number, number][] = [stops[0]];

  for (let i = 0; i < stops.length - 1; i++) {
    const cityA =  cityNames[i]   || '';
    const cityB =  cityNames[i+1] || '';
    const midpoints = landWaypoints(cityA, cityB);
    result.push(...midpoints, stops[i + 1]);
  }
  return result;
}

// ── Auto-fit map to active route ───────────────────────────────────────────
const RecenterAutomatically = ({ routePath }: { routePath: [number, number][] }) => {
  const map = useMap();
  useEffect(() => {
    if (routePath && routePath.length > 0) {
      map.fitBounds(routePath, { padding: [50, 50], maxZoom: 6 });
    }
  }, [routePath, map]);
  return null;
};

// ── Main Component ─────────────────────────────────────────────────────────
export function MapVisualization({ warehouses, routePath, altPath, activeRisk }: MapProps) {
  const riskCoords = activeRisk?.location ? CITY_COORDS[activeRisk.location] : null;

  // Extract ordered city names from the warehouses that match the route coordinates
  function getCityNames(path: [number, number][]): string[] {
    return path.map(([lat, lng]) => {
      const wh = warehouses.find(
        w => Math.abs(w.lat - lat) < 0.02 && Math.abs(w.lng - lng) < 0.02
      );
      return wh?.city || '';
    });
  }

  const optimalCities = getCityNames(routePath);
  const altCities     = getCityNames(altPath || []);

  // Build land-following polyline coordinates
  const optimalLine = buildLandLine(routePath, optimalCities);
  const altLine     = buildLandLine(altPath || [], altCities);

  return (
    <div className="w-full h-full relative rounded-xl overflow-hidden">
      <MapContainer
        center={[22.5, 79.5]}
        zoom={5}
        style={{ height: '100%', width: '100%', background: '#0a0a0a' }}
        zoomControl={true}
      >
        <RecenterAutomatically routePath={routePath.length > 0 ? routePath : [[22.5, 79.5]]} />

        {/* Dark base layer — no labels */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          opacity={0.85}
        />
        {/* Subtle label layer */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
          opacity={0.35}
        />

        {/* ── Optimal path (thick solid blue — land-following) */}
        {optimalLine.length > 1 && (
          <Polyline
            positions={optimalLine}
            pathOptions={{
              color: '#3b82f6',
              weight: 5,
              opacity: 0.92,
              lineCap: 'round',
              lineJoin: 'round',
            }}
          />
        )}

        {/* ── Alternative path (dashed orange — land-following) */}
        {altLine.length > 1 && (
          <Polyline
            positions={altLine}
            pathOptions={{
              color: '#d97706',
              weight: 3,
              opacity: 0.8,
              dashArray: '8, 8',
              lineCap: 'round',
            }}
          />
        )}

        {/* ── Warehouse nodes (only active ones on the route) */}
        {warehouses?.map((wh, idx) => {
          const isOnOptimal = routePath.some(
            ([lat, lng]) => Math.abs(lat - wh.lat) < 0.02 && Math.abs(lng - wh.lng) < 0.02
          );
          const isOnAlt = (altPath || []).some(
            ([lat, lng]) => Math.abs(lat - wh.lat) < 0.02 && Math.abs(lng - wh.lng) < 0.02
          );
          const isRisk = riskCoords &&
            Math.abs(riskCoords[0] - wh.lat) < 0.02 &&
            Math.abs(riskCoords[1] - wh.lng) < 0.02;

          if (!isOnOptimal && !isOnAlt && !isRisk) return null;

          const isStart = routePath.length > 0 &&
            Math.abs(routePath[0][0] - wh.lat) < 0.02 &&
            Math.abs(routePath[0][1] - wh.lng) < 0.02;
          const isEnd = routePath.length > 0 &&
            Math.abs(routePath[routePath.length - 1][0] - wh.lat) < 0.02 &&
            Math.abs(routePath[routePath.length - 1][1] - wh.lng) < 0.02;

          let fill = '#3b82f6';
          if (isStart) fill = '#10b981';
          if (isEnd)   fill = '#ef4444';
          if (isRisk)  fill = '#dc2626';

          return (
            <CircleMarker
              key={idx}
              center={[wh.lat, wh.lng]}
              radius={isStart || isEnd ? 9 : 7}
              pathOptions={{ color: '#ffffff', weight: 2, fillColor: fill, fillOpacity: 1 }}
            >
              <Tooltip direction="top" offset={[0, -10]} opacity={1}>
                <div style={{ fontFamily: 'inherit', fontWeight: 700, fontSize: 12 }}>
                  {wh.city}
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}

        {/* ── Standalone disruption marker */}
        {riskCoords && !warehouses.some(
          w => Math.abs(riskCoords[0] - w.lat) < 0.02 && Math.abs(riskCoords[1] - w.lng) < 0.02
        ) && (
          <CircleMarker
            center={riskCoords}
            radius={12}
            pathOptions={{
              color: '#ef4444',
              weight: 3,
              fillColor: 'rgba(239,68,68,0.4)',
              fillOpacity: 1,
              dashArray: '4, 4',
            }}
          >
            <Tooltip permanent direction="top">
              <span style={{ color: '#ef4444', fontWeight: 700 }}>
                ⚠ {activeRisk?.location}
              </span>
            </Tooltip>
          </CircleMarker>
        )}
      </MapContainer>

      {/* Leaflet theme overrides */}
      <style>{`
        .leaflet-container { background-color: #050505 !important; }
        .leaflet-control-zoom a {
          background-color: #1e293b !important;
          color: white !important;
          border-color: #334155 !important;
        }
        .leaflet-control-zoom a:hover { background-color: #334155 !important; }
        .leaflet-tooltip {
          background-color: #0f172a;
          color: white;
          border: 1px solid #334155;
          border-radius: 6px;
          padding: 4px 8px;
        }
        .leaflet-tooltip-top::before { border-top-color: #0f172a; }
      `}</style>
    </div>
  );
}
