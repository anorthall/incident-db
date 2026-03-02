import { describe, it, expect, beforeEach } from "vitest";
import {
  getViewedIncidents,
  markIncidentViewed,
  isIncidentViewed,
  clearViewedIncidents,
} from "../viewed-incidents";

beforeEach(() => {
  localStorage.clear();
});

describe("viewed-incidents", () => {
  it("returns empty array when no history", () => {
    expect(getViewedIncidents()).toEqual([]);
  });

  it("adds viewed incident", () => {
    markIncidentViewed(1, "Cave Rescue");
    const viewed = getViewedIncidents();
    expect(viewed).toHaveLength(1);
    expect(viewed[0]).toEqual({ id: 1, title: "Cave Rescue" });
  });

  it("most recent is first", () => {
    markIncidentViewed(1, "First");
    markIncidentViewed(2, "Second");
    const viewed = getViewedIncidents();
    expect(viewed[0].id).toBe(2);
    expect(viewed[1].id).toBe(1);
  });

  it("deduplicates by moving to front", () => {
    markIncidentViewed(1, "First");
    markIncidentViewed(2, "Second");
    markIncidentViewed(1, "First Updated");

    const viewed = getViewedIncidents();
    expect(viewed).toHaveLength(2);
    expect(viewed[0]).toEqual({ id: 1, title: "First Updated" });
  });

  it("enforces max limit of 10", () => {
    for (let i = 0; i < 15; i++) {
      markIncidentViewed(i, `Incident ${i}`);
    }
    expect(getViewedIncidents()).toHaveLength(10);
    expect(getViewedIncidents()[0].id).toBe(14);
  });

  it("isIncidentViewed returns correct result", () => {
    markIncidentViewed(42, "Test");
    expect(isIncidentViewed(42)).toBe(true);
    expect(isIncidentViewed(99)).toBe(false);
  });

  it("clearViewedIncidents removes all", () => {
    markIncidentViewed(1, "Test");
    clearViewedIncidents();
    expect(getViewedIncidents()).toEqual([]);
  });

  it("handles corrupt localStorage gracefully", () => {
    localStorage.setItem("cidb-viewed-incidents", "not-json");
    expect(getViewedIncidents()).toEqual([]);
    expect(localStorage.getItem("cidb-viewed-incidents")).toBeNull();
  });
});
