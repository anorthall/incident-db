const VIEWED_KEY = "cidb-viewed-incidents";
const MAX_VIEWED = 10;
const VIEWED_CHANGE_EVENT = "cidb-viewed-change";

export interface ViewedIncident {
  id: number;
  title: string;
}

export function getViewedIncidents(): ViewedIncident[] {
  if (typeof window === "undefined") return [];
  const saved = localStorage.getItem(VIEWED_KEY);
  if (!saved) return [];
  try {
    return JSON.parse(saved) as ViewedIncident[];
  } catch {
    localStorage.removeItem(VIEWED_KEY);
    return [];
  }
}

export function isIncidentViewed(id: number): boolean {
  return getViewedIncidents().some((v) => v.id === id);
}

export function markIncidentViewed(id: number, title: string): void {
  const viewed = getViewedIncidents();
  const filtered = viewed.filter((v) => v.id !== id);
  const updated = [{ id, title }, ...filtered].slice(0, MAX_VIEWED);
  localStorage.setItem(VIEWED_KEY, JSON.stringify(updated));
  window.dispatchEvent(new CustomEvent(VIEWED_CHANGE_EVENT));
}

export function clearViewedIncidents(): void {
  localStorage.removeItem(VIEWED_KEY);
  window.dispatchEvent(new CustomEvent(VIEWED_CHANGE_EVENT));
}

export function onViewedIncidentsChange(callback: () => void): () => void {
  window.addEventListener(VIEWED_CHANGE_EVENT, callback);
  return () => window.removeEventListener(VIEWED_CHANGE_EVENT, callback);
}
