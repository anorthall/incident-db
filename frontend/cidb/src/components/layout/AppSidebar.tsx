import { motion } from "framer-motion";
import {
  ClipboardList,
  Dices,
  ExternalLink,
  LogOut,
  MessageSquare,
  Settings,
  User,
  X,
} from "lucide-react";
import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar.tsx";
import { getRandomIncidentId } from "@/lib/api.ts";
import { useAuth } from "@/lib/auth-context.tsx";
import useFeedback from "@/lib/feedback-context.tsx";
import { useTheme } from "@/lib/theme.tsx";
import {
  clearViewedIncidents,
  getViewedIncidents,
  onViewedIncidentsChange,
  type ViewedIncident,
} from "@/lib/viewed-incidents.ts";
import {
  CIDBIconForDarkMode,
  CIDBIconForLightMode,
  cidbItems,
  CIDBLogoForDarkMode,
  CIDBLogoForLightMode,
  HISTORY_ENABLED_STORAGE_KEY,
  navItems,
} from "@/constants.ts";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();
  const navigate = useNavigate();
  const { isDarkMode } = useTheme();
  const { state } = useSidebar();
  const { openFeedback } = useFeedback();
  const { user, isAuthenticated, logout } = useAuth();
  const isCollapsed = state === "collapsed";
  const Logo = isCollapsed
    ? isDarkMode
      ? CIDBIconForDarkMode
      : CIDBIconForLightMode
    : isDarkMode
      ? CIDBLogoForDarkMode
      : CIDBLogoForLightMode;

  const incidentMatch = location.pathname.match(/^\/incidents\/(\d+)/);
  const currentIncidentId = incidentMatch ? parseInt(incidentMatch[1], 10) : null;

  const [historyEnabled] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(HISTORY_ENABLED_STORAGE_KEY);
      return saved !== "false";
    }
    return true;
  });

  const [viewedIncidents, setViewedIncidents] = useState<ViewedIncident[]>(() =>
    getViewedIncidents()
  );

  const seenIncidentIds = useRef<Set<number>>(new Set(getViewedIncidents().map((i) => i.id)));

  const [isLoadingRandom, setIsLoadingRandom] = useState(false);

  useEffect(() => {
    return onViewedIncidentsChange(() => {
      setViewedIncidents(getViewedIncidents());
    });
  }, []);

  const handleClearViewed = useCallback(() => {
    clearViewedIncidents();
    setViewedIncidents([]);
  }, []);

  const handleRandomIncident = useCallback(async () => {
    setIsLoadingRandom(true);
    try {
      const id = await getRandomIncidentId();
      if (id) {
        navigate(`/incidents/${id}`);
      }
    } finally {
      setIsLoadingRandom(false);
    }
  }, [navigate]);

  const handleFeedbackClick = useCallback(() => {
    if (currentIncidentId) {
      const incident = viewedIncidents.find((i) => i.id === currentIncidentId);
      if (incident) {
        openFeedback({ id: incident.id, title: incident.title });
      } else {
        openFeedback();
      }
    } else {
      openFeedback();
    }
  }, [currentIncidentId, viewedIncidents, openFeedback]);

  const handleLogout = useCallback(async () => {
    await logout();
    navigate("/");
  }, [logout, navigate]);

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader className="transition-all duration-200 h-16 box-content border-b flex justify-center items-center">
        <Link to="/" className={`flex items-center justify-center`}>
          <img
            src={Logo}
            alt="CIDB"
            className={`object-contain ${isCollapsed ? "max-h-8" : "max-h-10"} transition-all duration-200`}
          />
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === item.url}
                    tooltip={item.title}
                  >
                    <Link to={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={handleRandomIncident}
                  disabled={isLoadingRandom}
                  tooltip="Random Incident"
                  className="cursor-pointer"
                >
                  <Dices className={`h-4 w-4 ${isLoadingRandom ? "animate-spin" : ""}`} />
                  <span>Random Incident</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>CIDB</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={handleFeedbackClick}
                  tooltip="Feedback"
                  className="cursor-pointer"
                >
                  <MessageSquare className="h-4 w-4" />
                  <span>Feedback</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              {cidbItems
                .filter((item) => item.title !== "Feedback")
                .map((item) => {
                  const isExternal = item.url.startsWith("http") || item.url.startsWith("mailto:");
                  const iconElement =
                    "imageLight" in item ? (
                      <img
                        src={isDarkMode ? item.imageDark : item.imageLight}
                        alt=""
                        className="h-4.5 w-4.5 shrink-0 object-contain"
                      />
                    ) : (
                      <item.icon className="h-4 w-4" />
                    );
                  return (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton
                        asChild
                        isActive={!isExternal && location.pathname === item.url}
                        tooltip={item.title}
                      >
                        {isExternal ? (
                          <a href={item.url} target="_blank" rel="noopener noreferrer">
                            {iconElement}
                            <span>{item.title}</span>
                          </a>
                        ) : (
                          <Link to={item.url}>
                            {iconElement}
                            <span>{item.title}</span>
                          </Link>
                        )}
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>NSS</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild tooltip="caves.org">
                  <a href="https://caves.org/" target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4" />
                    <span>caves.org</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {isAuthenticated && user && (
          <SidebarGroup>
            <SidebarGroupLabel>Staff</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <div className="flex items-center gap-2 px-2 py-1.5 text-sm text-sidebar-foreground">
                    <User className="h-4 w-4 shrink-0" />
                    <span className="truncate">{user.name || user.email}</span>
                  </div>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === "/staff/feedback"}
                    tooltip="Feedback"
                  >
                    <Link to="/staff/feedback">
                      <ClipboardList className="h-4 w-4" />
                      <span>Feedback</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                {user.is_superuser && (
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild tooltip="Django Admin">
                      <a href="/admin/" target="_blank" rel="noopener noreferrer">
                        <Settings className="h-4 w-4" />
                        <span>Django Admin</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )}
                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={handleLogout}
                    tooltip="Log out"
                    className="cursor-pointer"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Log out</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter
        className={historyEnabled && viewedIncidents.length > 0 && !isCollapsed ? "border-t" : ""}
      >
        {historyEnabled && viewedIncidents.length > 0 && !isCollapsed && (
          <SidebarGroup>
            <SidebarGroupLabel>Recently Viewed</SidebarGroupLabel>
            <SidebarGroupAction
              onClick={handleClearViewed}
              title="Clear recently viewed"
              className="cursor-pointer text-muted-foreground"
            >
              <X />
            </SidebarGroupAction>

            <SidebarGroupContent className="pt-1">
              <SidebarMenu>
                {viewedIncidents.slice(0, 5).map((incident) => {
                  const isNew = !seenIncidentIds.current.has(incident.id);
                  if (isNew) {
                    seenIncidentIds.current.add(incident.id);
                  }
                  return (
                    <motion.div
                      key={incident.id}
                      initial={isNew ? { opacity: 0 } : false}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.25, ease: "easeOut" }}
                    >
                      <SidebarMenuItem>
                        <SidebarMenuButton asChild>
                          <Link to={`/incidents/${incident.id}`}>
                            <span className="truncate">{incident.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    </motion.div>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
