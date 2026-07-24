import { AppLayout } from "@/components/layout/app-layout";
import Logging from "@/pages/Logging";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Onboarding } from "@/pages/onboarding";
import { Settings } from "@/pages/settings";
import { Stations } from "@/pages/stations";
import { Trends } from "@/pages/trends";
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/stations" element={<Stations />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/logging" element={<Logging />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
