"""
Route scoring engine.

Score (0–100) considers: number of stops, tourist potential of stopovers,
visa complexity, approximate duration, and season fit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.routes import Airport, Route


@dataclass
class ScoreBreakdown:
    total: float
    stop_penalty: float
    tourist_bonus: float
    visa_bonus: float
    duration_penalty: float
    season_bonus: float
    label: str  # "Excelente" | "Muy buena" | "Buena" | "Regular"

    def as_dict(self) -> dict:
        return {
            "Total": round(self.total, 1),
            "Penalización escalas": round(self.stop_penalty, 1),
            "Bonus turístico": round(self.tourist_bonus, 1),
            "Bonus visa fácil": round(self.visa_bonus, 1),
            "Penalización duración": round(self.duration_penalty, 1),
            "Bonus temporada": round(self.season_bonus, 1),
        }


_TOURIST_POTENTIAL_SCORES = {"high": 15, "medium": 8, "low": 0}
_VISA_COMPLEXITY_SCORES = {"low": 10, "medium": 5, "high": 0}


def score_route(
    route: "Route",
    airports: dict[str, "Airport"],
    departure_month: int = 1,
) -> ScoreBreakdown:
    """
    Compute a 0–100 score for a route.

    Parameters
    ----------
    route:            The route to score.
    airports:         Full airport lookup dict.
    departure_month:  Month of departure (1–12) for season bonus.
    """
    base = 100.0

    # Penalizar por número de escalas (máx -25)
    stop_penalty = min(route.total_stops * 8, 25)

    # Bonus por potencial turístico de las escalas
    tourist_stopover_count = sum(
        1 for code in route.stopovers
        if airports.get(code) and airports[code].is_tourist_stopover
    )
    tourist_bonus = min(tourist_stopover_count * 8, 15)
    tourist_bonus += _TOURIST_POTENTIAL_SCORES.get(route.tourist_potential, 0)

    # Bonus por simplicidad de visa
    visa_bonus = _VISA_COMPLEXITY_SCORES.get(route.visa_complexity, 0)

    # Penalizar por duración excesiva (más de 30h suma penalización)
    extra_hours = max(route.approximate_duration_hours - 30, 0)
    duration_penalty = min(extra_hours * 0.5, 10)

    # Bonus de temporada
    best_months = route.season_recommendations.get("best_months", [])
    season_bonus = 5.0 if departure_month in best_months else 0.0

    total = base - stop_penalty + tourist_bonus + visa_bonus - duration_penalty + season_bonus
    total = max(0.0, min(100.0, total))

    label = _score_label(total)
    return ScoreBreakdown(
        total=total,
        stop_penalty=-stop_penalty,
        tourist_bonus=tourist_bonus,
        visa_bonus=visa_bonus,
        duration_penalty=-duration_penalty,
        season_bonus=season_bonus,
        label=label,
    )


def _score_label(score: float) -> str:
    if score >= 85:
        return "Excelente"
    if score >= 75:
        return "Muy buena"
    if score >= 60:
        return "Buena"
    return "Regular"


def rank_routes(
    routes: list["Route"],
    airports: dict[str, "Airport"],
    departure_month: int = 1,
) -> list[tuple["Route", ScoreBreakdown]]:
    """Return routes sorted by computed score (descending)."""
    scored = [(r, score_route(r, airports, departure_month)) for r in routes]
    return sorted(scored, key=lambda x: x[1].total, reverse=True)
