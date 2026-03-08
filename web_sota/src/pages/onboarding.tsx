import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CloudRain, Settings, LayoutDashboard, ExternalLink, Key, Mail, Lock } from "lucide-react";

const DEV_NETATMO = "https://dev.netatmo.com";

export function Onboarding() {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <CloudRain className="h-12 w-12 text-emerald-500 mx-auto" />
        <h1 className="text-3xl font-bold text-white">Welcome to Netatmo Weather</h1>
        <p className="text-slate-400 max-w-xl mx-auto">
          Connect your Netatmo weather station in a few steps. You will need a Netatmo account and an app from the developer portal.
        </p>
      </div>

      <div className="grid gap-6 max-w-2xl mx-auto">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <span className="rounded-full bg-slate-700 text-slate-200 w-7 h-7 flex items-center justify-center text-sm">1</span>
              Create a Netatmo app
            </CardTitle>
            <CardDescription className="text-slate-400">
              Go to the Netatmo developer portal and create an app to get your Client ID and Client secret.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <a
              href={DEV_NETATMO}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 text-sm"
            >
              <ExternalLink className="h-4 w-4" />
              dev.netatmo.com
            </a>
            <p className="text-sm text-slate-500">
              Sign in with your Netatmo account, then open <strong>My account</strong> and <strong>Create an app</strong>. Note the <strong>Client ID</strong> and <strong>Client secret</strong>.
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <span className="rounded-full bg-slate-700 text-slate-200 w-7 h-7 flex items-center justify-center text-sm">2</span>
              Enter credentials in Settings
            </CardTitle>
            <CardDescription className="text-slate-400">
              In this app, open Settings and enter the four values. They are stored in memory for the session only.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <ul className="text-sm text-slate-400 space-y-1">
              <li className="flex items-center gap-2">
                <Key className="h-4 w-4 text-slate-500" />
                Client ID (from the app)
              </li>
              <li className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-slate-500" />
                Client secret (from the app)
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-slate-500" />
                Username (your Netatmo account email)
              </li>
              <li className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-slate-500" />
                Password (your Netatmo account password)
              </li>
            </ul>
            <Link to="/settings">
              <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">
                <Settings className="h-4 w-4 mr-2" />
                Open Settings
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <span className="rounded-full bg-slate-700 text-slate-200 w-7 h-7 flex items-center justify-center text-sm">3</span>
              View your stations
            </CardTitle>
            <CardDescription className="text-slate-400">
              After saving credentials, the Dashboard and Stations pages will show data from your Netatmo account. Stations are loaded from the Netatmo cloud (no local network discovery).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/">
              <Button variant="outline" className="border-slate-700 text-slate-200 hover:bg-slate-800">
                <LayoutDashboard className="h-4 w-4 mr-2" />
                Go to Dashboard
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
