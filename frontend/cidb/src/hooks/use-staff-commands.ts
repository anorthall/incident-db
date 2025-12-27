import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";

export function useStaffCommands() {
  const navigate = useNavigate();
  const { logout, isAuthenticated } = useAuth();

  const handleStaffCommand = useCallback(
    async (query: string): Promise<boolean> => {
      const trimmedQuery = query.trim().toLowerCase();

      if (trimmedQuery === "staff:login") {
        navigate("/staff/login");
        return true;
      }

      if (trimmedQuery === "staff:logout") {
        if (isAuthenticated) {
          await logout();
          toast("Signed out successfully");
        } else {
          toast("You are not signed in");
        }
        return true;
      }

      return false;
    },
    [navigate, logout, isAuthenticated]
  );

  return { handleStaffCommand };
}
