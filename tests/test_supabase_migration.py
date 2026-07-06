from pathlib import Path


MIGRATION = Path("supabase/migrations/202607050001_initial_schema.sql")
PRIVATE_TABLES = (
    "app_users",
    "preference_profiles",
    "saved_cities",
    "saved_searches",
    "alerts",
    "recommendation_runs",
)


def test_private_tables_enable_rls_and_have_no_anonymous_policy() -> None:
    sql = MIGRATION.read_text()

    for table in PRIVATE_TABLES:
        assert f"alter table public.{table} enable row level security" in sql

    assert "to anon" not in sql
    assert "owns_app_user" in sql


def test_exact_financial_values_require_timestamped_consent() -> None:
    sql = MIGRATION.read_text()

    assert "exact_annual_income" in sql
    assert "exact_monthly_housing_budget" in sql
    assert "exact_financial_data_consent" in sql
    assert "exact_financial_data_consented_at" in sql
    assert "or (exact_financial_data_consent and exact_financial_data_consented_at is not null)" in sql


def test_alert_cannot_reference_another_users_saved_search() -> None:
    sql = MIGRATION.read_text()

    assert "foreign key (saved_search_id, user_id)" in sql
    assert "references public.saved_searches(id, user_id)" in sql
