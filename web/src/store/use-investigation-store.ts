import { create } from "zustand";

type InvestigationState = {
  query: string;
  topK: number;
  providers: string[];
  sidebarCollapsed: boolean;
  setQuery: (query: string) => void;
  setTopK: (topK: number) => void;
  toggleProvider: (provider: string) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
};

export const useInvestigationStore = create<InvestigationState>((set) => ({
  query: "payment timeout during checkout",
  topK: 5,
  providers: ["huggingface", "openai"],
  sidebarCollapsed: false,
  setQuery: (query) => set({ query }),
  setTopK: (topK) => set({ topK }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleProvider: (provider) =>
    set((state) => {
      const exists = state.providers.includes(provider);
      if (exists) {
        return {
          providers: state.providers.filter((item) => item !== provider),
        };
      }

      return { providers: [...state.providers, provider] };
    }),
}));
