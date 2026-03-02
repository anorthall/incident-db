import { parseAuthHeaders } from "./auth-api";
import { notifyAuthUpdate } from "./auth-sync";
import { getCsrfToken } from "./csrf";
import { captureApiError } from "./sentry";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";
const API_MAX_RETRIES = 3;
const API_RETRY_DELAY_MS = 1000;

function syncAuthFromResponse(response: Response) {
  const authHeader = response.headers.get("CIDB-User-Authenticated");
  if (authHeader === null) return;

  const user = parseAuthHeaders(response.headers);
  notifyAuthUpdate(user);
}

async function fetchWithRetry(
  url: string,
  options?: RequestInit,
  retries = API_MAX_RETRIES
): Promise<Response> {
  const method = options?.method || "GET";
  let lastError: Error | null = null;

  const csrfToken = getCsrfToken();
  const csrfHeaders: Record<string, string> =
    csrfToken && method !== "GET" ? { "X-CSRFToken": csrfToken } : {};

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const mergedOptions: RequestInit = {
        ...options,
        credentials: "include",
        headers: { ...csrfHeaders, ...options?.headers },
      };
      const response = await fetch(url, mergedOptions);

      syncAuthFromResponse(response);

      if (response.ok) {
        return response;
      }

      if (response.status >= 500 && attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, API_RETRY_DELAY_MS * attempt));
        continue;
      }

      return response;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, API_RETRY_DELAY_MS * attempt));
        continue;
      }

      captureApiError(lastError, {
        endpoint: url,
        method,
        attempt,
      });
    }
  }

  throw lastError || new Error("Request failed after retries");
}

export interface ImpreciseDate {
  raw: string;
  display: string;
  year: number;
  month: number | null;
  day: number | null;
  season: string | null;
  precision: "year" | "season" | "month" | "day";
}

export interface Tag {
  id: number;
  name: string;
}

export interface Location {
  id: number;
  country: string;
  state: string;
  region: string;
  latitude: number | null;
  longitude: number | null;
}

export interface Cave {
  id: number;
  name: string;
  location: Location | null;
}

export interface Publication {
  id: number;
  title: string;
}

export interface IncidentReference {
  author: string;
  title: string;
  source: string;
  raw_citation: string;
}

export interface IncidentListItem {
  id: number;
  title: string;
  date: ImpreciseDate | null;
  cave_name: string;
  location_summary: string;
  summary: string;
  tags: Tag[];
  view_count: number;
  relevance_score: number | null;
}

export interface IncidentDetail {
  id: number;
  title: string;
  date: ImpreciseDate | null;
  time: string | null;
  cave: Cave | null;
  report: string;
  analysis: string;
  summary: string;
  tags: Tag[];
  origin_publication: Publication | null;
  references: IncidentReference[];
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type SortField = "date" | "relevance" | "popularity" | "title" | "cave_name";
export type SortOrder = "asc" | "desc";

export interface SearchParams {
  q?: string;
  sort_by?: SortField;
  sort_order?: SortOrder;
  page?: number;
  page_size?: number;
}

export interface CreateReportParams {
  incident_id: number | null;
  reason: string;
  description?: string;
  email?: string;
  url?: string;
}

export interface ReportResponse {
  id: number;
  status: string;
  message: string;
}

export const ReportReasons = {
  inaccurate: "Inaccurate Information",
  incomplete: "Missing Information",
  duplicate: "Duplicate Entry",
  typo: "Typographical Error",
  formatting: "Formatting Error",
  privacy: "Privacy Concern",
  offensive: "Offensive Content",
  other: "Other",
} as const;

export type ReportReason = keyof typeof ReportReasons;

export async function searchIncidents(
  params: SearchParams
): Promise<PaginatedResponse<IncidentListItem>> {
  const searchParams = new URLSearchParams();

  if (params.q) searchParams.set("q", params.q);
  if (params.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params.sort_order) searchParams.set("sort_order", params.sort_order);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));

  const response = await fetchWithRetry(
    `${API_BASE_URL}/incidents/search?${searchParams.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getIncident(id: number): Promise<IncidentDetail> {
  const response = await fetchWithRetry(`${API_BASE_URL}/incidents/${id}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch incident: ${response.statusText}`);
  }

  return response.json();
}

export async function createReport(params: CreateReportParams): Promise<ReportResponse> {
  const response = await fetchWithRetry(`${API_BASE_URL}/reports/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`Failed to create report: ${response.statusText}`);
  }

  return response.json();
}

export interface SuggestionsResponse {
  suggestions: string[];
}

export interface DidYouMeanResponse {
  suggestion: string | null;
  similarity: number | null;
}

export async function getSearchSuggestions(q: string): Promise<SuggestionsResponse> {
  if (q.length < 2) {
    return { suggestions: [] };
  }

  try {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/incidents/suggestions?q=${encodeURIComponent(q)}`,
      undefined,
      2
    );

    if (!response.ok) {
      return { suggestions: [] };
    }

    return response.json();
  } catch {
    return { suggestions: [] };
  }
}

export async function getDidYouMean(q: string): Promise<DidYouMeanResponse> {
  if (q.length < 2) {
    return { suggestion: null, similarity: null };
  }

  try {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/incidents/did-you-mean?q=${encodeURIComponent(q)}`,
      undefined,
      2
    );

    if (!response.ok) {
      return { suggestion: null, similarity: null };
    }

    return response.json();
  } catch {
    return { suggestion: null, similarity: null };
  }
}

export async function trackSearchClick(
  query: string,
  incidentId: number,
  position: number
): Promise<void> {
  try {
    await fetchWithRetry(
      `${API_BASE_URL}/incidents/click`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          incident_id: incidentId,
          position,
        }),
      },
      2
    );
  } catch {
    // Click tracking failures are non-critical
  }
}

export async function getRandomIncidentId(): Promise<number | null> {
  try {
    const countResponse = await searchIncidents({ page: 1, page_size: 1 });
    const total = countResponse.total;
    if (total === 0) return null;

    const randomOffset = Math.floor(Math.random() * total);
    const randomPage = Math.floor(randomOffset) + 1;

    const response = await searchIncidents({
      page: randomPage,
      page_size: 1,
      sort_by: "date",
      sort_order: "desc",
    });

    if (response.items.length > 0) {
      return response.items[0].id;
    }
    return null;
  } catch {
    return null;
  }
}

export interface FeedbackReporter {
  id: string;
  email: string | null;
}

export interface FeedbackIncident {
  id: number;
  title: string;
}

export interface FeedbackListItem {
  id: number;
  incident: FeedbackIncident | null;
  url: string;
  reason: string;
  reason_display: string;
  description: string;
  status: string;
  status_display: string;
  reporter: FeedbackReporter | null;
  created_at: string;
  updated_at: string;
}

export type FeedbackSortField = "created_at" | "updated_at" | "status" | "reason";

export const FeedbackStatuses = {
  pending: "Pending Review",
  reviewed: "Reviewed",
  resolved: "Resolved",
  dismissed: "Dismissed",
} as const;

export type FeedbackStatus = keyof typeof FeedbackStatuses;

export interface FeedbackSearchParams {
  status?: FeedbackStatus;
  reason?: ReportReason;
  sort_by?: FeedbackSortField;
  sort_order?: SortOrder;
  page?: number;
  page_size?: number;
}

export async function listFeedback(
  params: FeedbackSearchParams
): Promise<PaginatedResponse<FeedbackListItem>> {
  const searchParams = new URLSearchParams();

  if (params.status) searchParams.set("status", params.status);
  if (params.reason) searchParams.set("reason", params.reason);
  if (params.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params.sort_order) searchParams.set("sort_order", params.sort_order);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));

  const response = await fetchWithRetry(
    `${API_BASE_URL}/staff/feedback/?${searchParams.toString()}`
  );

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in as staff");
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch feedback: ${response.statusText}`);
  }

  return response.json();
}

export interface FeedbackDetail extends FeedbackListItem {
  reviewer_notes: string;
}

export async function getFeedback(id: number): Promise<FeedbackDetail> {
  const response = await fetchWithRetry(`${API_BASE_URL}/staff/feedback/${id}/`);

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in as staff");
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch feedback: ${response.statusText}`);
  }

  return response.json();
}

export interface ResolveFeedbackResponse {
  id: number;
  status: string;
  message: string;
}

export async function resolveFeedback(
  id: number,
  status: FeedbackStatus,
  reviewerNotes: string
): Promise<ResolveFeedbackResponse> {
  const response = await fetchWithRetry(`${API_BASE_URL}/staff/feedback/${id}/resolve/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, reviewer_notes: reviewerNotes }),
  });

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in as staff");
  }

  if (!response.ok) {
    throw new Error(`Failed to resolve feedback: ${response.statusText}`);
  }

  return response.json();
}
