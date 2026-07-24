import {
  type CurrentWeatherResponse,
  type StationSummary,
  getCurrentWeather,
  getStations,
} from "@/common/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CloudRain,
  Droplets,
  Gauge,
  Loader2,
  Thermometer,
  Wifi,
  WifiOff,
  Wind,
  Trophy,
  Radio,
} from "lucide-react";
import { useEffect, useState } from "react";

function windDegToDir(deg: number | undefined | null): string {
  if (deg == null) return "";
  const dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return dirs[Math.round(deg / 22.5) % 16];
}

function CompassArrow({ angle }: { angle?: number | null }) {
  if (angle == null) return null;
  return (
    <span
      className="inline-block transition-transform text-emerald-400"
      style={{ transform: `rotate(${angle}deg)` }}
    >
      &#8593;
    </span>
  );
}

function MetricRow({
  label,
  value,
  unit,
  icon,
}: {
  label: string;
  value: number | undefined | null;
  unit: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="flex items-center gap-1.5 text-slate-400 text-xs">
        {icon}
        {label}
      </span>
      <span className="text-sm font-mono text-slate-200">
        {value != null ? `${value} ${unit}` : "\u2014"}
      </span>
    </div>
  );
}

export function Stations() {
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [weather, setWeather] = useState<Record<string, CurrentWeatherResponse>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await getStations();
        if (cancelled) return;
        setStations(res.stations ?? []);
        const wMap: Record<string, CurrentWeatherResponse> = {};
        for (const s of res.stations ?? []) {
          if (!s.id) continue;
          try {
            const w = await getCurrentWeather(s.id);
            if (!cancelled) wMap[s.id] = w;
          } catch {
            // skip per-station errors
          }
        }
        if (!cancelled) setWeather(wMap);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load stations");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 p-12 text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span>Loading stations...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/30 p-4 text-red-200">
        <p>{error}. Ensure the backend is running (web_sota\\start.ps1).</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="stations-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Stations</h2>
        <p className="text-slate-400">
          Netatmo weather stations and current readings
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stations.map((station) => {
          const w = weather[station.id];
          const d = w?.data;
          return (
            <Card key={station.id} className="border-slate-800 bg-slate-950/50" data-testid={`station-card-${station.name.replace(/[^a-zA-Z0-9-]/g, "-")}`}>
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div>
                  <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                    <CloudRain className="h-4 w-4 text-emerald-500" />
                    {station.name}
                  </CardTitle>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {station.home_name} &middot; {station.modules_count} modules
                    {station.data_types?.length
                      ? ` \u00b7 ${station.data_types.join(", ")}`
                      : ""}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={
                    station.reachable
                      ? "border-emerald-500/50 text-emerald-400"
                      : "border-slate-500 text-slate-400"
                  }
                >
                  {station.reachable ? (
                    <>
                      <Wifi className="h-3 w-3 mr-1" /> Online
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-3 w-3 mr-1" /> Offline
                    </>
                  )}
                </Badge>
              </CardHeader>
              <CardContent>
                {d ? (
                  <div className="space-y-1 divide-y divide-slate-800/50">
                    <MetricRow
                      label="Temperature"
                      value={d.temperature}
                      unit="\u00b0C"
                      icon={<Thermometer className="h-3 w-3 text-rose-400" />}
                    />
                    <MetricRow
                      label="Humidity"
                      value={d.humidity}
                      unit="%"
                      icon={<Droplets className="h-3 w-3 text-blue-400" />}
                    />
                    <MetricRow
                      label="Pressure"
                      value={d.pressure}
                      unit="hPa"
                      icon={<Gauge className="h-3 w-3 text-amber-400" />}
                    />
                    <MetricRow
                      label="CO2"
                      value={d.co2}
                      unit="ppm"
                      icon={<Trophy className="h-3 w-3 text-emerald-400" />}
                    />
                    <MetricRow
                      label="Noise"
                      value={d.noise}
                      unit="dB"
                      icon={<Radio className="h-3 w-3 text-purple-400" />}
                    />
                    {d.rain != null && (
                      <MetricRow
                        label="Rain"
                        value={d.rain}
                        unit="mm"
                        icon={<CloudRain className="h-3 w-3 text-cyan-400" />}
                      />
                    )}
                    {d.wind_strength != null && (
                      <div className="flex items-center justify-between py-1">
                        <span className="flex items-center gap-1.5 text-slate-400 text-xs">
                          <Wind className="h-3 w-3 text-indigo-400" />
                          Wind
                        </span>
                        <span className="text-sm font-mono text-slate-200 flex items-center gap-1">
                          <CompassArrow angle={d.wind_angle} />
                          {d.wind_strength} km/h
                          {d.wind_angle != null && (
                            <span className="text-xs text-slate-500">
                              {windDegToDir(d.wind_angle)}
                            </span>
                          )}
                        </span>
                      </div>
                    )}
                    {d.gust_strength != null && (
                      <MetricRow
                        label="Gust"
                        value={d.gust_strength}
                        unit="km/h"
                        icon={<Wind className="h-3 w-3 text-violet-400" />}
                      />
                    )}
                  </div>
                ) : station.reachable ? (
                  <p className="text-xs text-slate-500 py-2">Loading data...</p>
                ) : (
                  <p className="text-xs text-slate-600 py-2">Station offline</p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {stations.length === 0 && (
        <p className="text-slate-500">
          No stations found. Check Netatmo credentials and backend.
        </p>
      )}
    </div>
  );
}
