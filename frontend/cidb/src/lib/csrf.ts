const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

let csrfToken: string | null = null;

export function getCsrfToken(): string | null {
  return csrfToken;
}

export async function fetchCsrfToken(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
    credentials: "include",
  });
  if (response.ok) {
    const data = await response.json();
    csrfToken = data.csrf_token;
  }
}
