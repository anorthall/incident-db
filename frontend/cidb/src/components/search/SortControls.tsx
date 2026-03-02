import type { VisibilityState } from "@tanstack/react-table";
import { ArrowDownAZ, ArrowUpAZ, List, Settings2, Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { SortField, SortOrder } from "@/lib/api";

export type ViewMode = "cards" | "table";

const COLUMN_LABELS: Record<string, string> = {
  title: "Title",
  date: "Date",
  cave_name: "Cave",
  location_summary: "Location",
  view_count: "Views",
  tags: "Tags",
};

const ALL_COLUMNS = ["title", "date", "cave_name", "location_summary", "view_count", "tags"];

interface SortControlsProps {
  sortBy: SortField;
  sortOrder: SortOrder;
  viewMode: ViewMode;
  hasQuery: boolean;
  onSortByChange: (field: SortField) => void;
  onSortOrderChange: (order: SortOrder) => void;
  onViewModeChange: (mode: ViewMode) => void;
  columnVisibility?: VisibilityState;
  onColumnVisibilityChange?: (visibility: VisibilityState) => void;
  resultCount?: number;
  searchTime?: number | null;
}

export function SortControls({
  sortBy,
  sortOrder,
  viewMode,
  hasQuery,
  onSortByChange,
  onSortOrderChange,
  onViewModeChange,
  columnVisibility = {},
  onColumnVisibilityChange,
  resultCount,
  searchTime,
}: SortControlsProps) {
  const isColumnVisible = (columnId: string) => columnVisibility[columnId] !== false;

  const toggleColumn = (columnId: string) => {
    onColumnVisibilityChange?.({
      ...columnVisibility,
      [columnId]: !isColumnVisible(columnId),
    });
  };

  return (
    <div className="flex items-center justify-between gap-4 mb-4">
      {viewMode === "cards" ? (
        <>
          <div className="flex items-center gap-2">
            <ToggleGroup
              type="single"
              value={sortBy}
              onValueChange={(v) => v && onSortByChange(v as SortField)}
              variant="outline"
            >
              <ToggleGroupItem value="date" aria-label="Sort by date">
                Date
              </ToggleGroupItem>
              {hasQuery && (
                <ToggleGroupItem value="relevance" aria-label="Sort by relevance">
                  Relevance
                </ToggleGroupItem>
              )}
            </ToggleGroup>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => onSortOrderChange(sortOrder === "asc" ? "desc" : "asc")}
              title={sortOrder === "asc" ? "Ascending" : "Descending"}
            >
              {sortOrder === "asc" ? (
                <ArrowUpAZ className="h-4 w-4" />
              ) : (
                <ArrowDownAZ className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Hide table view toggle on mobile */}
          <div className="hidden sm:flex items-center gap-1">
            <Button
              variant="secondary"
              size="icon"
              onClick={() => onViewModeChange("cards")}
              title="List view"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onViewModeChange("table")}
              title="Table view"
            >
              <Table2 className="h-4 w-4" />
            </Button>
          </div>
        </>
      ) : (
        <>
          <div className="text-sm text-muted-foreground">
            {resultCount !== undefined && (
              <>
                <span className="font-medium text-foreground">{resultCount.toLocaleString()}</span>{" "}
                result{resultCount !== 1 ? "s" : ""}
                {searchTime !== null && searchTime !== undefined && (
                  <span className="ml-1">({searchTime}ms)</span>
                )}
              </>
            )}
          </div>
          <div className="flex items-center gap-2">
            <ToggleGroup type="single" value={viewMode} variant="outline">
              <ToggleGroupItem
                value="cards"
                aria-label="List view"
                onClick={() => onViewModeChange("cards")}
                className="gap-2"
              >
                <List className="h-4 w-4" />
                List
              </ToggleGroupItem>
              <ToggleGroupItem
                value="table"
                aria-label="Table view"
                onClick={() => onViewModeChange("table")}
                className="gap-2"
              >
                <Table2 className="h-4 w-4" />
                Table
              </ToggleGroupItem>
            </ToggleGroup>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="h-9">
                  <Settings2 className="mr-2 h-4 w-4" />
                  Columns
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-[160px]">
                <DropdownMenuLabel>Toggle columns</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {ALL_COLUMNS.map((columnId) => (
                  <DropdownMenuCheckboxItem
                    key={columnId}
                    checked={isColumnVisible(columnId)}
                    onCheckedChange={() => toggleColumn(columnId)}
                  >
                    {COLUMN_LABELS[columnId]}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </>
      )}
    </div>
  );
}
