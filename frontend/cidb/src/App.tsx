import {
  createRoutesFromChildren,
  matchRoutes,
  Route,
  Routes,
  useLocation,
  useNavigationType,
} from "react-router-dom";
import { RootLayout } from "@/components/layout/SidebarLayout";
import { Toaster } from "@/components/ui/sonner";
import { FeedbackDetailPage } from "@/pages/FeedbackDetailPage";
import { FeedbackListPage } from "@/pages/FeedbackListPage";
import { IncidentPage } from "@/pages/IncidentPage";
import { PrivacyPage } from "@/pages/PrivacyPage";
import { SearchPage } from "@/pages/SearchPage";
import { StaffLoginPage } from "@/pages/StaffLoginPage";

import * as Sentry from "@sentry/react";
import * as React from "react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    Sentry.reactRouterV7BrowserTracingIntegration({
      useEffect: React.useEffect,
      useLocation,
      useNavigationType,
      createRoutesFromChildren,
      matchRoutes,
    }),
    Sentry.replayIntegration(),
  ],
  sendDefaultPii: true,
  enableLogs: true,
  tracesSampleRate: 0.1,
  tracePropagationTargets: [
    /^\//,
    ...(import.meta.env.VITE_API_URL ? [new RegExp(`^${import.meta.env.VITE_API_URL}`)] : []),
  ],
  replaysSessionSampleRate: 0.05,
  replaysOnErrorSampleRate: 1.0,
});

const SentryRoutes = Sentry.withSentryReactRouterV7Routing(Routes);

function App() {
  return (
    <Sentry.ErrorBoundary>
      <SentryRoutes>
        <Route element={<RootLayout />}>
          <Route path="/" element={<SearchPage />} />
          <Route path="/incidents/:id" element={<IncidentPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/staff/login" element={<StaffLoginPage />} />
          <Route path="/staff/feedback" element={<FeedbackListPage />} />
          <Route path="/staff/feedback/:id" element={<FeedbackDetailPage />} />
        </Route>
      </SentryRoutes>
      <Toaster position="bottom-right" />
    </Sentry.ErrorBoundary>
  );
}

export default App;
