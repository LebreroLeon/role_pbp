import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { AuthBootstrap } from "../components/auth/AuthBootstrap";
import { queryClient } from "../lib/queryClient";

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthBootstrap />
      {children}
    </QueryClientProvider>
  );
}
