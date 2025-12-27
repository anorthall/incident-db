import { memo, useMemo } from "react";
import type { ColumnDef, VisibilityState } from "@tanstack/react-table";
import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown, Check } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { IncidentListItem, SortField, SortOrder } from "@/lib/api";
import { isIncidentViewed } from "@/lib/viewed-incidents";

type TableSortField = SortField;

interface IncidentTableProps {
  incidents: IncidentListItem[];
  onRowClick: (id: number, index: number) => void;
  sortBy: SortField;
  sortOrder: SortOrder;
  onSortChange: (field: TableSortField) => void;
  columnVisibility: VisibilityState;
  onColumnVisibilityChange: (visibility: VisibilityState) => void;
}

export const IncidentTable = memo(function IncidentTable({
  incidents,
  onRowClick,
  sortBy,
  sortOrder,
  onSortChange,
  columnVisibility,
  onColumnVisibilityChange,
}: IncidentTableProps) {
  const SortIcon = ({ field }: { field: TableSortField }) => {
    if (sortBy !== field) {
      return <ArrowUpDown className="ml-2 h-4 w-4" />;
    }
    return sortOrder === "asc" ? (
      <ArrowUp className="ml-2 h-4 w-4" />
    ) : (
      <ArrowDown className="ml-2 h-4 w-4" />
    );
  };

  const columns: ColumnDef<IncidentListItem>[] = useMemo(
    () => [
      {
        accessorKey: "date",
        size: 120,
        minSize: 100,
        header: () => (
          <Button variant="ghost" className="h-8 px-2 -ml-2" onClick={() => onSortChange("date")}>
            Date
            <SortIcon field="date" />
          </Button>
        ),
        cell: ({ row }) => {
          const date = row.original.date;
          if (!date) return "Unknown";
          const shortMonths = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
          ];
          if (date.precision === "year") return String(date.year);
          if (date.precision === "month" && date.month)
            return `${shortMonths[date.month - 1]} ${date.year}`;
          if (date.precision === "day" && date.month && date.day)
            return `${shortMonths[date.month - 1]} ${date.day}, ${date.year}`;
          return date.display;
        },
      },
      {
        accessorKey: "title",
        size: 350,
        minSize: 150,
        header: () => (
          <Button variant="ghost" className="h-8 px-2 -ml-2" onClick={() => onSortChange("title")}>
            Title
            <SortIcon field="title" />
          </Button>
        ),
        cell: ({ row }) => {
          const viewed = isIncidentViewed(row.original.id);
          return (
            <span
              className={`font-medium flex items-center gap-2 ${viewed ? "text-muted-foreground" : ""}`}
            >
              {row.getValue("title")}
              {viewed && <Check className="h-4 w-4 text-muted-foreground/70" />}
            </span>
          );
        },
      },
      {
        accessorKey: "cave_name",
        size: 150,
        minSize: 80,
        header: () => (
          <Button
            variant="ghost"
            className="h-8 px-2 -ml-2"
            onClick={() => onSortChange("cave_name")}
          >
            Cave
            <SortIcon field="cave_name" />
          </Button>
        ),
        cell: ({ row }) => row.getValue("cave_name") || "-",
      },
      {
        accessorKey: "location_summary",
        header: "Location",
        size: 180,
        minSize: 120,
        cell: ({ row }) => row.getValue("location_summary") || "-",
      },
      {
        accessorKey: "view_count",
        size: 100,
        minSize: 80,
        header: () => (
          <div className="text-center">
            <Button variant="ghost" className="h-8 px-2" onClick={() => onSortChange("popularity")}>
              Views
              <SortIcon field="popularity" />
            </Button>
          </div>
        ),
        cell: ({ row }) => (
          <div className="text-center text-muted-foreground">
            {(row.getValue("view_count") as number).toLocaleString()}
          </div>
        ),
      },
      {
        accessorKey: "tags",
        header: "Tags",
        size: 200,
        minSize: 150,
        cell: ({ row }) => {
          const tags = row.original.tags;
          return (
            <div className="flex flex-wrap gap-1 ">
              {tags.slice(0, 3).map((tag) => (
                <Badge key={tag.id} variant="outline" className="text-xs">
                  {tag.name}
                </Badge>
              ))}
              {tags.length > 3 && (
                <span className="text-xs text-muted-foreground">+{tags.length - 3}</span>
              )}
            </div>
          );
        },
      },
    ],
    [SortIcon, onSortChange]
  );

  const table = useReactTable({
    data: incidents,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onColumnVisibilityChange: (updater) => {
      const newState = typeof updater === "function" ? updater(columnVisibility) : updater;
      onColumnVisibilityChange(newState);
    },
    state: {
      columnVisibility,
    },
  });

  return (
    <div>
      <div className="rounded-md border max-w-svw">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row, index) => (
                <TableRow
                  key={row.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onRowClick(row.original.id, index)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  No incidents found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
});
