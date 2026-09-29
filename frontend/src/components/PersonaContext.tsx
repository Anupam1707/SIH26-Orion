import { createContext, useContext, useState, type ReactNode } from "react";
import { PERSONAS, type Persona } from "../lib/screens";

interface PersonaCtx {
  persona: Persona;
  setPersona: (p: Persona) => void;
}

const Ctx = createContext<PersonaCtx | null>(null);

function initial(): Persona {
  try {
    const saved = localStorage.getItem("muletrail.persona");
    return PERSONAS.find((p) => p === saved) ?? "I4C";
  } catch {
    return "I4C";
  }
}

export function PersonaProvider({ children }: { children: ReactNode }) {
  const [persona, setState] = useState<Persona>(initial);
  const setPersona = (p: Persona) => {
    setState(p);
    try {
      localStorage.setItem("muletrail.persona", p);
    } catch {
      /* storage unavailable: the choice just won't persist */
    }
  };
  return <Ctx.Provider value={{ persona, setPersona }}>{children}</Ctx.Provider>;
}

export function usePersona(): PersonaCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("usePersona must be used inside PersonaProvider");
  return v;
}
