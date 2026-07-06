import { useMemo, useRef, useState, type PointerEvent, type WheelEvent } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import { feature, mesh } from "topojson-client";
import { Minus, Plus, RotateCcw } from "lucide-react";
import statesAtlas from "us-atlas/states-10m.json";
import type { ExploreCity } from "./types";

const WIDTH = 960;
const HEIGHT = 560;

export function InteractiveMap({ cities, onOpen }: { cities: ExploreCity[]; onOpen: (city: ExploreCity) => void }) {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; originX: number; originY: number } | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const geography = useMemo(() => {
    const atlas = statesAtlas as unknown as { objects: { states: object } };
    const states = feature(atlas as never, atlas.objects.states as never);
    const projection = geoAlbersUsa().fitSize([WIDTH - 42, HEIGHT - 42], states as never);
    return {
      states,
      borders: mesh(atlas as never, atlas.objects.states as never, (a, b) => a !== b),
      projection,
      path: geoPath(projection),
    };
  }, []);
  const setBoundedZoom = (value: number) => setZoom(Math.max(1, Math.min(5, value)));
  const reset = () => { setZoom(1); setOffset({ x: 0, y: 0 }); };
  const onWheel = (event: WheelEvent<SVGSVGElement>) => {
    event.preventDefault();
    setBoundedZoom(zoom * (event.deltaY > 0 ? 0.85 : 1.18));
  };
  const onPointerDown = (event: PointerEvent<SVGSVGElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    drag.current = { x: event.clientX, y: event.clientY, originX: offset.x, originY: offset.y };
  };
  const onPointerMove = (event: PointerEvent<SVGSVGElement>) => {
    if (!drag.current || !svgRef.current) return;
    const scale = WIDTH / svgRef.current.getBoundingClientRect().width;
    setOffset({
      x: drag.current.originX + (event.clientX - drag.current.x) * scale / zoom,
      y: drag.current.originY + (event.clientY - drag.current.y) * scale / zoom,
    });
  };
  const stopDragging = () => { drag.current = null; };

  return <section className="map-shell" aria-label="Geographic view of job-covered places">
    <div className="map-label"><strong>United States</strong><span>Drag to pan · scroll to zoom</span></div>
    <svg ref={svgRef} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Interactive map of job-covered United States places" onWheel={onWheel} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={stopDragging} onPointerCancel={stopDragging}>
      <g transform={`translate(${WIDTH / 2} ${HEIGHT / 2}) scale(${zoom}) translate(${-WIDTH / 2 + offset.x} ${-HEIGHT / 2 + offset.y})`}>
        <path className="country-fill" d={geography.path(geography.states as never) ?? ""}/>
        <path className="state-borders" d={geography.path(geography.borders as never) ?? ""}/>
        {cities.slice(0,120).map((city) => {
          const point = geography.projection([city.longitude, city.latitude]);
          if (!point) return null;
          const radius = Math.max(4.5, Math.min(11, 3.5 + Math.sqrt(city.active_listing_count) * .55));
          return <circle key={city.place_geoid} cx={point[0]} cy={point[1]} r={radius / Math.sqrt(zoom)} className="city-dot" tabIndex={0} role="button" aria-label={`${city.name}, ${city.state_code}: ${city.active_listing_count} roles`} onPointerDown={(event) => event.stopPropagation()} onClick={() => onOpen(city)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") onOpen(city); }}><title>{city.name}, {city.state_code} · {city.active_listing_count} roles</title></circle>;
        })}
      </g>
    </svg>
    <div className="map-controls" aria-label="Map zoom controls"><button onClick={() => setBoundedZoom(zoom * 1.35)} aria-label="Zoom in"><Plus size={18}/></button><button onClick={() => setBoundedZoom(zoom / 1.35)} aria-label="Zoom out"><Minus size={18}/></button><button onClick={reset} aria-label="Reset map"><RotateCcw size={17}/></button></div>
    <output className="zoom-level">{Math.round(zoom * 100)}%</output>
  </section>;
}
