import { createContext, useCallback, useContext, useState } from "react";

export interface IncidentContext {
  id: number;
  title: string;
}

interface FeedbackContextValue {
  isOpen: boolean;
  openFeedback: (incident?: IncidentContext) => void;
  closeFeedback: () => void;
  incident: IncidentContext | null;
}

const FeedbackContext = createContext<FeedbackContextValue | null>(null);

export function FeedbackProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [incident, setIncident] = useState<IncidentContext | null>(null);

  const openFeedback = useCallback((incident?: IncidentContext) => {
    setIncident(incident ?? null);
    setIsOpen(true);
  }, []);

  const closeFeedback = useCallback(() => {
    setIsOpen(false);
    setIncident(null);
  }, []);

  return (
    <FeedbackContext.Provider value={{ isOpen, openFeedback, closeFeedback, incident }}>
      {children}
    </FeedbackContext.Provider>
  );
}

export default function useFeedback() {
  const context = useContext(FeedbackContext);
  if (!context) {
    throw new Error("useFeedback must be used within a FeedbackProvider");
  }
  return context;
}
