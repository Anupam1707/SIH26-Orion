import type { ScreenDef } from "../lib/screens";

/** Placeholder body for a screen that a later phase will build. */
export function ScreenStub({ screen }: { screen: ScreenDef }) {
  return (
    <section className="max-w-3xl">
      <h2 className="text-2xl font-semibold">{screen.label}</h2>
      <p className="mt-2 text-fg-dim">{screen.blurb}</p>
      <p className="mt-6 rounded border border-dashed border-line bg-ink-800 p-4 text-sm text-fg-dim">
        Not built yet — arrives in Phase {screen.phase}.
      </p>
    </section>
  );
}
