import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  FeedbackStatuses,
  listFeedback,
  ReportReasons,
  type FeedbackListItem,
  type FeedbackSearchParams,
  type FeedbackSortField,
  type FeedbackStatus,
  type ReportReason,
  type SortOrder,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  pending: "default",
  reviewed: "secondary",
  resolved: "outline",
  dismissed: "destructive",
};

export function FeedbackListPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<FeedbackSortField>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [statusFilter, setStatusFilter] = useState<FeedbackStatus | "all">("all");
  const [reasonFilter, setReasonFilter] = useState<ReportReason | "all">("all");
  const pageSize = 20;

  const params: FeedbackSearchParams = useMemo(
    () => ({
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(statusFilter !== "all" && { status: statusFilter }),
      ...(reasonFilter !== "all" && { reason: reasonFilter }),
    }),
    [page, sortBy, sortOrder, statusFilter, reasonFilter]
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["feedback", params],
    queryFn: () => listFeedback(params),
    enabled: isAuthenticated && (user?.is_staff || user?.is_editor),
  });

  const handleSortChange = useCallback(
    (field: FeedbackSortField) => {
      if (sortBy === field) {
        setSortOrder(sortOrder === "asc" ? "desc" : "asc");
      } else {
        setSortBy(field);
        setSortOrder("desc");
      }
      setPage(1);
    },
    [sortBy, sortOrder]
  );

  const SortIcon = useCallback(
    ({ field }: { field: FeedbackSortField }) => {
      if (sortBy !== field) {
        return <ArrowUpDown className="ml-2 h-4 w-4" />;
      }
      return sortOrder === "asc" ? (
        <ArrowUp className="ml-2 h-4 w-4" />
      ) : (
        <ArrowDown className="ml-2 h-4 w-4" />
      );
    },
    [sortBy, sortOrder]
  );

  const columns: ColumnDef<FeedbackListItem>[] = useMemo(
    () => [
      {
        accessorKey: "id",
        size: 60,
        header: "ID",
        cell: ({ row }) => <span className="text-muted-foreground">#{row.original.id}</span>,
      },
      {
        accessorKey: "created_at",
        size: 140,
        header: () => (
          <Button
            variant="ghost"
            className="h-8 px-2 -ml-2 cursor-pointer"
            onClick={() => handleSortChange("created_at")}
          >
            Date
            <SortIcon field="created_at" />
          </Button>
        ),
        cell: ({ row }) => {
          const date = new Date(row.original.created_at);
          return (
            <span className="text-sm">
              {date.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          );
        },
      },
      {
        accessorKey: "reason",
        size: 160,
        header: () => (
          <Button
            variant="ghost"
            className="h-8 px-2 -ml-2 cursor-pointer"
            onClick={() => handleSortChange("reason")}
          >
            Reason
            <SortIcon field="reason" />
          </Button>
        ),
        cell: ({ row }) => row.original.reason_display,
      },
      {
        accessorKey: "incident",
        size: 250,
        header: "Incident",
        cell: ({ row }) => {
          const incident = row.original.incident;
          if (!incident) {
            return <span className="text-muted-foreground">General Feedback</span>;
          }
          return (
            <Link
              to={`/incidents/${incident.id}`}
              className="text-primary hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {incident.title}
            </Link>
          );
        },
      },
      {
        accessorKey: "description",
        size: 300,
        header: "Description",
        cell: ({ row }) => <span className="line-clamp-2 text-sm">{row.original.description}</span>,
      },
      {
        accessorKey: "reporter",
        size: 180,
        header: "Reporter",
        cell: ({ row }) => {
          const reporter = row.original.reporter;
          if (!reporter?.email) {
            return <span className="text-muted-foreground">Anonymous</span>;
          }
          return <span className="text-sm">{reporter.email}</span>;
        },
      },
      {
        accessorKey: "status",
        size: 120,
        header: () => (
          <Button
            variant="ghost"
            className="h-8 px-2 -ml-2 cursor-pointer"
            onClick={() => handleSortChange("status")}
          >
            Status
            <SortIcon field="status" />
          </Button>
        ),
        cell: ({ row }) => {
          const status = row.original.status;
          return (
            <Badge variant={STATUS_VARIANT[status] || "outline"}>
              {row.original.status_display}
            </Badge>
          );
        },
      },
    ],
    [handleSortChange, SortIcon]
  );

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated || (!user?.is_staff && !user?.is_editor)) {
    return <Navigate to="/staff/login" replace />;
  }

  return (
    <div className="space-y-4 max-w-[1400px] mx-auto w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Feedback</h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Status:</span>
          <Select
            value={statusFilter}
            onValueChange={(v) => {
              setStatusFilter(v as FeedbackStatus | "all");
              setPage(1);
            }}
          >
            <SelectTrigger className="w-[150px] cursor-pointer">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all" className="cursor-pointer">
                All
              </SelectItem>
              {Object.entries(FeedbackStatuses).map(([key, label]) => (
                <SelectItem key={key} value={key} className="cursor-pointer">
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Reason:</span>
          <Select
            value={reasonFilter}
            onValueChange={(v) => {
              setReasonFilter(v as ReportReason | "all");
              setPage(1);
            }}
          >
            <SelectTrigger className="w-[180px] cursor-pointer">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all" className="cursor-pointer">
                All
              </SelectItem>
              {Object.entries(ReportReasons).map(([key, label]) => (
                <SelectItem key={key} value={key} className="cursor-pointer">
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {data && (
          <span className="text-sm text-muted-foreground ml-auto">
            {data.total} {data.total === 1 ? "item" : "items"}
          </span>
        )}
      </div>

      {error && (
        <p className="text-destructive">
          Error loading feedback. {error instanceof Error ? error.message : "Please try again."}
        </p>
      )}

      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Loading feedback...</p>
        </div>
      )}

      {data && (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows?.length ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      className="hover:bg-muted/50 cursor-pointer"
                      onClick={() => navigate(`/staff/feedback/${row.original.id}`)}
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
                      No feedback found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="cursor-pointer"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {data.page} of {data.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="cursor-pointer"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
