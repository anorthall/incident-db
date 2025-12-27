import { describe, it, expect, vi, beforeEach } from "vitest";
import { parseAuthHeaders } from "../auth-api";

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

beforeEach(() => {
  vi.resetModules();
  fetchMock.mockReset();
});

function makeHeaders(entries: Record<string, string>): Headers {
  const headers = new Headers();
  for (const [key, value] of Object.entries(entries)) {
    headers.set(key, value);
  }
  return headers;
}

describe("parseAuthHeaders", () => {
  it("parses authenticated user headers", () => {
    const headers = makeHeaders({
      "CIDB-User-Authenticated": "true",
      "CIDB-User-ID": "42",
      "CIDB-User-Email": "admin@example.com",
      "CIDB-User-Name": "Admin User",
      "CIDB-User-Is-Staff": "true",
      "CIDB-User-Is-Superuser": "false",
      "CIDB-User-Is-Editor": "true",
    });

    const user = parseAuthHeaders(headers);
    expect(user).toEqual({
      id: 42,
      email: "admin@example.com",
      name: "Admin User",
      is_staff: true,
      is_superuser: false,
      is_editor: true,
    });
  });

  it("returns null when not authenticated", () => {
    const headers = makeHeaders({ "CIDB-User-Authenticated": "false" });
    expect(parseAuthHeaders(headers)).toBeNull();
  });

  it("returns null when authenticated header is missing", () => {
    const headers = makeHeaders({});
    expect(parseAuthHeaders(headers)).toBeNull();
  });

  it("returns null when required ID header is missing", () => {
    const headers = makeHeaders({
      "CIDB-User-Authenticated": "true",
      "CIDB-User-Email": "admin@example.com",
    });
    expect(parseAuthHeaders(headers)).toBeNull();
  });

  it("returns null when required email header is missing", () => {
    const headers = makeHeaders({
      "CIDB-User-Authenticated": "true",
      "CIDB-User-ID": "42",
    });
    expect(parseAuthHeaders(headers)).toBeNull();
  });

  it("defaults name to empty string when missing", () => {
    const headers = makeHeaders({
      "CIDB-User-Authenticated": "true",
      "CIDB-User-ID": "1",
      "CIDB-User-Email": "user@example.com",
    });

    const user = parseAuthHeaders(headers);
    expect(user).not.toBeNull();
    expect(user!.name).toBe("");
  });
});

describe("staffLogin", () => {
  it("sends credentials and returns response", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          user: { id: 1, email: "staff@example.com", name: "Staff", is_staff: true },
          message: "Login successful",
        }),
    });

    const { staffLogin } = await import("../auth-api");
    const result = await staffLogin("staff@example.com", "password123");

    expect(result.user.email).toBe("staff@example.com");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/auth/login"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "staff@example.com", password: "password123" }),
      })
    );
  });

  it("throws with error detail on failure", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: "Invalid credentials" }),
    });

    const { staffLogin } = await import("../auth-api");
    await expect(staffLogin("bad@example.com", "wrong")).rejects.toThrow("Invalid credentials");
  });
});

describe("staffLogout", () => {
  it("posts to logout endpoint", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true });

    const { staffLogout } = await import("../auth-api");
    await staffLogout();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/auth/logout"),
      expect.objectContaining({ method: "POST" })
    );
  });
});
