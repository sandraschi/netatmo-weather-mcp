import {
  type CurrentWeatherResponse,
  type StationsResponse,
  getCurrentWeather,
  getHealth,
  getStations,
} from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Activity,
  AlertCircle,
  CloudRain,
  Droplets,
  Gauge,
  Radio,
  Thermometer,
  Trophy,
  Wind,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function windDegToDir(deg: number | undefined | null): string {
  if (deg == null) return "";
  const dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return dirs[Math.round(deg / 22.5) % 16];
}

function KpiCard({
  title,
  value,
  unit,
  icon,
  subtitle,
  color,
  ...rest
}: {
  title: string;
  value: string;
  unit?: string;
  icon: React.ReactNode;
  subtitle?: string;
  color: string;
  "data-testid"?: string;
}) {
  return (
    <Card className="border-slate-800 bg-slate-950/50" {...rest}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-slate-200">
          {title}
        </CardTitle>
        <span style={{ color }}>{icon}</span>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">
          {value}
          {unit && <span className="text-sm font-normal text-slate-400 ml-1">{unit}</span>}
        </div>
        {subtitle && (
          <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}

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
    return () => {
      cancelled = true;
    };
  }, []);

  const firstStation = stations?.stations?.[0];
  const modulesCount = firstStation?.modules_count ?? 0;
  const d = weather?.data;

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Weather Dashboard
          </h2>
          <p className="text-slate-400">
            Netatmo station and environmental telemetry
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-800 bg-amber-950/50 p-4 text-amber-200 space-y-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <p className="text-sm">
              {error}. Run web_sota\\start.ps1 to start backend and frontend.
            </p>
          </div>
          <Link
            to="/onboarding"
            className="text-sm text-emerald-400 hover:text-emerald-300 underline"
          >
            Get started with Netatmo credentials
          </Link>
        </div>
      )}

      <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard
          title="Stations"
          value={stations == null ? "\u2014" : String(stations.total_count)}
          icon={<CloudRain className="h-4 w-4" />}
          subtitle={stations == null ? "Loading..." : `${modulesCount} modules`}
          color="#10b981"
          data-testid="kpi-stations"
        />
        <KpiCard
          title="Online"
          value={stations == null ? "\u2014" : String(stations.reachable_count)}
          icon={<Activity className="h-4 w-4" />}
          subtitle={stations == null ? "" : "reachable"}
          color="#3b82f6"
          data-testid="kpi-reachable"
        />
        <KpiCard
          title="Temperature"
          value={d?.temperature != null ? String(d.temperature) : "\u2014"}
          unit={d?.temperature != null ? "\u00b0C" : undefined}
          icon={<Thermometer className="h-4 w-4" />}
          color="#fb7185"
          data-testid="kpi-temperature"
        />
        <KpiCard
          title="Humidity"
          value={d?.humidity != null ? String(d.humidity) : "\u2014"}
          unit={d?.humidity != null ? "%" : undefined}
          icon={<Droplets className="h-4 w-4" />}
          color="#38bdf8"
          data-testid="kpi-humidity"
        />
        <KpiCard
          title="Pressure"
          value={d?.pressure != null ? String(d.pressure) : "\u2014"}
          unit={d?.pressure != null ? "hPa" : undefined}
          icon={<Gauge className="h-4 w-4" />}
          color="#fbbf24"
          data-testid="kpi-pressure"
        />
        <KpiCard
          title="CO2"
          value={d?.co2 != null ? String(d.co2) : "\u2014"}
          unit={d?.co2 != null ? "ppm" : undefined}
          icon={<Trophy className="h-4 w-4" />}
          color="#34d399"
          data-testid="kpi-co2"
        />
      </div>

      <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard
          title="Noise"
          value={d?.noise != null ? String(d.noise) : "\u2014"}
          unit={d?.noise != null ? "dB" : undefined}
          icon={<Radio className="h-4 w-4" />}
          color="#a78bfa"
        />
        <KpiCard
          title="Rain"
          value={d?.rain != null ? String(d.rain) : "\u2014"}
          unit={d?.rain != null ? "mm" : undefined}
          icon={<CloudRain className="h-4 w-4" />}
          color="#22d3ee"
        />
        <KpiCard
          title="Wind"
          value={d?.wind_strength != null ? String(d.wind_strength) : "\u2014"}
          unit={d?.wind_strength != null ? "km/h" : undefined}
          subtitle={d?.wind_angle != null ? windDegToDir(d.wind_angle) : undefined}
          icon={<Wind className="h-4 w-4" />}
          color="#818cf8"
        />
        <KpiCard
          title="Gust"
          value={d?.gust_strength != null ? String(d.gust_strength) : "\u2014"}
          unit={d?.gust_strength != null ? "km/h" : undefined}
          icon={<Wind className="h-4 w-4" />}
          color="#c084fc"
        />
        <KpiCard
          title="Backend"
          value={healthOk === null ? "\u2014" : healthOk ? "Online" : "Offline"}
          icon={<Activity className="h-4 w-4" />}
          subtitle={healthOk === true ? "127.0.0.1:10823" : healthOk === false ? "Not connected" : "Checking..."}
          color={healthOk === true ? "#10b981" : healthOk === false ? "#ef4444" : "#6b7280"}
          data-testid="kpi-backend"
        />
      </div>
    </div>
  );
}
