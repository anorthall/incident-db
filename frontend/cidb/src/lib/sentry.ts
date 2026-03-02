import * as Sentry from "@sentry/react";

export function captureApiError(
  error: Error,
  context: { endpoint: string; method: string; attempt?: number }
) {
  Sentry.captureException(error, {
    tags: {
      type: "api_error",
      endpoint: context.endpoint,
      method: context.method,
    },
    extra: {
      attempt: context.attempt,
    },
  });
}

export { Sentry };
