import { describe, it, expect, vi, beforeEach } from "vitest";

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

vi.mock("../sentry", () => ({
  captureApiError: vi.fn(),
}));

vi.mock("../auth-sync", () => ({
  notifyAuthUpdate: vi.fn(),
}));

beforeEach(() => {
  vi.resetModules();
  fetchMock.mockReset();
});

function okResponse(data: unknown, headers: Record<string, string> = {}): Partial<Response> {
  const h = new Headers(headers);
  return {
    ok: true,
    status: 200,
    headers: h,
    json: () => Promise.resolve(data),
  };
}

function errorResponse(status: number, headers: Record<string, string> = {}): Partial<Response> {
  const h = new Headers(headers);
  return {
    ok: false,
    status,
    statusText: `Error ${status}`,
    headers: h,
    json: () => Promise.resolve({ detail: "error" }),
  };
}

describe("searchIncidents", () => {
  it("builds correct URL with params", async () => {
    fetchMock.mockResolvedValueOnce(
      okResponse({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 })
    );

    const { searchIncidents } = await import("../api");
    await searchIncidents({ q: "cave rescue", page: 2, page_size: 10, sort_by: "date" });

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain("q=cave+rescue");
    expect(calledUrl).toContain("page=2");
    expect(calledUrl).toContain("page_size=10");
    expect(calledUrl).toContain("sort_by=date");
  });

  it("omits empty params", async () => {
    fetchMock.mockResolvedValueOnce(
      okResponse({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 })
    );

    const { searchIncidents } = await import("../api");
    await searchIncidents({});

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).not.toContain("q=");
    expect(calledUrl).not.toContain("sort_by=");
  });
});

describe("getIncident", () => {
  it("fetches by ID", async () => {
    fetchMock.mockResolvedValueOnce(okResponse({ id: 42, title: "Test" }));

    const { getIncident } = await import("../api");
    const result = await getIncident(42);

    expect(result.id).toBe(42);
    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/incidents/42");
  });
});

describe("createReport", () => {
  it("sends JSON body with POST", async () => {
    fetchMock.mockResolvedValueOnce(okResponse({ id: 1, status: "pending", message: "Created" }));

    const { createReport } = await import("../api");
    await createReport({
      incident_id: 5,
      reason: "inaccurate",
      description: "Wrong date",
    });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body as string)).toEqual({
      incident_id: 5,
      reason: "inaccurate",
      description: "Wrong date",
    });
  });
});

describe("fetchWithRetry", () => {
  it("retries on 500 errors", async () => {
    fetchMock
      .mockResolvedValueOnce(errorResponse(500))
      .mockResolvedValueOnce(
        okResponse({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 })
      );

    const { searchIncidents } = await import("../api");
    const result = await searchIncidents({});

    expect(result.total).toBe(0);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  }, 15000);

  it("does not retry on 4xx errors", async () => {
    fetchMock.mockResolvedValueOnce(errorResponse(422));

    const { searchIncidents } = await import("../api");
    await expect(searchIncidents({})).rejects.toThrow();

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("getSearchSuggestions", () => {
  it("returns empty for short queries", async () => {
    const { getSearchSuggestions } = await import("../api");
    const result = await getSearchSuggestions("a");

    expect(result.suggestions).toEqual([]);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("CSRF token injection", () => {
  it("includes X-CSRFToken on POST requests when token exists", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ csrf_token: "my-csrf" }),
    });

    const csrf = await import("../csrf");
    await csrf.fetchCsrfToken();

    vi.resetModules();
    fetchMock.mockReset();

    vi.doMock("../csrf", () => ({
      getCsrfToken: () => "my-csrf",
    }));
    vi.doMock("../sentry", () => ({
      captureApiError: vi.fn(),
    }));
    vi.doMock("../auth-sync", () => ({
      notifyAuthUpdate: vi.fn(),
    }));

    fetchMock.mockResolvedValueOnce(okResponse({ id: 1, status: "pending", message: "Created" }));

    const { createReport } = await import("../api");
    await createReport({ incident_id: 1, reason: "typo" });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers["X-CSRFToken"]).toBe("my-csrf");
  });
});
