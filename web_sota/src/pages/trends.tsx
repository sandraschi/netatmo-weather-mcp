import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Thermometer, Droplets, Gauge, Wind, RefreshCw } from "lucide-react";
import { getStations, getCurrentWeather, type StationSummary } from "@/common/api";

interface Snapshot {
  timestamp: string;
  temperature?: number;
  humidity?: number;
  pressure?: number;
}

export function Trends() {
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [current, setCurrent] = useState<Snapshot | null>(null);
  const [history, setHistory] = useState<Snapshot[]>([]);
  const [error, setError] = useState("");

  const load = async (stationId: string) => {
    setError("");
    try {
      const w = await getCurrentWeather(stationId);
      const snap: Snapshot = {
        timestamp: w.timestamp,
        temperature: w.data.temperature,
        humidity: w.data.humidity,
        pressure: w.data.pressure,
      };
      setCurrent(snap);
      setHistory(prev => [...prev.slice(-59), snap]);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const s = await getStations();
        const list = s.stations || [];
        setStations(list);
        if (list.length > 0) {
          setSelected(list[0].id);
          await load(list[0].id);
        }
      } catch {
        setError("Cannot reach Netatmo API");
      }
    })();
  }, []);

  useEffect(() => {
    if (!selected) return;
    const interval = setInterval(() => load(selected), 30000);
    return () => clearInterval(interval);
  }, [selected]);

  const data = ["temperature", "humidity", "pressure"] as const;
  const colors: Record<string, string> = { temperature: "text-rose-400", humidity: "text-blue-400", pressure: "text-amber-400" };
  const icons: Record<string, React.ReactNode> = {
    temperature: <Thermometer className="h-4 w-4" />,
    humidity: <Droplets className="h-4 w-4" />,
    pressure: <Gauge className="h-4 w-4" />,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Live Trends</h2>
          <p className="text-slate-400">Real-time weather data from Netatmo stations</p>
        </div>
        <button onClick={() => selected && load(selected)} className="text-slate-400 hover:text-white transition-colors">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {stations.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {stations.map(s => (
            <button
              key={s.id}
              onClick={() => { setSelected(s.id); load(s.id); }}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${selected === s.id ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
            >
              {s.name}
            </button>
          ))}
        </div>
      )}

      {error && (
        <Card className="border-red-800 bg-red-950/20">
          <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      {current && (
        <div className="grid gap-4 md:grid-cols-3">
          {data.map(key => (
            <Card key={key} className="border-slate-800 bg-slate-950/50">
              <CardHeader className="pb-2">
                <CardTitle className={`text-sm font-medium flex items-center gap-2 ${colors[key]}`}>
                  {icons[key]}
                  {key.charAt(0).toUpperCase() + key.slice(1)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {current[key] != null ? `${current[key]}${key === "temperature" ? "°C" : key === "humidity" ? "%" : " hPa"}` : "—"}
                </div>
                <p className="text-xs text-slate-500 mt-1">Last: {current.timestamp}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {history.length > 1 && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-amber-500" />
              Recent readings (last {history.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-800">
                    <th className="text-left py-2 pr-4">Time</th>
                    <th className="text-right pr-4">Temp</th>
                    <th className="text-right pr-4">Humidity</th>
                    <th className="text-right">Pressure</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(-20).reverse().map((s, i) => (
                    <tr key={i} className="border-b border-slate-800/50 text-slate-300">
                      <td className="py-1.5 pr-4 text-xs text-slate-500">{s.timestamp}</td>
                      <td className="text-right pr-4">{s.temperature != null ? `${s.temperature}°C` : "—"}</td>
                      <td className="text-right pr-4">{s.humidity != null ? `${s.humidity}%` : "—"}</td>
                      <td className="text-right">{s.pressure != null ? `${s.pressure} hPa` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {!current && !error && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="p-6 text-center text-slate-500">Loading data…</CardContent>
        </Card>
      )}
    </div>
  );
}
