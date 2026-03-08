import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CloudRain, Wifi, WifiOff, Loader2 } from "lucide-react";
import { getStations, getCurrentWeather, type StationSummary, type CurrentWeatherResponse } from "@/common/api";

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
        for (const s of res.stations ?? []) {
          if (!s.id) continue;
          try {
            const w = await getCurrentWeather(s.id);
            if (!cancelled) setWeather((prev) => ({ ...prev, [s.id]: w }));
          } catch {
            // skip per-station errors
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load stations");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 p-12 text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span>Loading stations…</span>
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
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Stations</h2>
        <p className="text-slate-400">Netatmo weather stations and current readings</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stations.map((station) => {
          const w = weather[station.id];
          return (
            <Card key={station.id} className="border-slate-800 bg-slate-950/50">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                  <CloudRain className="h-4 w-4 text-emerald-500" />
                  {station.name}
                </CardTitle>
                <Badge
                  variant="outline"
                  className={
                    station.reachable
                      ? "border-emerald-500/50 text-emerald-400"
                      : "border-slate-500 text-slate-400"
                  }
                >
                  {station.reachable ? (
                    <><Wifi className="h-3 w-3 mr-1" /> Online</>
                  ) : (
                    <><WifiOff className="h-3 w-3 mr-1" /> Offline</>
                  )}
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-500 mb-2">{station.home_name} · {station.modules_count} modules</p>
                {w?.data && (
                  <div className="font-mono text-xs text-slate-400 space-y-1">
                    {w.data.temperature != null && <p>Temp: {w.data.temperature} °C</p>}
                    {w.data.humidity != null && <p>Humidity: {w.data.humidity} %</p>}
                    {w.data.pressure != null && <p>Pressure: {w.data.pressure} mbar</p>}
                  </div>
                )}
                {station.reachable && !w && <p className="text-xs text-slate-500">Loading data…</p>}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {stations.length === 0 && (
        <p className="text-slate-500">No stations found. Check Netatmo credentials and backend.</p>
      )}
    </div>
  );
}
