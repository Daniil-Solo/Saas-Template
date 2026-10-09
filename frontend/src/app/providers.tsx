import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { setupAuth } from "@/features/auth";

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
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
