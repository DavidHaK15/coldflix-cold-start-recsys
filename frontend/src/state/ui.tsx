import { createContext, useContext, useState, type ReactNode } from "react";
import type { Movie } from "../api/client";

interface UIContextValue {
  selectedMovie: Movie | null;
  openMovie: (movie: Movie) => void;
  closeMovie: () => void;
}

const UIContext = createContext<UIContextValue | null>(null);

export function UIProvider({ children }: { children: ReactNode }) {
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  return (
    <UIContext.Provider
      value={{
        selectedMovie,
        openMovie: setSelectedMovie,
        closeMovie: () => setSelectedMovie(null),
      }}
    >
      {children}
    </UIContext.Provider>
  );
}

export function useUI(): UIContextValue {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error("useUI must be used within UIProvider");
  return ctx;
}
