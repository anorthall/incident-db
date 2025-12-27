import { getCsrfToken } from "./csrf";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export interface StaffUser {
  id: number;
  email: string;
  name: string;
  is_staff: boolean;
  is_superuser: boolean;
  is_editor: boolean;
}

export function parseAuthHeaders(headers: Headers): StaffUser | null {
  const isAuthenticated = headers.get("CIDB-User-Authenticated") === "true";
  if (!isAuthenticated) return null;

  const id = headers.get("CIDB-User-ID");
  const email = headers.get("CIDB-User-Email");
  const name = headers.get("CIDB-User-Name");
  const isStaff = headers.get("CIDB-User-Is-Staff") === "true";
  const isSuperuser = headers.get("CIDB-User-Is-Superuser") === "true";
  const isEditor = headers.get("CIDB-User-Is-Editor") === "true";

  if (!id || !email) return null;

  return {
    id: parseInt(id, 10),
    email,
    name: name || "",
    is_staff: isStaff,
    is_superuser: isSuperuser,
    is_editor: isEditor,
  };
}

export interface LoginResponse {
  user: StaffUser;
  message: string;
}

async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const csrfToken = getCsrfToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (csrfToken && options.method && options.method !== "GET") {
    headers["X-CSRFToken"] = csrfToken;
  }

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
}

export async function staffLogin(email: string, password: string): Promise<LoginResponse> {
  const response = await authFetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Login failed");
  }

  return response.json();
}

export async function staffLogout(): Promise<void> {
  const response = await authFetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Logout failed");
  }
}

export async function getCurrentUser(): Promise<StaffUser> {
  const response = await authFetch(`${API_BASE_URL}/auth/me`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Not authenticated");
  }

  return response.json();
}
