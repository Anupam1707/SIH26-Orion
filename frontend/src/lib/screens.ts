/** The six screens (spec §14) and the personas that pick a default one. */

export interface ScreenDef {
  path: string;
  label: string;
  blurb: string;
  phase: number;
}

export const SCREENS: readonly ScreenDef[] = [
  { path: "/command-center", label: "Command Center", blurb: "KPI strip, complaint feed and a mini map of live cases.", phase: 2 },
  { path: "/case", label: "Case View", blurb: "Follow the money hop by hop, with the laundering pattern and its signals.", phase: 2 },
  { path: "/heatmap", label: "Risk Heatmap", blurb: "Where the stolen cash is most likely to come out, with reasons.", phase: 3 },
  { path: "/alerts", label: "Alerts", blurb: "Mock alerts to police and banks, with delivery status.", phase: 4 },
  { path: "/blocking", label: "Fund Blocking", blurb: "Which accounts to freeze, and how much money that stops.", phase: 4 },
  { path: "/adversary", label: "Adversary Lab", blurb: "What it costs a criminal to evade the predictions.", phase: 5 },
];

export type Persona = "I4C" | "Investigator" | "Bank officer";
export const PERSONAS: readonly Persona[] = ["I4C", "Investigator", "Bank officer"];

/** Default landing screen per persona. */
export const PERSONA_HOME: Record<Persona, string> = {
  I4C: "/command-center",
  Investigator: "/case",
  "Bank officer": "/blocking",
};

/** Screens each persona is expected to act on; the sidebar highlights these. */
export const PERSONA_FOCUS: Record<Persona, readonly string[]> = {
  I4C: ["/command-center", "/heatmap"],
  Investigator: ["/case", "/heatmap", "/alerts"],
  "Bank officer": ["/blocking", "/alerts"],
};
