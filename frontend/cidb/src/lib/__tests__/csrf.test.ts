import { describe, it, expect, vi, beforeEach } from "vitest";

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

beforeEach(() => {
  vi.resetModules();
  fetchMock.mockReset();
});

describe("csrf", () => {
  it("fetchCsrfToken stores token on success", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ csrf_token: "test-csrf-token" }),
    });

    const { fetchCsrfToken, getCsrfToken } = await import("../csrf");
    await fetchCsrfToken();

    expect(getCsrfToken()).toBe("test-csrf-token");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/auth/csrf"),
      expect.objectContaining({ credentials: "include" })
    );
  });

  it("getCsrfToken returns null before fetch", async () => {
    const { getCsrfToken } = await import("../csrf");
    expect(getCsrfToken()).toBeNull();
  });

  it("fetchCsrfToken handles failure gracefully", async () => {
    fetchMock.mockResolvedValueOnce({ ok: false });

    const { fetchCsrfToken, getCsrfToken } = await import("../csrf");
    await fetchCsrfToken();

    expect(getCsrfToken()).toBeNull();
  });
});
