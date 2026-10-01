import { describe, expect, it } from "vitest";
import { formatInr, formatIst, formatIstTime } from "./format";

describe("formatInr", () => {
  it("uses Indian digit grouping below one lakh", () => {
    expect(formatInr(0)).toBe("₹0");
    expect(formatInr(950)).toBe("₹950");
    expect(formatInr(50_000)).toBe("₹50,000");
    expect(formatInr(99_949)).toBe("₹99,949");
  });
  it("switches to lakh and crore", () => {
    expect(formatInr(100_000)).toBe("₹1 lakh");
    expect(formatInr(120_000)).toBe("₹1.2 lakh");
    expect(formatInr(2_500_000)).toBe("₹25 lakh");
    expect(formatInr(10_000_000)).toBe("₹1 crore");
    expect(formatInr(34_000_000)).toBe("₹3.4 crore");
  });
  it("promotes values that round up to 100 lakh", () => {
    expect(formatInr(9_996_000)).toBe("₹1 crore");
  });
  it("handles negatives and non-finite input", () => {
    expect(formatInr(-120_000)).toBe("-₹1.2 lakh");
    expect(formatInr(Number.NaN)).toBe("—");
  });
});

describe("IST formatting", () => {
  it("renders IST regardless of the offset in the input", () => {
    expect(formatIstTime("2026-08-30T10:15:00+05:30")).toBe("10:15");
    expect(formatIstTime("2026-08-30T04:45:00Z")).toBe("10:15");
    expect(formatIst("2026-08-30T04:45:00Z")).toBe("30 Aug 2026, 10:15 IST");
  });
  it("does not throw on bad input", () => {
    expect(formatIst("not a date")).toBe("—");
  });
});
