import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { getCurrentUser, staffLogin, staffLogout, type StaffUser } from "./auth-api";
import { registerAuthCallback, unregisterAuthCallback } from "./auth-sync";

const AUTH_STORAGE_KEY = "cidb_staff_user";

interface AuthContextValue {
  user: StaffUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function getStoredUser(): StaffUser | null {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function setStoredUser(user: StaffUser | null) {
  if (user) {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<StaffUser | null>(getStoredUser);
  const [isLoading, setIsLoading] = useState(() => getStoredUser() === null);
  const initialCheckDone = useRef(false);

  const updateUser = useCallback((newUser: StaffUser | null) => {
    setUser(newUser);
    setStoredUser(newUser);
  }, []);

  useEffect(() => {
    registerAuthCallback(updateUser);
    return () => unregisterAuthCallback();
  }, [updateUser]);

  const checkAuth = useCallback(async () => {
    if (initialCheckDone.current) return;
    initialCheckDone.current = true;

    try {
      const currentUser = await getCurrentUser();
      updateUser(currentUser);
    } catch {
      updateUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [updateUser]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await staffLogin(email, password);
      updateUser(response.user);
    },
    [updateUser]
  );

  const logout = useCallback(async () => {
    await staffLogout();
    updateUser(null);
  }, [updateUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
