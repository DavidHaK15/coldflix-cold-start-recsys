import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { StrategyId } from "../api/client";

export interface Profile {
  genres: string[];
  ratings: Record<number, number>;
  strategy: StrategyId;
  simulatedUserId: number | null;
  onboarded: boolean;
}

const STORAGE_KEY = "coldflix.profile.v1";

const DEFAULT_PROFILE: Profile = {
  genres: [],
  ratings: {},
  strategy: "dropout",
  simulatedUserId: null,
  onboarded: false,
};

interface ProfileContextValue extends Profile {
  interactionCount: number;
  toggleGenre: (genre: string) => void;
  setGenres: (genres: string[]) => void;
  rate: (movieId: number, rating: number) => void;
  setStrategy: (strategy: StrategyId) => void;
  setSimulatedUser: (userId: number | null) => void;
  completeOnboarding: () => void;
  reset: () => void;
}

const ProfileContext = createContext<ProfileContextValue | null>(null);

function loadProfile(): Profile {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_PROFILE, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return DEFAULT_PROFILE;
}

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile>(loadProfile);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
  }, [profile]);

  const toggleGenre = useCallback((genre: string) => {
    setProfile((p) => ({
      ...p,
      genres: p.genres.includes(genre)
        ? p.genres.filter((g) => g !== genre)
        : [...p.genres, genre],
    }));
  }, []);

  const setGenres = useCallback((genres: string[]) => {
    setProfile((p) => ({ ...p, genres }));
  }, []);

  const rate = useCallback((movieId: number, rating: number) => {
    setProfile((p) => ({ ...p, ratings: { ...p.ratings, [movieId]: rating } }));
  }, []);

  const setStrategy = useCallback((strategy: StrategyId) => {
    setProfile((p) => ({ ...p, strategy }));
  }, []);

  const setSimulatedUser = useCallback((simulatedUserId: number | null) => {
    setProfile((p) => ({ ...p, simulatedUserId }));
  }, []);

  const completeOnboarding = useCallback(() => {
    setProfile((p) => ({ ...p, onboarded: true }));
  }, []);

  const reset = useCallback(() => setProfile({ ...DEFAULT_PROFILE, onboarded: true }), []);

  const value = useMemo<ProfileContextValue>(
    () => ({
      ...profile,
      interactionCount: Object.keys(profile.ratings).length,
      toggleGenre,
      setGenres,
      rate,
      setStrategy,
      setSimulatedUser,
      completeOnboarding,
      reset,
    }),
    [profile, toggleGenre, setGenres, rate, setStrategy, setSimulatedUser, completeOnboarding, reset],
  );

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfile(): ProfileContextValue {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error("useProfile must be used within ProfileProvider");
  return ctx;
}
