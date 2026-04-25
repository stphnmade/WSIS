from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from wsis.decision import DecisionInputs, DecisionRun
from wsis.domain.models import CityDetail, CitySummary, ScoreWeights
from wsis.services.city_service import CityNotFoundError, CityService, get_city_service
from wsis.services.decision_service import (
    DecisionRequestError,
    DecisionService,
    get_decision_service,
)


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
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
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
