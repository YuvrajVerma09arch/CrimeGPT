import { describe, expect, it } from "vitest";
import {
  formatDate,
  formatDateTime,
  relevancePercent,
  STATUS_COLORS,
} from "../utils/format";

describe("format utils", () => {
  it("formats ISO dates", () => {
    expect(formatDate("2026-01-05")).toBe("05 Jan 2026");
  });

  it("returns a dash for empty values", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDateTime(undefined)).toBe("—");
  });

  it("converts relevance scores to clamped percentages", () => {
    expect(relevancePercent(0.87)).toBe(87);
    expect(relevancePercent(1.4)).toBe(100);
    expect(relevancePercent(-0.2)).toBe(0);
    expect(relevancePercent(null)).toBe(0);
  });

  it("has a color for every case status", () => {
    for (const status of ["OPEN", "ARRESTED", "CHARGESHEETED", "CLOSED"]) {
      expect(STATUS_COLORS[status]).toBeTruthy();
    }
  });
});
