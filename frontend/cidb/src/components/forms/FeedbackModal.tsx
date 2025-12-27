import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSidebar } from "@/components/ui/sidebar";
import { Textarea } from "@/components/ui/textarea";
import { MOBILE_BREAKPOINT } from "@/constants.ts";
import { useReportForm } from "@/hooks/use-report-form";
import { type ReportReason, ReportReasons } from "@/lib/api";
import useFeedback from "@/lib/feedback-context";

export function FeedbackModal() {
  const { isOpen, closeFeedback, incident } = useFeedback();
  const { state, isMobile } = useSidebar();
  const isCollapsed = state === "collapsed";
  const isIncidentPage = !!incident;

  const {
    reason,
    setReason,
    description,
    setDescription,
    email,
    setEmail,
    handleSubmit,
    resetForm,
    isSuccess,
    isError,
    isPending,
  } = useReportForm({
    incidentId: incident?.id ?? null,
    url: typeof window !== "undefined" ? window.location.href : "",
    onSuccess: undefined,
  });

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      resetForm();
      closeFeedback();
    }
  };

  const canSubmit = isIncidentPage ? !!reason : description.trim().length > 0;

  const sidebarOffset = isMobile ? "0rem" : isCollapsed ? "1.5rem" : "8rem";

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-xl"
        style={{ left: `calc(50% + ${sidebarOffset})` }}
        onOpenAutoFocus={(e) => {
          if (window.innerWidth < MOBILE_BREAKPOINT) e.preventDefault();
        }}
      >
        <DialogHeader className="pb-4">
          <DialogTitle className="text-xl">
            {isSuccess ? "Feedback sent" : "Send feedback"}
          </DialogTitle>
          <DialogDescription className={isSuccess ? "hidden" : "text-base"}>
            {isIncidentPage
              ? `Help us improve '${incident.title}'.`
              : "Help us improve the Caving Incident Database."}
          </DialogDescription>
        </DialogHeader>

        {isSuccess ? (
          <div className="text-center">
            <p className="text-base text-muted-foreground pt-4 pb-10">
              Thank you for your feedback. We'll review it shortly.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {isIncidentPage && (
              <div className="space-y-3">
                <Label htmlFor="reason" className="text-base">
                  Issue type
                </Label>
                <Select value={reason} onValueChange={(v) => setReason(v as ReportReason)}>
                  <SelectTrigger className="w-full h-11 text-base cursor-pointer">
                    <SelectValue placeholder="Select an issue type" />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.entries(ReportReasons) as [ReportReason, string][]).map(
                      ([value, label]) => (
                        <SelectItem key={value} value={value} className="cursor-pointer">
                          {label}
                        </SelectItem>
                      )
                    )}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-3">
              <Label htmlFor="description" className="text-base">
                {isIncidentPage ? (
                  <>
                    Description <span className="text-muted-foreground">(optional)</span>
                  </>
                ) : (
                  "Your feedback"
                )}
              </Label>
              <Textarea
                id="description"
                placeholder={
                  isIncidentPage ? "Please describe the issue..." : "Tell us what you think..."
                }
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={8}
                className="text-base"
              />
            </div>

            <div className="space-y-3">
              <Label htmlFor="email" className="text-base">
                Email <span className="text-muted-foreground">(optional)</span>
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="text-base h-11"
              />
            </div>

            {isError && (
              <p className="text-base text-destructive">
                Failed to submit feedback. Please try again.
              </p>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="ghost"
                size="lg"
                className="cursor-pointer"
                onClick={() => handleOpenChange(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="lg"
                className="cursor-pointer"
                disabled={!canSubmit || isPending}
              >
                {isPending ? "Submitting..." : "Submit feedback"}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
