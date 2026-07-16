"""
Static reference data for FIFA World Cup 2026 host stadiums.
In a production system this would come from a live venue-management
database; here it's an in-memory dataset for the prototype.
"""

STADIUMS = {
    "metlife": {
        "name": "MetLife Stadium",
        "city": "East Rutherford, NJ, USA",
        "gates": {
            "Gate A": "Low crowd",
            "Gate B": "Moderate crowd",
            "Gate C": "High crowd",
            "Gate D": "Low crowd",
        },
    },
    "azteca": {
        "name": "Estadio Azteca",
        "city": "Mexico City, Mexico",
        "gates": {
            "Gate 1": "Moderate crowd",
            "Gate 2": "Low crowd",
            "Gate 3": "High crowd",
            "Gate 4": "Moderate crowd",
        },
    },
    "bc_place": {
        "name": "BC Place",
        "city": "Vancouver, Canada",
        "gates": {
            "Gate N": "Low crowd",
            "Gate S": "Moderate crowd",
            "Gate E": "Low crowd",
            "Gate W": "High crowd",
        },
    },
    "att_stadium": {
        "name": "AT&T Stadium",
        "city": "Arlington, TX, USA",
        "gates": {
            "Gate A": "High crowd",
            "Gate B": "Moderate crowd",
            "Gate C": "Low crowd",
            "Gate D": "Moderate crowd",
        },
    },
    "sofi": {
        "name": "SoFi Stadium",
        "city": "Inglewood, CA, USA",
        "gates": {
            "Gate 1": "Low crowd",
            "Gate 2": "Low crowd",
            "Gate 3": "Moderate crowd",
            "Gate 4": "High crowd",
        },
    },
}

DEFAULT_STADIUM_ID = "metlife"


def get_stadium(stadium_id: str) -> dict | None:
    """Return stadium data by id, or None if not found."""
    return STADIUMS.get(stadium_id)


def get_all_stadiums_summary() -> list[dict]:
    """Return a lightweight list of stadiums for populating a selector."""
    return [
        {"id": sid, "name": data["name"], "city": data["city"]}
        for sid, data in STADIUMS.items()
    ]