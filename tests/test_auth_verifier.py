from __future__ import annotations

import jwt
import pytest

from wsis.auth import AuthTokenError, SupabaseTokenVerifier
from wsis.auth.verifier import AuthConfigurationError, SupabaseAuthSettings


SETTINGS = SupabaseAuthSettings(
    issuer="https://example.supabase.co/auth/v1",
    audience="authenticated",
    jwks_url="https://example.supabase.co/auth/v1/.well-known/jwks.json",
)
TOKEN = "header.payload.signature"


def test_verifier_maps_trusted_claims_to_principal() -> None:
    verifier = SupabaseTokenVerifier(
        SETTINGS,
        decoder=lambda _: {
            "sub": "user-123",
            "email": "person@example.com",
            "email_verified": True,
            "aal": "aal1",
            "role": "authenticated",
        },
    )

    principal = verifier.verify(TOKEN)

    assert principal.subject == "user-123"
    assert principal.email == "person@example.com"
    assert principal.email_verified is True
    assert principal.assurance_level == "aal1"
    assert principal.role == "authenticated"


def test_verifier_rejects_malformed_token_before_decode() -> None:
    verifier = SupabaseTokenVerifier(SETTINGS, decoder=lambda _: {"sub": "unused"})

    with pytest.raises(AuthTokenError, match="Malformed"):
        verifier.verify("not-a-jwt")


def test_verifier_hides_jwt_validation_details() -> None:
    def reject(_: str) -> dict[str, str]:
        raise jwt.InvalidAudienceError("internal detail")

    verifier = SupabaseTokenVerifier(SETTINGS, decoder=reject)

    with pytest.raises(AuthTokenError, match="Invalid or expired"):
        verifier.verify(TOKEN)


def test_verifier_requires_subject() -> None:
    verifier = SupabaseTokenVerifier(SETTINGS, decoder=lambda _: {"role": "authenticated"})

    with pytest.raises(AuthTokenError, match="subject"):
        verifier.verify(TOKEN)


def test_settings_fail_closed_without_issuer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WSIS_SUPABASE_JWT_ISSUER", raising=False)
    monkeypatch.delenv("WSIS_SUPABASE_JWKS_URL", raising=False)

    with pytest.raises(AuthConfigurationError):
        SupabaseAuthSettings.from_env()
