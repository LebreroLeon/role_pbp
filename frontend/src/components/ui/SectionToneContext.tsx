import { createContext, useContext, type ReactNode } from "react";

import { DEFAULT_SECTION_TONE, type SectionTone } from "./sectionTone";

const SectionToneContext = createContext<SectionTone>(DEFAULT_SECTION_TONE);

type SectionToneProviderProps = {
  tone?: SectionTone;
  children: ReactNode;
};

export function SectionToneProvider({ tone = DEFAULT_SECTION_TONE, children }: SectionToneProviderProps) {
  return <SectionToneContext.Provider value={tone}>{children}</SectionToneContext.Provider>;
}

export function useSectionTone(): SectionTone {
  return useContext(SectionToneContext);
}

/** Envuelve un bloque con otro tono (p. ej. paso del wizard de biblioteca). */
export function Section({ tone, children, className }: { tone: SectionTone; children: ReactNode; className?: string }) {
  return (
    <SectionToneProvider tone={tone}>
      {className ? <div className={className}>{children}</div> : children}
    </SectionToneProvider>
  );
}
