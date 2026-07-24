import {
  type HistoryDataPoint,
  type HistoryResponse,
  type StationSummary,
  getCurrentWeather,
  getStations,
  getWeatherHistory,
} from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Droplets,
  Gauge,
  Loader2,
  RefreshCw,
  Thermometer,
  TrendingUp,
  Wind,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

interface LiveSnapshot {
  ts: string;
  temperature?: number;
  humidity?: number;
  pressure?: number;
  wind_strength?: number;
  wind_angle?: number;
  co2?: number;
}

const METRICS: {
  key: keyof HistoryDataPoint;
  label: string;
  unit: string;
  color: string;
  icon: React.ReactNode;
}[] = [
  { key: "temperature", label: "Temperature", unit: "\u00b0C", color: "#fb7185", icon: <Thermometer className="h-4 w-4" /> },
  { key: "humidity", label: "Humidity", unit: "%", color: "#38bdf8", icon: <Droplets className="h-4 w-4" /> },
  { key: "pressure", label: "Pressure", unit: "hPa", color: "#fbbf24", icon: <Gauge className="h-4 w-4" /> },
  { key: "wind_strength", label: "Wind", unit: "km/h", color: "#a78bfa", icon: <Wind className="h-4 w-4" /> },
  { key: "co2", label: "CO2", unit: "ppm", color: "#34d399", icon: <TrendingUp className="h-4 w-4" /> },
];

function windDegToDir(deg: number | undefined | null): string {
  if (deg == null) return "";
  const dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return dirs[Math.round(deg / 22.5) % 16];
}

function formatTs(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString("de-AT", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return ts;
  }
}

export function Trends() {
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [selected, setSelected] = useState("");
  const [timeframe, setTimeframe] = useState("24h");
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [current, setCurrent] = useState<LiveSnapshot | null>(null);
  const [liveHistory, setLiveHistory] = useState<LiveSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const loadHistory = useCallback(async (stationId: string, tf: string) => {
    try {
      const h = await getWeatherHistory(stationId, tf);
      setHistory(h);
      return h;
    } catch (e) {
      setError((e as Error).message);
      return null;
    }
  }, []);

  const loadCurrent = useCallback(async (stationId: string) => {
    try {
      const w = await getCurrentWeather(stationId);
      const snap: LiveSnapshot = {
        ts: w.timestamp,
        temperature: w.data.temperature,
        humidity: w.data.humidity,
        pressure: w.data.pressure,
        wind_strength: w.data.wind_strength,
        wind_angle: w.data.wind_angle,
        co2: w.data.co2,
      };
      setCurrent(snap);
      setLiveHistory((prev) => [...prev.slice(-59), snap]);
    } catch {
      // skip
    }
  }, []);

  const selectStation = useCallback(async (id: string) => {
    setSelected(id);
    setError("");
    setLiveHistory([]);
    setLoading(true);
    await Promise.all([loadHistory(id, timeframe), loadCurrent(id)]);
    setLoading(false);
  }, [timeframe, loadHistory, loadCurrent]);

  useEffect(() => {
    (async () => {
      try {
        const s = await getStations();
        const list = s.stations || [];
        setStations(list);
        if (list.length > 0) {
          await selectStation(list[0].id);
        } else {
          setLoading(false);
        }
      } catch (e) {
        setError((e as Error).message);
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selected) return;
    intervalRef.current = setInterval(() => {
      loadCurrent(selected);
    }, 30000);
    return () => clearInterval(intervalRef.current);
  }, [selected, loadCurrent]);

  const handleTimeframeChange = async (tf: string) => {
    setTimeframe(tf);
    if (selected) {
      setLoading(true);
      await loadHistory(selected, tf);
      setLoading(false);
    }
  };

  const chartData = history?.historical_data?.map((p) => ({
    ...p,
    _time: formatTs(p.timestamp),
  })) ?? [];

  return (
    <div className="space-y-6" data-testid="trends-page">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Live Trends
          </h2>
          <p className="text-slate-400">
            Real-time weather data from Netatmo stations
          </p>
        </div>
        <button
          onClick={() => {
            if (selected) {
              loadCurrent(selected);
              loadHistory(selected, timeframe);
            }
          }}
          className="text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Station selector */}
      {stations.length > 0 && (
        <div className="flex gap-2 flex-wrap items-center">
          {stations.map((s) => (
            <button
              key={s.id}
              onClick={() => selectStation(s.id)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                selected === s.id
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              }`}
            >
              {s.name}
            </button>
          ))}
          <div className="ml-auto flex gap-1">
            {["24h", "7d"].map((tf) => (
              <button
                key={tf}
                onClick={() => handleTimeframeChange(tf)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  timeframe === tf
                    ? "bg-slate-700 text-white"
                    : "bg-slate-800/50 text-slate-500 hover:text-slate-300"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <Card className="border-red-800 bg-red-950/20">
          <CardContent className="p-4 text-sm text-red-400">
            {error}
          </CardContent>
        </Card>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-2 p-12 text-slate-400">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading data...</span>
        </div>
      )}

      {!loading && selected && (
        <>
          {/* Current values row */}
          {current && (
            <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
              {METRICS.map((m) => {
                const val = current[m.key as keyof typeof current];
                return (
              <Card key={m.key} className="border-slate-800 bg-slate-950/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                        <span style={{ color: m.color }}>{m.icon}</span>
                        {m.label}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-bold text-white">
                        {val != null ? `${val}${m.unit}` : "\u2014"}
                      </div>
                      {m.key === "wind_strength" && current.wind_angle != null && (
                        <p className="text-xs text-slate-500">
                          {windDegToDir(current.wind_angle)} ({current.wind_angle}\u00b0)
                        </p>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Charts */}
          {chartData.length > 1 && METRICS.map((m) => {
            const hasData = chartData.some((p) => p[m.key] != null);
            if (!hasData) return null;
            return (
              <Card key={m.key} className="border-slate-800 bg-slate-950/50" data-testid={`metric-${m.key}`}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                    <span style={{ color: m.color }}>{m.icon}</span>
                    {m.label} over {timeframe}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                          dataKey="_time"
                          tick={{ fill: "#94a3b8", fontSize: 11 }}
                          tickLine={false}
                          axisLine={{ stroke: "#334155" }}
                          interval="preserveStartEnd"
                        />
                        <YAxis
                          tick={{ fill: "#94a3b8", fontSize: 11 }}
                          tickLine={false}
                          axisLine={{ stroke: "#334155" }}
                          width={50}
                          tickFormatter={(v: number) => `${v}`}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#0f172a",
                            border: "1px solid #334155",
                            borderRadius: "6px",
                            fontSize: "12px",
                          }}
                          labelStyle={{ color: "#e2e8f0" }}
                          formatter={(value: number) => [
                            `${value}${m.unit}`,
                            m.label,
                          ]}
                          labelFormatter={(label) => `${label}`}
                        />
                        <Line
                          type="monotone"
                          dataKey={m.key}
                          stroke={m.color}
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 4, fill: m.color }}
                          connectNulls
                        />
                        <Legend
                          wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {/* Live snapshots table */}
          {liveHistory.length > 1 && (
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-amber-500" />
                  Recent readings (last {liveHistory.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 border-b border-slate-800">
                        <th className="text-left py-2 pr-3">Time</th>
                        <th className="text-right pr-3">Temp</th>
                        <th className="text-right pr-3">Humidity</th>
                        <th className="text-right pr-3">Pressure</th>
                        <th className="text-right pr-3">Wind</th>
                        <th className="text-right">CO2</th>
                      </tr>
                    </thead>
                    <tbody>
                      {liveHistory
                        .slice(-20)
                        .reverse()
                        .map((s, i) => (
                          <tr
                            key={i}
                            className="border-b border-slate-800/50 text-slate-300"
                          >
                            <td className="py-1.5 pr-3 text-xs text-slate-500">
                              {formatTs(s.ts)}
                            </td>
                            <td className="text-right pr-3">
                              {s.temperature != null
                                ? `${s.temperature}\u00b0C`
                                : "\u2014"}
                            </td>
                            <td className="text-right pr-3">
                              {s.humidity != null ? `${s.humidity}%` : "\u2014"}
                            </td>
                            <td className="text-right pr-3">
                              {s.pressure != null
                                ? `${s.pressure} hPa`
                                : "\u2014"}
                            </td>
                            <td className="text-right pr-3">
                              {s.wind_strength != null
                                ? `${s.wind_strength} km/h ${windDegToDir(s.wind_angle)}`
                                : "\u2014"}
                            </td>
                            <td className="text-right">
                              {s.co2 != null ? `${s.co2} ppm` : "\u2014"}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Empty chart state */}
          {chartData.length <= 1 && !loading && (
            <Card className="border-slate-800 bg-slate-950/50">
              <CardContent className="p-8 text-center text-slate-500">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p>Not enough historical data points for a chart.</p>
                <p className="text-xs mt-1">
                  Data accumulates as the backend polls the Netatmo API.
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {!loading && !selected && stations.length === 0 && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="p-8 text-center text-slate-500">
            <Thermometer className="h-8 w-8 mx-auto mb-2 opacity-40" />
            <p>No stations found.</p>
            <p className="text-xs mt-1">
              Check Netatmo credentials in Settings and ensure the backend is
              running.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
