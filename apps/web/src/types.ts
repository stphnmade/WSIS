export type IntentId = "offer" | "opportunities" | "compare" | "explore";

export type ExploreCity = {
  place_geoid: string;
  slug: string;
  name: string;
  state_code: string;
  latitude: number;
  longitude: number;
  active_listing_count: number;
  latest_listing_date: string;
  coverage_status: string;
};

export type JobListing = {
  job_id: string;
  place_geoid: string;
  place_name: string;
  state_code: string;
  company_name: string;
  title: string;
  category: string;
  locations: string;
  job_url: string;
  date_posted: string;
  date_updated: string;
  sponsorship: string;
  source: string;
};

export type CitySummary = {
  slug: string;
  name: string;
  state_code: string;
  overall_score: number;
  headline: string;
  population: number;
  score_context: {
    overall_confidence: string;
    eligible_for_mvp_ranking: boolean;
  };
};

export type CityDetail = {
  summary: CitySummary;
  metrics: {
    median_rent: number;
    median_income: number;
    unemployment_pct: number;
    education_bachelors_pct: number;
    mean_commute_minutes: number;
    avg_temp_f: number;
    sunny_days: number;
    violent_crime_per_100k: number;
  };
  highlights: string[];
  reddit_panel?: {
    included_in_score: boolean;
    summary: string;
    themes: string[];
    posts_analyzed: number;
    generated_at: string;
  };
};

export type UserProfile = {
  intent: IntentId;
  role: string;
  offeredCity: string;
  housingBudget: number;
  placeScale: "major" | "midsize" | "small" | "open";
  socialEnergy: "quiet" | "mix" | "lively" | "open";
  greenery: "parks" | "nature" | "both" | "open";
};
