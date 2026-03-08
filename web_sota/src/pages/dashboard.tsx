import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, CloudRain, Battery, Database, AlertCircle } from "lucide-react";
import { getHealth, getStations, getCurrentWeather, type StationsResponse, type CurrentWeatherResponse } from "@/common/api";

export function Dashboard() {
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [stations, setStations] = useState<StationsResponse | null>(null);
  const [weather, setWeather] = useState<CurrentWeatherResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const h = await getHealth();
        if (cancelled) return;
        setHealthOk(h.success && h.status === "online");
        if (!h.success) return;
        const s = await getStations();
        if (cancelled) return;
        setStations(s);
        const first = s.stations?.[0];
        if (first?.id) {
          const w = await getCurrentWeather(first.id);
          if (!cancelled) setWeather(w);
        }
      } catch (e) {
        if (!cancelled) {
          setHealthOk(false);
          setError(e instanceof Error ? e.message : "Backend unreachable");
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const firstStation = stations?.stations?.[0];
  const modulesCount = firstStation?.modules_count ?? 0;
  const reachableCount = stations?.reachable_count ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Weather Dashboard</h2>
          <p className="text-slate-400">Netatmo station and environmental telemetry</p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-800 bg-amber-950/50 p-4 text-amber-200 space-y-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <p className="text-sm">{error}. Run web_sota\\start.ps1 to start backend and frontend.</p>
          </div>
          <Link to="/onboarding" className="text-sm text-emerald-400 hover:text-emerald-300 underline">
            Get started with Netatmo credentials
          </Link>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Active Stations</CardTitle>
            <CloudRain className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {stations == null ? "—" : stations.total_count}
            </div>
            <p className="text-xs text-slate-400">
              {stations == null ? "Loading…" : `${modulesCount} modules connected`}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Reachable</CardTitle>
            <Battery className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {stations == null ? "—" : reachableCount}
            </div>
            <p className="text-xs text-slate-400">
              {stations == null ? "—" : "Stations online"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Backend</CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {healthOk === null ? "—" : healthOk ? "10823" : "Offline"}
            </div>
            <p className="text-xs text-slate-400">
              {healthOk === null ? "Checking…" : healthOk ? "API active" : "Not connected"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Current</CardTitle>
            <Database className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {weather?.data?.temperature != null ? `${weather.data.temperature} °C` : "—"}
            </div>
            <p className="text-xs text-slate-400">
              {weather ? (firstStation?.name ?? "Indoor") : "No data"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Current conditions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 font-mono text-sm text-slate-400">
              {weather?.data ? (
                <>
                  {weather.data.temperature != null && <p>Temperature: {weather.data.temperature} °C</p>}
                  {weather.data.humidity != null && <p>Humidity: {weather.data.humidity} %</p>}
                  {weather.data.pressure != null && <p>Pressure: {weather.data.pressure} mbar</p>}
                  {weather.data.co2 != null && <p>CO2: {weather.data.co2} ppm</p>}
                  {weather.data.noise != null && <p>Noise: {weather.data.noise} dB</p>}
                  {weather.data.rain != null && <p>Rain: {weather.data.rain} mm</p>}
                </>
              ) : error ? (
                <p className="text-amber-400">No data — start the backend.</p>
              ) : (
                <p>Loading…</p>
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">System</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center">
                <Activity className="h-4 w-4 text-slate-400 mr-2" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-white">Backend</p>
                  <p className="text-xs text-slate-400">
                    {healthOk === true ? "127.0.0.1:10823 healthy" : healthOk === false ? "Disconnected" : "Checking…"}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
