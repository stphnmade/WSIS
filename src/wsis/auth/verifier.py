from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import os
from typing import Any

import jwt
from jwt import PyJWKClient

from wsis.auth.principal import AuthPrincipal


class AuthConfigurationError(RuntimeError):
    """Raised when required identity-provider settings are missing."""


class AuthTokenError(ValueError):
    """Raised when an access token cannot be trusted."""


ClaimsDecoder = Callable[[str], Mapping[str, Any]]


@dataclass(frozen=True)
class SupabaseAuthSettings:
    issuer: str
    audience: str
    jwks_url: str
    jwks_cache_seconds: int = 600

    @classmethod
    def from_env(cls) -> "SupabaseAuthSettings":
        issuer = os.getenv("WSIS_SUPABASE_JWT_ISSUER", "").rstrip("/")
        audience = os.getenv("WSIS_SUPABASE_JWT_AUDIENCE", "authenticated")
        jwks_url = os.getenv("WSIS_SUPABASE_JWKS_URL", "")
        if not jwks_url and issuer:
            jwks_url = f"{issuer}/.well-known/jwks.json"
        if not issuer or not jwks_url:
            raise AuthConfigurationError(
                "WSIS_SUPABASE_JWT_ISSUER and WSIS_SUPABASE_JWKS_URL are required"
            )
        return cls(
            issuer=issuer,
            audience=audience,
            jwks_url=jwks_url,
            jwks_cache_seconds=int(os.getenv("WSIS_SUPABASE_JWKS_CACHE_SECONDS", "600")),
        )


class SupabaseTokenVerifier:
    """Verify Supabase JWTs and map trusted claims to a small domain principal."""

    def __init__(
        self,
        settings: SupabaseAuthSettings,
        *,
        decoder: ClaimsDecoder | None = None,
    ) -> None:
        self._settings = settings
        self._decoder = decoder or self._build_decoder(settings)

    @staticmethod
    def _build_decoder(settings: SupabaseAuthSettings) -> ClaimsDecoder:
        jwks = PyJWKClient(
            settings.jwks_url,
            cache_jwk_set=True,
            lifespan=settings.jwks_cache_seconds,
        )

        def decode(token: str) -> Mapping[str, Any]:
            signing_key = jwks.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256", "EdDSA"],
                audience=settings.audience,
                issuer=settings.issuer,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            )

        return decode

    def verify(self, token: str) -> AuthPrincipal:
        if not token or token.count(".") != 2:
            raise AuthTokenError("Malformed bearer token")
        try:
            claims = self._decoder(token)
        except jwt.PyJWTError as error:
            raise AuthTokenError("Invalid or expired bearer token") from error

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthTokenError("Bearer token is missing a subject")

        email = claims.get("email")
        app_metadata = claims.get("app_metadata")
        app_metadata = app_metadata if isinstance(app_metadata, Mapping) else {}
        return AuthPrincipal(
            subject=subject,
            email=email if isinstance(email, str) else None,
            email_verified=bool(
                claims.get("email_verified")
                or app_metadata.get("email_verified")
            ),
            assurance_level=claims.get("aal") if isinstance(claims.get("aal"), str) else None,
            role=claims.get("role") if isinstance(claims.get("role"), str) else None,
        )
