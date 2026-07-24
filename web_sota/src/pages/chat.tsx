import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Thermometer, Droplets, Wind, Gauge, Download, Trash2, Loader2 } from "lucide-react";
import { getHealth, getStations, getCurrentWeather, type StationSummary } from "@/common/api";

const LS_KEY = "netatmo-mcp-chat-history";
const PERS_KEY = "netatmo-mcp-chat-personality";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: Record<string, unknown>;
}

const PERSONALITIES = [
  { id: "weather-expert", label: "Weather Expert", prompt: "You are a knowledgeable weather expert. Explain weather data clearly." },
  { id: "data-analyst", label: "Data Analyst", prompt: "You are a data analyst focused on weather patterns and trends." },
  { id: "quick-summarizer", label: "Quick Summarizer", prompt: "You are a concise summarizer. Keep responses short." },
  { id: "custom", label: "Custom", prompt: "" },
];

const EXAMPLE_PROMPTS = [
  { group: "Weather", items: [
    "What's the current temperature?",
    "Show me humidity and CO2 levels",
    "Is it going to rain?",
  ]},
  { group: "Analysis", items: [
    "Compare all station readings",
    "What's the pressure trend?",
    "Show wind conditions",
  ]},
  { group: "Stations", items: [
    "List all my weather stations",
    "Which station has the highest temp?",
    "Station health check",
  ]},
];

function loadHistory(): Message[] {
  try { const d = localStorage.getItem(LS_KEY); return d ? JSON.parse(d) : []; } catch { return []; }
}

function saveHistory(msgs: Message[]) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(msgs.slice(-100))); } catch {}
}

function loadPersonality(): string {
  try { return localStorage.getItem(PERS_KEY) || "weather-expert"; } catch { return "weather-expert"; }
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => loadHistory());
  const [input, setInput] = useState("");
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<string>("checking");
  const [personalityId, setPersonalityId] = useState(() => loadPersonality());
  const [showExamples, setShowExamples] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => { saveHistory(messages); }, [messages]);

  useEffect(() => {
    localStorage.setItem(PERS_KEY, personalityId);
  }, [personalityId]);

  useEffect(() => {
    (async () => {
      try {
        const h = await getHealth();
        setHealth(h.status);
        const s = await getStations();
        setStations(s.stations || []);
        if (messages.length === 0) {
          if (s.stations?.length > 0) {
            setMessages([{
              role: "assistant",
              content: `Connected to Netatmo. ${s.stations.length} station(s) found. Ask me about weather data or type a station name.`,
            }]);
          } else {
            setMessages([{ role: "assistant", content: "Connected to Netatmo API. No stations found — check credentials in Settings." }]);
          }
        }
      } catch {
        setHealth("unreachable");
        if (messages.length === 0) {
          setMessages([{ role: "assistant", content: "Cannot reach Netatmo API server. Ensure the backend is running on port 10823." }]);
        }
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const send = async () => {
    if (!input.trim()) return;
    const q = input.trim();
    setInput("");
    const userMsg: Message = { role: "user", content: q };
    setMessages(prev => [...prev, userMsg]);
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

  const exportChat = () => {
    const text = messages.map(m => `${m.role === "user" ? "You" : "Weather AI"}: ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `netatmo-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const icon = (role: string) => {
    if (role === "user") return <User className="h-4 w-4 text-slate-400" />;
    return <Bot className="h-4 w-4 text-emerald-400" />;
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4" data-testid="chat-page">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-white">Weather Query</h2>
            <span className="text-xs text-emerald-400 bg-emerald-900/30 px-2 py-0.5 rounded border border-emerald-800/50" data-testid="skill-badge">netatmo-weather</span>
          </div>
          <p className="text-slate-400" data-testid="chat-controls">
            API <span className={`inline-block w-2 h-2 rounded-full ${health === "ok" ? "bg-green-500" : health === "unreachable" ? "bg-red-500" : "bg-yellow-500 animate-pulse"}`} data-testid="backend-dot" />
            {health === "ok" ? " connected" : health === "unreachable" ? " offline" : " connecting..."}
            · {stations.length} station(s)
          </p>
        </div>
        <div className="flex items-center gap-2" data-testid="chat-controls">
          <select
            value={personalityId}
            onChange={(e) => setPersonalityId(e.target.value)}
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200"
            data-testid="personality-select"
          >
            {PERSONALITIES.map(p => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
          <Button variant="outline" size="sm" onClick={exportChat} disabled={messages.length === 0} className="h-8 text-xs gap-1" data-testid="chat-export">
            <Download className="h-3 w-3" /> Export
          </Button>
          <Button variant="outline" size="sm" onClick={() => setMessages([])} disabled={messages.length === 0} className="h-8 text-xs gap-1 text-red-400 border-red-900/30 hover:bg-red-950/20" data-testid="chat-clear">
            <Trash2 className="h-3 w-3" /> Clear
          </Button>
        </div>
      </div>

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden" data-testid="dashboard">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="chat-messages">
          {messages.length === 0 ? (
            <p className="text-slate-500 text-sm">Loading stations...</p>
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
          {loading && (
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-emerald-900/20 border border-emerald-800 flex items-center justify-center">
                <Loader2 className="h-4 w-4 text-emerald-400 animate-spin" />
              </div>
              <span className="text-sm text-slate-500">Thinking...</span>
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          {messages.length === 0 && (
            <div className="mb-3" data-testid="example-prompts">
              <button
                type="button"
                onClick={() => setShowExamples(!showExamples)}
                className="text-xs text-slate-500 hover:text-slate-300 mb-2"
              >
                {showExamples ? "Hide" : "Show"} example prompts
              </button>
              {showExamples && (
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_PROMPTS.flatMap(g => g.items).map((p, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setInput(p)}
                      className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded border border-slate-700 transition-colors"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-none"
              placeholder="Ask about weather, or type a station name..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !loading && send()}
              data-testid="chat-input"
            />
            <Button size="icon" className="bg-emerald-600 hover:bg-emerald-700" disabled={loading || !input.trim()} onClick={send} data-testid="chat-send">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
