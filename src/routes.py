"""
Route loading, filtering and query logic.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd


DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class Airport:
    iata_code: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    is_tourist_stopover: bool
    visa_notes: str
    hub_airlines: list[str] = field(default_factory=list)

    @classmethod
    def from_series(cls, row: pd.Series) -> "Airport":
        airlines = [a.strip() for a in str(row.get("hub_airlines", "")).split(",") if a.strip()]
        return cls(
            iata_code=str(row["iata_code"]),
            name=str(row["name"]),
            city=str(row["city"]),
            country=str(row["country"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            is_tourist_stopover=str(row["is_tourist_stopover"]).lower() == "true",
            visa_notes=str(row["visa_notes"]),
            hub_airlines=airlines,
        )


@dataclass
class Route:
    id: str
    name: str
    origin: str
    destination: str
    stopovers: list[str]
    total_stops: int
    approximate_duration_hours: int
    tourist_potential: str  # "low" | "medium" | "high"
    season_recommendations: dict
    airlines_example: list[str]
    visa_complexity: str  # "low" | "medium" | "high"
    visa_notes: str
    score: int
    highlights: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "Route":
        return cls(
            id=data["id"],
            name=data["name"],
            origin=data["origin"],
            destination=data["destination"],
            stopovers=data.get("stopovers", []),
            total_stops=data.get("total_stops", len(data.get("stopovers", []))),
            approximate_duration_hours=data.get("approximate_duration_hours", 0),
            tourist_potential=data.get("tourist_potential", "medium"),
            season_recommendations=data.get("season_recommendations", {}),
            airlines_example=data.get("airlines_example", []),
            visa_complexity=data.get("visa_complexity", "medium"),
            visa_notes=data.get("visa_notes", ""),
            score=data.get("score", 0),
            highlights=data.get("highlights", []),
        )

    @property
    def all_airports(self) -> list[str]:
        return [self.origin] + self.stopovers + [self.destination]


def load_airports(csv_path: Optional[Path] = None) -> dict[str, Airport]:
    """Load airport data from CSV and return a dict keyed by IATA code."""
    path = csv_path or DATA_DIR / "airports.csv"
    df = pd.read_csv(path)
    return {row["iata_code"]: Airport.from_series(row) for _, row in df.iterrows()}


def load_routes(json_path: Optional[Path] = None) -> list[Route]:
    """Load sample routes from JSON."""
    path = json_path or DATA_DIR / "sample_routes.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Route.from_dict(r) for r in data["routes"]]


def filter_routes(
    routes: list[Route],
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    max_stops: Optional[int] = None,
    visa_complexity: Optional[list[str]] = None,
    tourist_potential: Optional[list[str]] = None,
) -> list[Route]:
    """Return routes matching the given filters."""
    result = routes

    if origin:
        result = [r for r in result if r.origin == origin or origin in r.all_airports[:-1]]
    if destination:
        result = [r for r in result if r.destination == destination]
    if max_stops is not None:
        result = [r for r in result if r.total_stops <= max_stops]
    if visa_complexity:
        result = [r for r in result if r.visa_complexity in visa_complexity]
    if tourist_potential:
        result = [r for r in result if r.tourist_potential in tourist_potential]

    return result


def get_routes_dataframe(routes: list[Route]) -> pd.DataFrame:
    """Convert a list of Route objects to a pandas DataFrame for analysis."""
    records = []
    for r in routes:
        records.append(
            {
                "id": r.id,
                "name": r.name,
                "origin": r.origin,
                "destination": r.destination,
                "stopovers": " → ".join(r.stopovers),
                "total_stops": r.total_stops,
                "duration_hours": r.approximate_duration_hours,
                "tourist_potential": r.tourist_potential,
                "visa_complexity": r.visa_complexity,
                "score": r.score,
                "airlines": ", ".join(r.airlines_example),
            }
        )
    return pd.DataFrame(records)


def get_season_recommendation(route: Route, month: int) -> str:
    """Return a text recommendation for the given route and departure month."""
    best = route.season_recommendations.get("best_months", [])
    notes = route.season_recommendations.get("notes", "")
    if month in best:
        return f"✅ Mes {month} es recomendado para esta ruta. {notes}"
    return f"⚠️ Mes {month} no es el óptimo para esta ruta. {notes}"
