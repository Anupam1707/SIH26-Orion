/** ₹ lakh/crore formatting and IST time formatting (spec §14). */

const LAKH = 100_000;
const CRORE = 10_000_000;
const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function scaled(n: number, unit: number, name: string): string {
  const v = Math.round((n / unit) * 10) / 10;
  return `${v.toFixed(1).replace(/\.0$/, "")} ${name}`;
}

/** ₹50,000 · ₹1.2 lakh · ₹3.4 crore. Negative values keep their sign. */
export function formatInr(amount: number): string {
  if (!Number.isFinite(amount)) return "—";
  const sign = amount < 0 ? "-" : "";
  const n = Math.abs(amount);
  if (n < LAKH) return `${sign}₹${inr.format(Math.round(n))}`;
  if (n < CRORE) {
    // 99.96 lakh rounds to 100.0 lakh, which is really 1 crore.
    if (Math.round((n / LAKH) * 10) / 10 >= 100) return `${sign}₹${scaled(n, CRORE, "crore")}`;
    return `${sign}₹${scaled(n, LAKH, "lakh")}`;
  }
  return `${sign}₹${scaled(n, CRORE, "crore")}`;
}

const IST = "Asia/Kolkata";

/** e.g. "30 Aug 2026, 10:15 IST" — always IST, whatever the browser's zone. */
export function formatIst(ts: string | Date): string {
  const d = typeof ts === "string" ? new Date(ts) : ts;
  if (Number.isNaN(d.getTime())) return "—";
  const date = new Intl.DateTimeFormat("en-IN", {
    timeZone: IST, day: "numeric", month: "short", year: "numeric",
  }).format(d);
  return `${date}, ${formatIstTime(d)} IST`;
}

/** e.g. "10:15" (24-hour, IST). */
export function formatIstTime(ts: string | Date): string {
  const d = typeof ts === "string" ? new Date(ts) : ts;
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: IST, hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(d);
}
