"""Authentication primitives independent from API routes."""

from wsis.auth.principal import AuthPrincipal
from wsis.auth.verifier import (
    AuthConfigurationError,
    AuthTokenError,
    SupabaseAuthSettings,
    SupabaseTokenVerifier,
)

__all__ = [
    "AuthConfigurationError",
    "AuthPrincipal",
    "AuthTokenError",
    "SupabaseAuthSettings",
    "SupabaseTokenVerifier",
]
