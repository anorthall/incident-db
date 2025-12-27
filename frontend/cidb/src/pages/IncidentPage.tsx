import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";

import { IncidentLayoutFlat } from "@/components/incidents/IncidentLayoutFlat";
import { Button } from "@/components/ui/button";
import { getIncident } from "@/lib/api";
import { markIncidentViewed } from "@/lib/viewed-incidents";

export function IncidentPage() {
  const { id } = useParams<{ id: string }>();
  const incidentId = parseInt(id!, 10);

  const {
    data: incident,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["incident", incidentId],
    queryFn: () => getIncident(incidentId),
    enabled: !isNaN(incidentId),
  });

  useEffect(() => {
    if (incident) {
      markIncidentViewed(incident.id, incident.title);
    }
  }, [incident]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-destructive">Incident not found</p>
        <Button variant="ghost" asChild>
          <Link to="/">Back to search</Link>
        </Button>
      </div>
    );
  }

  return <IncidentLayoutFlat incident={incident} />;
}
