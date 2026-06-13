export interface Movie {
  movie_id: number;
  title: string;
  genres: string[];
  year: number;
  runtime: number;
  maturity: string;
  tagline: string;
  overview: string;
  popularity_score: number;
  avg_rating: number;
  rating_count: number;
}

export interface Recommendation extends Movie {
  score: number;
  strategy: string;
}

export interface DatasetStats {
  num_users: number;
  num_movies: number;
  num_ratings: number;
  num_genres: number;
  avg_rating: number;
  sparsity: number;
}

export type StrategyId = "popularity" | "content" | "onboarding" | "dropout" | "item_cf";

export interface StrategyInfo {
  id: StrategyId;
  name: string;
  description: string;
  cold_start_type: string;
}

export interface LearningCurvePoint {
  interactions: number;
  recall_at_10: number;
}

export interface StrategyCurve {
  strategy: string;
  label: string;
  points: LearningCurvePoint[];
}

export interface LearningCurveResponse {
  curves: StrategyCurve[];
  sample_users: number;
  note: string;
}

export interface RecommendRequest {
  strategy: StrategyId;
  top_n?: number;
  user_id?: number | null;
  preferred_genres?: string[];
  onboarding_ratings?: Record<number, number>;
}

const API_BASE = "/api";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getStats: () => fetchJson<DatasetStats>("/stats"),
  getStrategies: () => fetchJson<StrategyInfo[]>("/strategies"),
  getGenres: () => fetchJson<{ genres: string[] }>("/genres"),
  getCatalog: () => fetchJson<Movie[]>("/catalog"),
  getSimilar: (movieId: number) => fetchJson<Movie[]>(`/similar/${movieId}`),
  getOnboardingItems: () => fetchJson<Movie[]>("/onboarding/items"),
  getWarmUsers: () => fetchJson<{ users: number[]; total: number }>("/users/warm"),
  recommend: (body: RecommendRequest) =>
    fetchJson<Recommendation[]>("/recommend", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getLearningCurve: (sampleUsers = 50) =>
    fetchJson<LearningCurveResponse>(`/evaluation/learning-curve?sample_users=${sampleUsers}`),
};
