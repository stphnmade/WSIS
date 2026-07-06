# WSIS Supabase foundation

This directory contains the versioned Postgres schema for public city/job data
and private user data. The migration can be applied locally without production
credentials by using the Supabase CLI:

```bash
supabase init  # first run only; creates local config.toml
supabase start
supabase db reset
```

Production migrations should run from CI or an operator workstation using a
secret database URL. Never expose the database password, JWT secret, or
`service_role` key to the Vite bundle. Browser code may receive only the
Supabase URL and publishable/anonymous key.

## Authorization model

- Geography, provenance, metrics, and active jobs are publicly readable.
- Public clients cannot write pipeline data; ingestion uses a server-only
  database role or service-role client.
- User tables have row-level security enabled and no anonymous policies.
- Authenticated ownership is resolved through `app_users.auth_user_id = auth.uid()`.
- Anonymous recommendation input is written only through FastAPI with a
  server-generated session identifier; it is not directly exposed by RLS.
- Exact income or housing budget values require explicit, timestamped consent.
  Prefer bands unless exact values materially improve a requested calculation.

FastAPI validates Supabase access tokens using the project's asymmetric JWKS.
Set the issuer and audience explicitly. The application intentionally has no
fallback JWT secret and does not accept tokens when auth is unconfigured.

## Environment variables

```dotenv
WSIS_SUPABASE_URL=https://project-ref.supabase.co
WSIS_SUPABASE_PUBLISHABLE_KEY=
WSIS_SUPABASE_JWT_ISSUER=https://project-ref.supabase.co/auth/v1
WSIS_SUPABASE_JWT_AUDIENCE=authenticated
WSIS_SUPABASE_JWKS_URL=https://project-ref.supabase.co/auth/v1/.well-known/jwks.json
WSIS_SUPABASE_JWKS_CACHE_SECONDS=600
```

The publishable key is configuration, not authorization. Every private request
still requires a valid user access token and passes both FastAPI authorization
and database RLS.
