import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

export function Trends() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Trends</h2>
        <p className="text-slate-400">Weather history and trends (historical API coming soon)</p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-amber-500" />
            Historical data
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-400 text-sm">
            Use the MCP tool <code className="rounded bg-slate-800 px-1">weather_data_operations</code> with
            operation <code className="rounded bg-slate-800 px-1">historical</code> for time-series data.
            Charts can be added here once the backend exposes a history endpoint.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
