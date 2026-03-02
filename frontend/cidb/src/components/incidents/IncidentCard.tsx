import { Check, Eye } from "lucide-react";
import { memo } from "react";
import { Badge } from "@/components/ui/badge";
import type { IncidentListItem } from "@/lib/api";
import { isIncidentViewed } from "@/lib/viewed-incidents";

interface IncidentCardProps {
  incident: IncidentListItem;
  onClick?: () => void;
}

export const IncidentCard = memo(function IncidentCard({ incident, onClick }: IncidentCardProps) {
  const viewed = isIncidentViewed(incident.id);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick?.();
    }
  };

  return (
    <article className="py-4 border-b last:border-b-0">
      <h2
        onClick={onClick}
        onKeyDown={handleKeyDown}
        tabIndex={onClick ? 0 : undefined}
        role={onClick ? "button" : undefined}
        className={`text-lg font-medium hover:underline cursor-pointer mb-1 w-fit flex items-center gap-2 ${viewed ? "text-muted-foreground" : ""}`}
      >
        {incident.title}
        {viewed && (
          <Check className="h-4 w-4 text-muted-foreground/70" aria-label="Previously viewed" />
        )}
      </h2>

      <div
        onClick={onClick}
        onKeyDown={handleKeyDown}
        tabIndex={onClick ? 0 : undefined}
        role={onClick ? "button" : undefined}
        aria-label={`View details for ${incident.title}`}
        className="flex items-center gap-2 text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground transition-colors w-fit"
      >
        {incident.date && <span>{incident.date.display}</span>}
        {incident.cave_name && (
          <>
            <span>·</span>
            <span>{incident.cave_name}</span>
          </>
        )}
        {incident.location_summary && (
          <>
            <span>·</span>
            <span>{incident.location_summary}</span>
          </>
        )}
        {incident.view_count > 0 && (
          <>
            <span>·</span>
            <span className="flex items-center gap-1">
              <Eye className="h-3 w-3" />
              {incident.view_count.toLocaleString()}
            </span>
          </>
        )}
      </div>

      {incident.summary && <p className="text-sm text-muted-foreground">{incident.summary}</p>}

      {incident.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {incident.tags.slice(0, 5).map((tag) => (
            <Badge key={tag.id} variant="outline" className="text-xs">
              {tag.name}
            </Badge>
          ))}
          {incident.tags.length > 5 && (
            <span className="text-xs text-muted-foreground">+{incident.tags.length - 5} more</span>
          )}
        </div>
      )}
    </article>
  );
});
