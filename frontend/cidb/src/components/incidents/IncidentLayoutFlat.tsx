import { Calendar, Eye, MapPin, Mountain, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { IncidentDetail } from "@/lib/api";
import { isIncidentViewed } from "@/lib/viewed-incidents";

interface IncidentLayoutProps {
  incident: IncidentDetail;
}

export function IncidentLayoutFlat({ incident }: IncidentLayoutProps) {
  const hasSources = incident.origin_publication || incident.references.length > 0;
  const viewed = isIncidentViewed(incident.id);

  return (
    <article>
      {/* Title and meta */}
      <header className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-3">{incident.title}</h1>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
          {viewed && (
            <span className="inline-flex items-center gap-1.5 text-primary/70">
              <Eye className="h-4 w-4" />
              Viewed
            </span>
          )}
          {incident.date && (
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="h-4 w-4" />
              {incident.date.display}
            </span>
          )}
          {incident.cave && (
            <span className="inline-flex items-center gap-1.5">
              <Mountain className="h-4 w-4" />
              {incident.cave.name}
            </span>
          )}
          {incident.cave?.location && (
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="h-4 w-4" />
              {[
                incident.cave.location.region,
                incident.cave.location.state,
                incident.cave.location.country,
              ]
                .filter(Boolean)
                .join(", ")}
            </span>
          )}
        </div>

        {incident.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {incident.tags.map((tag) => (
              <Badge key={tag.id} variant="outline">
                {tag.name}
              </Badge>
            ))}
          </div>
        )}
      </header>

      {/* Summary */}
      {incident.summary && (
        <div className="mb-12">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
            <Sparkles className="h-3 w-3" />
            <span>AI-generated summary</span>
          </div>
          <blockquote className="border-l-4 border-primary/30 pl-4 text-lg leading-relaxed">
            {incident.summary}
          </blockquote>
        </div>
      )}

      {/* Report */}
      {incident.report && (
        <section className="mb-12">
          <h2 className="text-sm font-medium tracking-tight text-muted-foreground uppercase mb-3">
            Report
          </h2>
          <p className="whitespace-pre-wrap leading-7">{incident.report}</p>
        </section>
      )}

      {/* Analysis */}
      {incident.analysis && (
        <section className="mb-12">
          <h2 className="text-sm font-medium tracking-tight text-muted-foreground uppercase mb-3">
            Analysis
          </h2>
          <p className="whitespace-pre-wrap leading-7">{incident.analysis}</p>
        </section>
      )}

      {/* References */}
      {hasSources && (
        <section className="mb-12">
          <h2 className="text-sm font-medium tracking-tight text-muted-foreground uppercase mb-3">
            Sources
          </h2>

          {incident.origin_publication && (
            <p className="text-sm text-muted-foreground mb-4">
              Originally published in{" "}
              <span className="text-foreground">{incident.origin_publication.title}</span>
            </p>
          )}

          {incident.references.length > 0 && (
            <ol className="list-decimal list-outside ml-5 space-y-2 text-sm">
              {incident.references.map((ref, i) => (
                <li key={i} className="pl-1">
                  {ref.raw_citation ||
                    [ref.author, ref.title, ref.source].filter(Boolean).join(", ")}
                </li>
              ))}
            </ol>
          )}
        </section>
      )}

      {/* Metadata */}
      <footer className="text-xs text-muted-foreground mb-12">
        <span>Added {new Date(incident.created_at).toLocaleDateString()}</span>
        {incident.updated_at !== incident.created_at && (
          <>
            <span className="mx-2">·</span>
            <span>Updated {new Date(incident.updated_at).toLocaleDateString()}</span>
          </>
        )}
      </footer>
    </article>
  );
}
