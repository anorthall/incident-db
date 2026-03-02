import { useMutation } from "@tanstack/react-query";
import * as React from "react";
import { useCallback, useState } from "react";
import { createReport, type CreateReportParams } from "@/lib/api";

interface UseReportFormOptions {
  incidentId?: number | null;
  url?: string;
  onSuccess?: () => void;
}

export function useReportForm({
  incidentId = null,
  url = "",
  onSuccess,
}: UseReportFormOptions = {}) {
  const [reason, setReason] = useState<string>("");
  const [description, setDescription] = useState("");
  const [email, setEmail] = useState("");

  const mutation = useMutation({
    mutationFn: createReport,
    onSuccess,
  });

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const params: CreateReportParams = {
        incident_id: incidentId,
        reason: reason || "other",
        description: description.trim() || undefined,
        email: email.trim() || undefined,
        url: url || undefined,
      };
      mutation.mutate(params);
    },
    [incidentId, reason, description, email, url, mutation]
  );

  const resetForm = useCallback(() => {
    setReason("");
    setDescription("");
    setEmail("");
    mutation.reset();
  }, [mutation]);

  return {
    reason,
    setReason,
    description,
    setDescription,
    email,
    setEmail,
    handleSubmit,
    resetForm,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    isPending: mutation.isPending,
  };
}
