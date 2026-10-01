import { useNavigate } from "react-router-dom";
import { PERSONAS, PERSONA_HOME, type Persona } from "../lib/screens";
import { usePersona } from "./PersonaContext";

export function TopBar({
  backendOk,
  alertCount,
  mode,
}: {
  backendOk: boolean | null;
  alertCount: number;
  mode?: "live" | "simulated" | null;
}) {
  const { persona, setPersona } = usePersona();
  const navigate = useNavigate();

  const onPersona = (p: Persona) => {
    setPersona(p);
    navigate(PERSONA_HOME[p]); // persona switch changes the default screen (spec §14)
  };

  const getStatus = () => {
    if (backendOk === null) {
      return { text: "Connecting…", cls: "text-fg-dim", title: "Checking backend connection..." };
    }
    if (backendOk) {
      if (mode === "simulated") {
        return {
          text: "Demo Simulation (Vercel)",
          cls: "text-accent font-medium",
          title: "Running authenticated precomputed scenario. Fully interactive without external server.",
        };
      }
      return {
        text: "Backend online",
        cls: "text-ok",
        title: "Connected to live FastAPI backend.",
      };
    }
    return {
      text: "Backend offline",
      cls: "text-danger",
      title: "Backend unreachable.",
    };
  };

  const status = getStatus();

  return (
    <header className="flex items-center gap-4 border-b border-line bg-ink-900 px-5 py-3">
      <div
        className="flex items-center gap-3 cursor-pointer select-none"
        onClick={() => navigate(PERSONA_HOME[persona])}
        title="ORION: Graph-Aware Prediction of Cyber-Fraud Cash-Out Hotspots and Fund-Freezing Recommendations"
      >
        <img
          src="/orion-logo-horizontal.png"
          alt="ORION"
          className="h-7 w-auto object-contain transition-opacity hover:opacity-90"
        />
        <span className="text-xs text-fg-dim font-mono hidden md:inline border-l border-line pl-3">
          PS 26184 · MHA / I4C
        </span>
      </div>

      {/* Persistent on every screen: nothing here is real data (spec §2). */}
      <span
        className="rounded border border-warn px-2 py-0.5 text-xs font-medium text-warn"
        title="All names, accounts, transactions and coordinates are fictional."
      >
        Simulated data
      </span>

      <span
        className={`text-sm flex items-center gap-1.5 ${status.cls}`}
        role="status"
        title={status.title}
      >
        <span className={`inline-block h-2 w-2 rounded-full ${backendOk ? (mode === "simulated" ? "bg-accent animate-pulse" : "bg-ok") : "bg-danger"}`} />
        {status.text}
      </span>

      <div className="ml-auto flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-fg-dim">
          Persona
          <select
            value={persona}
            onChange={(e) => onPersona(e.target.value as Persona)}
            className="rounded border border-line bg-ink-800 px-2 py-1 text-fg"
          >
            {PERSONAS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={() => navigate("/alerts")}
          aria-label={`Notifications, ${alertCount} unread`}
          className="relative rounded border border-line bg-ink-800 px-3 py-1 text-fg hover:bg-ink-700"
        >
          <span aria-hidden>🔔</span>
          {alertCount > 0 && (
            <span className="absolute -right-2 -top-2 rounded-full bg-danger px-1.5 text-xs font-semibold text-ink-950">
              {alertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
