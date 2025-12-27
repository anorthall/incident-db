import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App.tsx";
import "./index.css";
import { AuthProvider } from "./lib/auth-context.tsx";
import { FeedbackProvider } from "./lib/feedback-context.tsx";
import { fetchCsrfToken } from "./lib/csrf.ts";
import { ThemeProvider } from "./lib/theme.tsx";

void fetchCsrfToken();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <AuthProvider>
            <FeedbackProvider>
              <App />
            </FeedbackProvider>
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
);
