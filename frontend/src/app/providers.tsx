import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { setupAuth } from "@/features/auth";
import { ErrorBoundary } from "@/shared/observability/sentry";

import { ErrorFallback } from "./error-fallback";

export function createQueryClient(): QueryClient {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  });
  setupAuth(queryClient);
  return queryClient;
}

type ProvidersProps = {
  queryClient: QueryClient;
  children: ReactNode;
};

export function Providers({ queryClient, children }: ProvidersProps) {
  return (
    <ErrorBoundary fallback={<ErrorFallback />}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ErrorBoundary>
  );
}
