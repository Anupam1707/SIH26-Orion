import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "./api/client";
import { PersonaProvider, usePersona } from "./components/PersonaContext";
import { ScreenStub } from "./components/ScreenStub";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { PERSONA_HOME, SCREENS } from "./lib/screens";
import { CommandCenter } from './screens/CommandCenter';
import { CaseView } from './screens/CaseView';
import { RiskHeatmap } from './screens/RiskHeatmap';
import { Alerts } from './screens/Alerts';
import { FundBlocking } from './screens/FundBlocking';

function Shell() {
  const { persona } = usePersona();
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    let alive = true;
    const check = () =>
      api
        .health()
        .then(() => alive && setBackendOk(true))
        .catch(() => alive && setBackendOk(false));
    void check();
    const t = setInterval(check, 5000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  // Poll alert count for the notification bell.
  useEffect(() => {
    let alive = true;
    const poll = () => api.alerts().then(a => {
      if (alive) setAlertCount(a.filter(x => x.status === 'triggered').length);
    }).catch(() => {});
    void poll();
    const t = setInterval(poll, 5000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  return (
    <div className="flex h-full flex-col">
      <TopBar backendOk={backendOk} alertCount={alertCount} />
      <div className="shell-body flex min-h-0 flex-1">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/" element={<Navigate to={PERSONA_HOME[persona]} replace />} />
            {SCREENS.map((s) => (
              <Route key={s.path} path={s.path} element={s.path === '/command-center' ? <CommandCenter /> : s.path === '/case' ? <CaseView /> : s.path === '/heatmap' ? <RiskHeatmap /> : s.path === '/alerts' ? <Alerts /> : s.path === '/blocking' ? <FundBlocking /> : <ScreenStub screen={s} />} />
            ))}
            <Route path="*" element={<Navigate to={PERSONA_HOME[persona]} replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <PersonaProvider>
      <Shell />
    </PersonaProvider>
  );
}
