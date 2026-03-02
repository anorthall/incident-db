import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { FeedbackStatuses, getFeedback, resolveFeedback, type FeedbackStatus } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  pending: "default",
  reviewed: "secondary",
  resolved: "outline",
  dismissed: "destructive",
};

export function FeedbackDetailPage() {
  const { id } = useParams<{ id: string }>();
  const feedbackId = parseInt(id || "0", 10);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const [newStatus, setNewStatus] = useState<FeedbackStatus | "">("");
  const [reviewerNotes, setReviewerNotes] = useState("");

  const {
    data: feedback,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["feedback", feedbackId],
    queryFn: () => getFeedback(feedbackId),
    enabled: isAuthenticated && (user?.is_staff || user?.is_editor) && feedbackId > 0,
  });

  const resolveMutation = useMutation({
    mutationFn: () => {
      if (!newStatus) throw new Error("Please select a status");
      return resolveFeedback(feedbackId, newStatus, reviewerNotes);
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["feedback"] });
      navigate("/staff/feedback");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to resolve feedback");
    },
  });

  const handleResolve = () => {
    if (!newStatus) {
      toast.error("Please select a status");
      return;
    }
    resolveMutation.mutate();
  };

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

  if (!feedbackId) {
    return <Navigate to="/staff/feedback" replace />;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/staff/feedback")}
          className="cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Feedback
        </Button>
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

      {feedback && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-xl">Feedback #{feedback.id}</CardTitle>
                  <CardDescription>
                    Submitted{" "}
                    {new Date(feedback.created_at).toLocaleDateString("en-US", {
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </CardDescription>
                </div>
                <Badge variant={STATUS_VARIANT[feedback.status] || "outline"}>
                  {feedback.status_display}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Reason</Label>
                  <p className="font-medium">{feedback.reason_display}</p>
                </div>

                <div className="space-y-1">
                  <Label className="text-muted-foreground">Reporter</Label>
                  <p className="font-medium">{feedback.reporter?.email || "Anonymous"}</p>
                </div>
              </div>

              {feedback.incident && (
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Related Incident</Label>
                  <p>
                    <Link
                      to={`/incidents/${feedback.incident.id}`}
                      className="text-primary hover:underline font-medium inline-flex items-center gap-1"
                    >
                      {feedback.incident.title}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </p>
                </div>
              )}

              {feedback.url && (
                <div className="space-y-1">
                  <Label className="text-muted-foreground">URL</Label>
                  <p>
                    <a
                      href={feedback.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline inline-flex items-center gap-1 break-all"
                    >
                      {feedback.url}
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                  </p>
                </div>
              )}

              <div className="space-y-1">
                <Label className="text-muted-foreground">Description</Label>
                <p className="whitespace-pre-wrap bg-muted/50 p-4 rounded-md">
                  {feedback.description}
                </p>
              </div>

              {feedback.reviewer_notes && (
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Reviewer Notes</Label>
                  <p className="whitespace-pre-wrap bg-muted/50 p-4 rounded-md">
                    {feedback.reviewer_notes}
                  </p>
                </div>
              )}

              <div className="text-sm text-muted-foreground">
                Last updated:{" "}
                {new Date(feedback.updated_at).toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Update Status</CardTitle>
              <CardDescription>Change the status and add reviewer notes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="status">New Status</Label>
                <Select value={newStatus} onValueChange={(v) => setNewStatus(v as FeedbackStatus)}>
                  <SelectTrigger className="w-full md:w-[250px] cursor-pointer">
                    <SelectValue placeholder="Select a status" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(FeedbackStatuses).map(([key, label]) => (
                      <SelectItem key={key} value={key} className="cursor-pointer">
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Reviewer Notes</Label>
                <Textarea
                  id="notes"
                  placeholder="Add internal notes about this feedback..."
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  rows={4}
                />
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleResolve}
                  disabled={!newStatus || resolveMutation.isPending}
                  className="cursor-pointer"
                >
                  {resolveMutation.isPending ? "Updating..." : "Update Status"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate("/staff/feedback")}
                  className="cursor-pointer"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
