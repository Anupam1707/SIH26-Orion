import { NavLink } from "react-router-dom";
import { PERSONA_FOCUS, SCREENS } from "../lib/screens";
import { usePersona } from "./PersonaContext";

export function Sidebar() {
  const { persona } = usePersona();
  const focus = PERSONA_FOCUS[persona];

  return (
    <nav aria-label="Screens" className="flex w-56 shrink-0 flex-col gap-1 border-r border-line bg-ink-900 p-3">
      {SCREENS.map((s) => {
        const highlighted = focus.includes(s.path);
        return (
          <NavLink
            key={s.path}
            to={s.path}
            className={({ isActive }) =>
              [
                "flex items-center justify-between rounded px-3 py-2 text-base",
                isActive ? "bg-ink-600 text-fg" : "text-fg-dim hover:bg-ink-700 hover:text-fg",
              ].join(" ")
            }
          >
            {s.label}
            {highlighted && (
              <span className="h-2 w-2 rounded-full bg-accent" title={`Key screen for ${persona}`} aria-label="Key screen" />
            )}
          </NavLink>
        );
      })}
    </nav>
  );
}
