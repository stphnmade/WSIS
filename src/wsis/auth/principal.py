from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthPrincipal:
    subject: str
    email: str | None
    email_verified: bool
    assurance_level: str | None
    role: str | None
