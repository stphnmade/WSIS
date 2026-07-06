begin;

create extension if not exists pgcrypto;

create table public.states (
  id uuid primary key default gen_random_uuid(),
  fips_code text not null unique check (fips_code ~ '^[0-9]{2}$'),
  abbreviation text not null unique check (abbreviation ~ '^[A-Z]{2}$'),
  name text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.cities (
  id uuid primary key default gen_random_uuid(),
  state_id uuid not null references public.states(id) on delete restrict,
  place_fips text not null check (place_fips ~ '^[0-9]{5}$'),
  slug text not null unique check (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  name text not null,
  latitude double precision check (latitude between -90 and 90),
  longitude double precision check (longitude between -180 and 180),
  population bigint check (population >= 0),
  timezone text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (state_id, place_fips),
  unique (state_id, name)
);

create index cities_state_id_idx on public.cities(state_id);
create index cities_name_idx on public.cities(name);

create table public.data_sources (
  id uuid primary key default gen_random_uuid(),
  key text not null unique check (key ~ '^[a-z0-9_]+$'),
  name text not null,
  homepage_url text not null check (homepage_url ~ '^https://'),
  license_name text,
  license_url text check (license_url is null or license_url ~ '^https://'),
  attribution text,
  refresh_cadence interval,
  terms_reviewed_at date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.city_metrics (
  id bigint generated always as identity primary key,
  city_id uuid not null references public.cities(id) on delete cascade,
  source_id uuid not null references public.data_sources(id) on delete restrict,
  metric_key text not null check (metric_key ~ '^[a-z0-9_]+$'),
  value_numeric numeric,
  value_text text,
  unit text,
  period_start date,
  period_end date,
  observed_at timestamptz,
  fetched_at timestamptz not null default now(),
  source_record_url text check (source_record_url is null or source_record_url ~ '^https://'),
  source_record_id text,
  metadata jsonb not null default '{}'::jsonb,
  check (num_nonnulls(value_numeric, value_text) = 1),
  check (period_end is null or period_start is null or period_end >= period_start),
  unique nulls not distinct (city_id, source_id, metric_key, period_start, source_record_id)
);

create index city_metrics_lookup_idx
  on public.city_metrics(city_id, metric_key, period_end desc nulls last);
create index city_metrics_source_idx on public.city_metrics(source_id, fetched_at desc);

create table public.jobs (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references public.data_sources(id) on delete restrict,
  external_id text not null,
  canonical_url text not null check (canonical_url ~ '^https://'),
  employer_name text not null,
  title text not null,
  description_text text,
  employment_type text,
  workplace_type text check (workplace_type in ('on_site', 'hybrid', 'remote', 'unknown')),
  salary_min numeric check (salary_min >= 0),
  salary_max numeric check (salary_max >= 0),
  salary_currency char(3),
  salary_period text check (salary_period in ('hour', 'month', 'year')),
  posted_at timestamptz,
  expires_at timestamptz,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  is_active boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  check (salary_max is null or salary_min is null or salary_max >= salary_min),
  check (expires_at is null or posted_at is null or expires_at >= posted_at),
  unique (source_id, external_id)
);

create index jobs_active_posted_idx on public.jobs(is_active, posted_at desc);
create index jobs_title_idx on public.jobs(title);

create table public.job_locations (
  job_id uuid not null references public.jobs(id) on delete cascade,
  city_id uuid references public.cities(id) on delete set null,
  location_text text not null,
  is_remote boolean not null default false,
  primary key (job_id, location_text)
);

create index job_locations_city_id_idx on public.job_locations(city_id);

create table public.app_users (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid not null unique references auth.users(id) on delete cascade,
  consent_version text,
  consented_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.preference_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.app_users(id) on delete cascade,
  version integer not null default 1 check (version > 0),
  answers jsonb not null default '{}'::jsonb,
  income_band text,
  housing_budget_band text,
  exact_annual_income numeric check (exact_annual_income >= 0),
  exact_monthly_housing_budget numeric check (exact_monthly_housing_budget >= 0),
  exact_financial_data_consent boolean not null default false,
  exact_financial_data_consented_at timestamptz,
  created_at timestamptz not null default now(),
  superseded_at timestamptz,
  check (
    (exact_annual_income is null and exact_monthly_housing_budget is null)
    or (exact_financial_data_consent and exact_financial_data_consented_at is not null)
  ),
  check (not exact_financial_data_consent or exact_financial_data_consented_at is not null),
  unique (user_id, version)
);

create index preference_profiles_user_active_idx
  on public.preference_profiles(user_id, created_at desc) where superseded_at is null;

create table public.saved_cities (
  user_id uuid not null references public.app_users(id) on delete cascade,
  city_id uuid not null references public.cities(id) on delete cascade,
  note text check (char_length(note) <= 2000),
  created_at timestamptz not null default now(),
  primary key (user_id, city_id)
);

create table public.saved_searches (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.app_users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 120),
  criteria jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.saved_searches add constraint saved_searches_id_user_unique unique (id, user_id);

create index saved_searches_user_idx on public.saved_searches(user_id, updated_at desc);

create table public.alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.app_users(id) on delete cascade,
  saved_search_id uuid,
  alert_type text not null check (alert_type in ('jobs', 'city_data', 'saved_search')),
  delivery_channel text not null check (delivery_channel in ('email', 'push', 'in_app')),
  cadence text not null check (cadence in ('instant', 'daily', 'weekly')),
  is_enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (saved_search_id, user_id)
    references public.saved_searches(id, user_id) on delete cascade
);

create index alerts_user_enabled_idx on public.alerts(user_id, is_enabled);

create table public.recommendation_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.app_users(id) on delete set null,
  anonymous_session_id uuid,
  input_snapshot jsonb not null,
  model_version text not null,
  result jsonb not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz,
  check (user_id is not null or anonymous_session_id is not null),
  check (expires_at is null or expires_at > created_at)
);

create index recommendation_runs_user_idx
  on public.recommendation_runs(user_id, created_at desc) where user_id is not null;
create index recommendation_runs_expiry_idx
  on public.recommendation_runs(expires_at) where expires_at is not null;

alter table public.states enable row level security;
alter table public.cities enable row level security;
alter table public.data_sources enable row level security;
alter table public.city_metrics enable row level security;
alter table public.jobs enable row level security;
alter table public.job_locations enable row level security;
alter table public.app_users enable row level security;
alter table public.preference_profiles enable row level security;
alter table public.saved_cities enable row level security;
alter table public.saved_searches enable row level security;
alter table public.alerts enable row level security;
alter table public.recommendation_runs enable row level security;

create policy "public read states" on public.states for select using (true);
create policy "public read cities" on public.cities for select using (true);
create policy "public read data sources" on public.data_sources for select using (true);
create policy "public read city metrics" on public.city_metrics for select using (true);
create policy "public read active jobs" on public.jobs for select using (is_active);
create policy "public read active job locations" on public.job_locations for select using (
  exists (select 1 from public.jobs where jobs.id = job_locations.job_id and jobs.is_active)
);

create function public.owns_app_user(target_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.app_users
    where id = target_user_id and auth_user_id = (select auth.uid())
  );
$$;

revoke all on function public.owns_app_user(uuid) from public;
grant execute on function public.owns_app_user(uuid) to authenticated;

create policy "users select self" on public.app_users for select to authenticated
  using (auth_user_id = (select auth.uid()));
create policy "users insert self" on public.app_users for insert to authenticated
  with check (auth_user_id = (select auth.uid()));
create policy "users update self" on public.app_users for update to authenticated
  using (auth_user_id = (select auth.uid()))
  with check (auth_user_id = (select auth.uid()));
create policy "users delete self" on public.app_users for delete to authenticated
  using (auth_user_id = (select auth.uid()));

create policy "preference profiles owned" on public.preference_profiles for all to authenticated
  using ((select public.owns_app_user(user_id)))
  with check ((select public.owns_app_user(user_id)));
create policy "saved cities owned" on public.saved_cities for all to authenticated
  using ((select public.owns_app_user(user_id)))
  with check ((select public.owns_app_user(user_id)));
create policy "saved searches owned" on public.saved_searches for all to authenticated
  using ((select public.owns_app_user(user_id)))
  with check ((select public.owns_app_user(user_id)));
create policy "alerts owned" on public.alerts for all to authenticated
  using ((select public.owns_app_user(user_id)))
  with check ((select public.owns_app_user(user_id)));
create policy "recommendation runs owned" on public.recommendation_runs for all to authenticated
  using (user_id is not null and (select public.owns_app_user(user_id)))
  with check (user_id is not null and (select public.owns_app_user(user_id)));

commit;
