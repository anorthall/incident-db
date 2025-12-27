import type { StaffUser } from "./auth-api";

type AuthUpdateCallback = (user: StaffUser | null) => void;

let authUpdateCallback: AuthUpdateCallback | null = null;

export function registerAuthCallback(callback: AuthUpdateCallback) {
  authUpdateCallback = callback;
}

export function unregisterAuthCallback() {
  authUpdateCallback = null;
}

export function notifyAuthUpdate(user: StaffUser | null) {
  authUpdateCallback?.(user);
}
