from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from wsis.decision import DecisionInputs, DecisionRun
from wsis.auth import AuthConfigurationError, AuthTokenError, SupabaseAuthSettings, SupabaseTokenVerifier
from wsis.domain.models import CityDetail, CitySummary, ScoreWeights
from wsis.services.city_service import CityNotFoundError, CityService, get_city_service
from wsis.services.decision_service import (
    DecisionRequestError,
    DecisionService,
    get_decision_service,
)
from wsis.services.explore_service import ExploreCity, ExploreService, PublicJobListing, get_explore_service


def _score_weights(
    affordability: float = Query(0.40, ge=0),
    job_market: float = Query(0.25, ge=0),
    safety: float = Query(0.15, ge=0),
    climate: float = Query(0.10, ge=0),
    social_sentiment: float = Query(0.0, ge=0),
) -> ScoreWeights:
    return ScoreWeights(
        affordability=affordability,
        job_market=job_market,
        safety=safety,
        climate=climate,
        social_sentiment=social_sentiment,
    )


app = FastAPI(
    title="WSIS API",
    version="0.1.0",
    description="Local-first API scaffold for Where Should I Start.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "WSIS_FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_ROOT = Path(
    os.getenv("WSIS_PROJECT_ROOT", str(Path(__file__).resolve().parents[3]))
).resolve()
WEB_DIST = PROJECT_ROOT / "apps" / "web" / "dist"


@app.get("/api/auth/config")
def auth_config() -> dict[str, str | bool]:
    url = os.getenv("WSIS_SUPABASE_URL", "").rstrip("/")
    publishable_key = os.getenv("WSIS_SUPABASE_PUBLISHABLE_KEY", "")
    return {
        "enabled": bool(url and publishable_key),
        "supabase_url": url,
        "publishable_key": publishable_key,
    }


@app.get("/api/auth/me")
def authenticated_user(authorization: str | None = Header(None)) -> dict[str, str | bool | None]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        verifier = SupabaseTokenVerifier(SupabaseAuthSettings.from_env())
        principal = verifier.verify(authorization.removeprefix("Bearer ").strip())
    except AuthConfigurationError as error:
        raise HTTPException(status_code=503, detail="Authentication is not configured") from error
    except AuthTokenError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    return {
        "subject": principal.subject,
        "email": principal.email,
        "email_verified": principal.email_verified,
        "assurance_level": principal.assurance_level,
        "role": principal.role,
    }


@app.get("/api/status")
def read_root() -> dict[str, str]:
    return {"product": "WSIS", "status": "ok"}


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/v1/cities", response_model=list[CitySummary])
def list_cities(
    weights: ScoreWeights = Depends(_score_weights),
    city_service: CityService = Depends(get_city_service),
) -> list[CitySummary]:
    return city_service.list_cities(weights)


@app.get("/api/v1/explore", response_model=list[ExploreCity])
def explore_places(
    limit: int = Query(100, ge=1, le=750),
    q: str | None = Query(None, min_length=1, max_length=100),
    state: str | None = Query(None, min_length=2, max_length=2),
    role: str | None = Query(None, min_length=2, max_length=100),
    explore_service: ExploreService = Depends(get_explore_service),
) -> list[ExploreCity]:
    return explore_service.list_places(limit=limit, query=q, state_code=state, role=role)


@app.get("/api/v1/jobs", response_model=list[PublicJobListing])
def list_jobs(
    place_geoid: str = Query(..., pattern=r"^\d{7}$"),
    limit: int = Query(50, ge=1, le=100),
    explore_service: ExploreService = Depends(get_explore_service),
) -> list[PublicJobListing]:
    return explore_service.list_jobs(place_geoid=place_geoid, limit=limit)


@app.get("/api/v1/cities/{slug}", response_model=CityDetail)
def get_city(
    slug: str,
    weights: ScoreWeights = Depends(_score_weights),
    city_service: CityService = Depends(get_city_service),
) -> CityDetail:
    try:
        return city_service.get_city(slug, weights)
    except CityNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"City not found: {error}") from error


@app.get("/api/v1/compare", response_model=list[CityDetail])
def compare_cities(
    slugs: list[str] = Query(...),
    weights: ScoreWeights = Depends(_score_weights),
    city_service: CityService = Depends(get_city_service),
) -> list[CityDetail]:
    if len(slugs) < 2:
        raise HTTPException(status_code=422, detail="Provide at least two city slugs.")
    try:
        return city_service.compare_cities(slugs, weights)
    except CityNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"City not found: {error}") from error


@app.post("/api/v1/decisions", response_model=DecisionRun)
def run_decision(
    inputs: DecisionInputs,
    decision_service: DecisionService = Depends(get_decision_service),
) -> DecisionRun:
    try:
        return decision_service.run_decision(inputs)
    except DecisionRequestError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="web-assets")

    @app.get("/")
    def web_index() -> FileResponse:
        return FileResponse(WEB_DIST / "index.html")

    @app.get("/{path:path}")
    def web_fallback(path: str) -> FileResponse:
        return FileResponse(WEB_DIST / "index.html")
