import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type { VisibilityState } from "@tanstack/react-table";
import { ChevronUp, Table2 } from "lucide-react";
import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { IncidentCard } from "@/components/incidents/IncidentCard";
import { IncidentTable } from "@/components/incidents/IncidentTable";
import { NoResultsMessage } from "@/components/search/NoResultsMessage";
import { SortControls, type ViewMode } from "@/components/search/SortControls";
import { Button } from "@/components/ui/button";
import { searchIncidents, type SortField, type SortOrder, trackSearchClick } from "@/lib/api";
import {
  DELETING_SPEED_MS,
  MOBILE_BREAKPOINT,
  SCROLL_THRESHOLD,
  SEARCH_COUNT_STORAGE_KEY,
  TABLE_HINT_DELAY_MS,
  TABLE_HINT_DURATION_MS,
  TABLE_HINT_MIN_SEARCHES,
  TABLE_VIEW_HINT_STORAGE_KEY,
  TABLET_BREAKPOINT,
  TYPING_PAUSE_MS,
  TYPING_SPEED_MS,
  VIEW_MODE_STORAGE_KEY,
} from "@/constants.ts";
import { useStaffCommands } from "@/hooks/use-staff-commands";

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlQuery = searchParams.get("q") || "";
  const [query, setQuery] = useState(urlQuery);
  const { handleStaffCommand } = useStaffCommands();
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [searchTime, setSearchTime] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<SortField>("relevance");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    if (typeof window !== "undefined") {
      // Force cards view on mobile
      if (window.innerWidth < MOBILE_BREAKPOINT) return "cards";
      const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
      if (saved === "cards" || saved === "table") return saved;
    }
    return "cards";
  });

  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({
    tags: false,
    view_count: false,
  });
  const tableHintShownRef = useRef(false);

  // Force cards view on mobile resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < MOBILE_BREAKPOINT && viewMode === "table") {
        setViewMode("cards");
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [viewMode]);

  const handleViewModeChange = useCallback((mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, mode);
  }, []);

  const searchStartRef = useRef<number>(0);
  const navigate = useNavigate();
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const hasSearched = urlQuery.length > 0;

  // Track search start time and scroll to top on new search
  useEffect(() => {
    if (urlQuery) {
      searchStartRef.current = performance.now();
      setSearchTime(null);
      window.scrollTo(0, 0);
    }
  }, [urlQuery]);

  const { data, error, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ["incidents", urlQuery, sortBy, sortOrder],
    queryFn: ({ pageParam = 1 }) =>
      searchIncidents({
        q: urlQuery || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.total_pages ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
    enabled: hasSearched,
  });

  const { data: countData } = useQuery({
    queryKey: ["incidents-count"],
    queryFn: () => searchIncidents({ page: 1, page_size: 1 }),
    enabled: !hasSearched,
  });

  useEffect(() => {
    setQuery(urlQuery);
  }, [urlQuery]);

  useEffect(() => {
    if (data?.pages[0] && searchStartRef.current > 0 && searchTime === null) {
      setSearchTime(Math.round(performance.now() - searchStartRef.current));
    }
  }, [data, searchTime]);

  useEffect(() => {
    if (!loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Back to top visibility
  useEffect(() => {
    const handleScroll = () => {
      setShowBackToTop(window.scrollY > SCROLL_THRESHOLD);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Track search count for table hint
  useEffect(() => {
    if (!urlQuery) return;
    const currentCount = parseInt(localStorage.getItem(SEARCH_COUNT_STORAGE_KEY) || "0", 10);
    localStorage.setItem(SEARCH_COUNT_STORAGE_KEY, String(currentCount + 1));
  }, [urlQuery]);

  // Table view hint toast for desktop visitors on 3rd+ search
  useEffect(() => {
    if (tableHintShownRef.current) return;
    if (typeof window === "undefined") return;
    if (window.innerWidth < TABLET_BREAKPOINT) return; // Desktop only
    if (localStorage.getItem(TABLE_VIEW_HINT_STORAGE_KEY)) return; // Already shown
    if (viewMode !== "cards") return; // Only show when in list view
    const items = data?.pages.flatMap((page) => page.items) ?? [];
    if (!data || items.length === 0) return; // Need results

    const searchCount = parseInt(localStorage.getItem(SEARCH_COUNT_STORAGE_KEY) || "0", 10);
    if (searchCount < TABLE_HINT_MIN_SEARCHES) return; // Only show on 3rd+ search

    tableHintShownRef.current = true;
    localStorage.setItem(TABLE_VIEW_HINT_STORAGE_KEY, "true");

    const timer = setTimeout(() => {
      toast(
        <div className="flex items-start gap-3">
          <Table2 className="h-5 w-5 mt-0.5 text-primary" />
          <div>
            <p className="font-medium">Try Table View</p>
            <p className="text-sm text-muted-foreground mt-1">
              Switch to table view for easier scanning and sorting of incidents.
            </p>
          </div>
        </div>,
        {
          duration: TABLE_HINT_DURATION_MS,
          action: {
            label: "Try it",
            onClick: () => handleViewModeChange("table"),
          },
        }
      );
    }, TABLE_HINT_DELAY_MS);

    return () => clearTimeout(timer);
  }, [data, viewMode, handleViewModeChange]);

  const scrollToTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const handleSearch = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim()) {
        const handled = await handleStaffCommand(query);
        if (handled) {
          setQuery("");
          return;
        }
        setSearchParams({ q: query.trim() });
      }
    },
    [query, setSearchParams, handleStaffCommand]
  );

  const handleIncidentClick = useCallback(
    (incidentId: number, position: number) => {
      if (urlQuery) {
        void trackSearchClick(urlQuery, incidentId, position);
      }
      navigate(`/incidents/${incidentId}`);
    },
    [urlQuery, navigate]
  );

  const allItems = data?.pages.flatMap((page) => page.items) ?? [];
  const searchTotal = data?.pages[0]?.total ?? 0;
  const totalCount = countData?.total ?? 0;

  const exampleQueriesRef = useRef(
    [
      "rope failure",
      "flooding incidents",
      "hypothermia rescue",
      "vertical caving",
      "equipment failure",
      "lost cavers",
      "rock fall",
      "cave diving",
      "squeeze passage",
      "medical emergencies",
      "airplane crash",
      "collapsed passage",
      "anchor failure",
      "bad air",
      "sump rescue",
      "rappel accidents",
      "ladder climb",
      "solo caving",
    ].sort(() => Math.random() - 0.5)
  );

  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [animatedPlaceholder, setAnimatedPlaceholder] = useState("");
  const [isTyping, setIsTyping] = useState(true);
  const [isFocused, setIsFocused] = useState(false);
  const animationTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const clearAnimationTimeout = () => {
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current);
        animationTimeoutRef.current = null;
      }
    };

    if (query) {
      clearAnimationTimeout();
      return;
    }

    const exampleQueries = exampleQueriesRef.current;
    const currentQuery = exampleQueries[placeholderIndex];
    let charIndex = 0;

    if (isTyping) {
      const typeChar = () => {
        if (charIndex <= currentQuery.length) {
          setAnimatedPlaceholder(currentQuery.slice(0, charIndex));
          charIndex++;
          animationTimeoutRef.current = setTimeout(typeChar, TYPING_SPEED_MS);
        } else {
          animationTimeoutRef.current = setTimeout(() => setIsTyping(false), TYPING_PAUSE_MS);
        }
      };
      typeChar();
    } else {
      charIndex = currentQuery.length;
      const deleteChar = () => {
        if (charIndex >= 0) {
          setAnimatedPlaceholder(currentQuery.slice(0, charIndex));
          charIndex--;
          animationTimeoutRef.current = setTimeout(deleteChar, DELETING_SPEED_MS);
        } else {
          setPlaceholderIndex((i) => (i + 1) % exampleQueries.length);
          setIsTyping(true);
        }
      };
      deleteChar();
    }

    return clearAnimationTimeout;
  }, [placeholderIndex, isTyping, query]);

  if (!hasSearched) {
    return (
      <div className="flex flex-col items-center pt-[15vh]">
        <div className="text-center mb-12">
          <h1 className="text-6xl font-semibold tracking-tight">Caving Incident Database</h1>
          <p
            className={`mt-4 text-2xl font-light text-muted-foreground transition-opacity duration-700 ease-out ${totalCount > 0 ? "opacity-100" : "opacity-0"}`}
          >
            <span className="text-primary font-medium">
              {totalCount > 0 ? totalCount.toLocaleString() : "0"}
            </span>{" "}
            incidents documented
          </p>
        </div>

        <form onSubmit={handleSearch} className="w-full max-w-2xl px-4 py-12">
          <div
            className={`relative rounded-lg p-0.5 transition-colors ${isFocused ? "bg-linear-to-r from-red-500 via-yellow-500 to-purple-500 bg-size-[200%_100%] animate-gradient-x" : "bg-border"}`}
          >
            <input
              type="text"
              placeholder={animatedPlaceholder}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              autoFocus
              className={`w-full h-16 text-2xl px-8 rounded-md bg-background outline-none placeholder:text-muted-foreground/50 ${!query ? "caret-transparent" : ""}`}
            />
          </div>
        </form>
      </div>
    );
  }

  const maxWidthClass = viewMode === "table" ? "max-w-[1400px]" : "max-w-3xl";

  return (
    <div className={`${maxWidthClass} mx-auto w-full`}>
      {error && <p className="text-destructive">Error loading incidents. Please try again.</p>}

      {data && allItems.length > 0 && (
        <SortControls
          sortBy={sortBy}
          sortOrder={sortOrder}
          viewMode={viewMode}
          hasQuery={!!urlQuery}
          onSortByChange={setSortBy}
          onSortOrderChange={setSortOrder}
          onViewModeChange={handleViewModeChange}
          columnVisibility={columnVisibility}
          onColumnVisibilityChange={setColumnVisibility}
          resultCount={searchTotal}
          searchTime={searchTime}
        />
      )}

      {data && allItems.length === 0 && <NoResultsMessage />}

      {data && allItems.length > 0 && (
        <>
          {viewMode === "cards" ? (
            <div>
              {allItems.map((incident, index) => (
                <IncidentCard
                  key={incident.id}
                  incident={incident}
                  onClick={() => handleIncidentClick(incident.id, index + 1)}
                />
              ))}
            </div>
          ) : (
            <IncidentTable
              incidents={allItems}
              onRowClick={(id, index) => handleIncidentClick(id, index + 1)}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={(field) => {
                if (sortBy === field) {
                  setSortOrder(sortOrder === "asc" ? "desc" : "asc");
                } else {
                  setSortBy(field);
                  setSortOrder("desc");
                }
              }}
              columnVisibility={columnVisibility}
              onColumnVisibilityChange={setColumnVisibility}
            />
          )}

          <div ref={loadMoreRef} className="py-8 text-center">
            {isFetchingNextPage && <p className="text-muted-foreground">Loading more...</p>}
          </div>
        </>
      )}

      <Button
        onClick={scrollToTop}
        size="icon"
        className={`fixed bottom-4 right-4 rounded-full shadow-lg transition-opacity duration-300 cursor-pointer ${showBackToTop ? "opacity-100" : "opacity-0 pointer-events-none"}`}
      >
        <ChevronUp className="h-5 w-5" />
      </Button>
    </div>
  );
}
