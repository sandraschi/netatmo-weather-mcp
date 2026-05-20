import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Thermometer, Droplets, Wind, Gauge } from "lucide-react";
import { getHealth, getStations, getCurrentWeather, type StationSummary } from "@/common/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: Record<string, unknown>;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<string>("checking");

  useEffect(() => {
    (async () => {
      try {
        const h = await getHealth();
        setHealth(h.status);
        const s = await getStations();
        setStations(s.stations || []);
        if (s.stations?.length > 0) {
          const st = s.stations[0];
          setMessages([{
            role: "assistant",
            content: `Connected to Netatmo. ${s.stations.length} station(s) found. Ask me about weather data or type a station name.`,
          }]);
        } else {
          setMessages([{ role: "assistant", content: "Connected to Netatmo API. No stations found — check credentials in Settings." }]);
        }
      } catch {
        setHealth("unreachable");
        setMessages([{ role: "assistant", content: "Cannot reach Netatmo API server. Ensure the backend is running on port 10823." }]);
      }
    })();
  }, []);

  const send = async () => {
    if (!input.trim()) return;
    const q = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: q }]);
    setLoading(true);

    try {
      const target = stations.find(s => q.toLowerCase().includes(s.name.toLowerCase()));
      const stationId = target?.id || (stations[0]?.id);
      if (!stationId) {
        setMessages(prev => [...prev, { role: "assistant", content: "No stations available. Configure credentials in Settings." }]);
        setLoading(false);
        return;
      }
      const weather = await getCurrentWeather(stationId);
      const d = weather.data;
      const lines = [`**${target?.name || stations[0]?.name}** — ${weather.timestamp}`];
      if (d.temperature != null) lines.push(`Temperature: ${d.temperature}°C`);
      if (d.humidity != null) lines.push(`Humidity: ${d.humidity}%`);
      if (d.pressure != null) lines.push(`Pressure: ${d.pressure} hPa`);
      if (d.co2 != null) lines.push(`CO₂: ${d.co2} ppm`);
      if (d.noise != null) lines.push(`Noise: ${d.noise} dB`);
      if (d.rain != null) lines.push(`Rain: ${d.rain} mm`);
      if (d.wind_strength != null) lines.push(`Wind: ${d.wind_strength} m/s (${d.wind_angle ?? ""}°)`);

      setMessages(prev => [...prev, {
        role: "assistant",
        content: lines.join("\n"),
        data: d as Record<string, unknown>,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${(e as Error).message}` }]);
    }
    setLoading(false);
  };

  const icon = (role: string) => {
    if (role === "user") return <User className="h-4 w-4 text-slate-400" />;
    return <Bot className="h-4 w-4 text-emerald-400" />;
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Weather Query</h2>
          <p className="text-slate-400">
            API {health === "ok" ? "connected" : health === "unreachable" ? "offline" : "connecting…"}
            · {stations.length} station(s)
          </p>
        </div>
      </div>

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <p className="text-slate-500 text-sm">Loading stations…</p>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className="flex gap-3">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center border ${msg.role === "user" ? "bg-slate-800 border-slate-700" : "bg-emerald-900/20 border-emerald-800"}`}>
                  {icon(msg.role)}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${msg.role === "user" ? "text-slate-200" : "text-emerald-400"}`}>
                      {msg.role === "user" ? "You" : "Weather AI"}
                    </span>
                  </div>
                  <div className={`text-sm p-3 rounded-md border inline-block ${msg.role === "user" ? "text-slate-300 bg-slate-900/50 border-slate-800" : "text-slate-300 bg-emerald-950/10 border-emerald-900/30"}`}>
                    <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
                    {msg.data && (
                      <div className="flex gap-3 mt-2 text-xs text-slate-400">
                        {msg.data.temperature != null && <span className="flex items-center gap-1"><Thermometer className="h-3 w-3" />{msg.data.temperature as number}°C</span>}
                        {msg.data.humidity != null && <span className="flex items-center gap-1"><Droplets className="h-3 w-3" />{msg.data.humidity as number}%</span>}
                        {msg.data.wind_strength != null && <span className="flex items-center gap-1"><Wind className="h-3 w-3" />{msg.data.wind_strength as number} m/s</span>}
                        {msg.data.pressure != null && <span className="flex items-center gap-1"><Gauge className="h-3 w-3" />{msg.data.pressure as number} hPa</span>}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-none"
              placeholder="Ask about weather, or type a station name…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !loading && send()}
            />
            <Button size="icon" className="bg-emerald-600 hover:bg-emerald-700" disabled={loading || !input.trim()} onClick={send}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
