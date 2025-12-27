import { Monitor, Moon, Sun } from "lucide-react";
import * as React from "react";
import { useCallback, useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { useStaffCommands } from "@/hooks/use-staff-commands";

import { AppSidebar } from "@/components/layout/AppSidebar.tsx";
import { FeedbackModal } from "@/components/forms/FeedbackModal";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { getCookie } from "@/lib/cookies";
import { useTheme } from "@/lib/theme";
import { MOBILE_BREAKPOINT, SIDEBAR_COOKIE_KEY } from "@/constants.ts";

function getSidebarStateFromCookie(): boolean {
  if (typeof document === "undefined") return true;
  return getCookie(SIDEBAR_COOKIE_KEY) === "true";
}

export function RootLayout() {
  const sidebarOpen = getSidebarStateFromCookie();
  const navigate = useNavigate();
  const { handleStaffCommand } = useStaffCommands();
  const [query, setQuery] = useState("");
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== "undefined" && window.innerWidth < MOBILE_BREAKPOINT
  );
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const ThemeIcon = theme === "dark" ? Moon : theme === "light" ? Sun : Monitor;

  const handleSearch = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim()) {
        const handled = await handleStaffCommand(query);
        if (handled) {
          setQuery("");
          return;
        }
        navigate(`/?q=${encodeURIComponent(query.trim())}`);
        setQuery("");
      }
    },
    [query, navigate, handleStaffCommand]
  );

  return (
    <SidebarProvider defaultOpen={sidebarOpen}>
      <AppSidebar />
      <SidebarInset>
        <div className="min-h-screen flex flex-col">
          <header className="border-b sm:sticky sm:top-0 bg-background z-10 px-4">
            <div className="h-16 flex justify-between items-center">
              <SidebarTrigger className="cursor-pointer" />

              <form
                onSubmit={handleSearch}
                className="max-w-3xl w-full px-4 transition-all duration-300 ease-in-out"
              >
                <Input
                  type="text"
                  placeholder={isMobile ? "Search" : "Search incidents..."}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => setIsSearchFocused(true)}
                  onBlur={() => setIsSearchFocused(false)}
                  className="h-10 text-base w-full"
                />
              </form>

              <div
                className={`flex items-center shrink-0 justify-self-end transition-all duration-200 ease-out ${isSearchFocused ? "max-w-0 opacity-0 scale-90 sm:max-w-none sm:opacity-100 sm:scale-100" : "opacity-100 scale-100"}`}
                style={{ overflow: "hidden" }}
              >
                <DropdownMenu>
                  <DropdownMenuTrigger className="cursor-pointer outline-none p-2 hover:bg-accent hover:text-accent-foreground rounded-md">
                    <ThemeIcon className="h-5 w-5" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="shadow-none p-0 min-w-0">
                    <DropdownMenuItem
                      onClick={() => setTheme("light")}
                      className={`cursor-pointer rounded-none ${theme === "light" ? "bg-accent" : ""}`}
                    >
                      <Sun className="h-4 w-4 mr-2" />
                      Light
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setTheme("dark")}
                      className={`cursor-pointer rounded-none ${theme === "dark" ? "bg-accent" : ""}`}
                    >
                      <Moon className="h-4 w-4 mr-2" />
                      Dark
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setTheme("system")}
                      className={`cursor-pointer rounded-none ${theme === "system" ? "bg-accent" : ""}`}
                    >
                      <Monitor className="h-4 w-4 mr-2" />
                      System
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </header>

          <main className="mx-auto px-4 py-6 grow w-full max-w-3xl">
            <Outlet />
          </main>
        </div>
      </SidebarInset>
      <FeedbackModal />
    </SidebarProvider>
  );
}
