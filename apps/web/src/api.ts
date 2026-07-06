import type { CityDetail, CitySummary, ExploreCity, JobListing } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function fetchExplore(limit = 100, role = ""): Promise<ExploreCity[]> {
  const roleQuery = role.trim() ? `&role=${encodeURIComponent(role.trim())}` : "";
  return getJson(`/api/v1/explore?limit=${limit}${roleQuery}`);
}

export function fetchProfiles(): Promise<CitySummary[]> {
  return getJson("/api/v1/cities");
}

export function fetchCity(slug: string): Promise<CityDetail> {
  return getJson(`/api/v1/cities/${encodeURIComponent(slug)}`);
}

export function fetchJobs(placeGeoid: string, limit = 50): Promise<JobListing[]> {
  return getJson(`/api/v1/jobs?place_geoid=${encodeURIComponent(placeGeoid)}&limit=${limit}`);
}
