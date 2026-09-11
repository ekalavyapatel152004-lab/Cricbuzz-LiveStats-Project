import os
import requests
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"

BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"


def get_headers():
    """Create headers required by RapidAPI."""

    if not RAPIDAPI_KEY:
        raise ValueError(
            "RAPIDAPI_KEY not found. Check your .env file."
        )

    return {
        "Content-Type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }


def get_recent_matches():
    """Fetch recent cricket matches."""

    url = f"{BASE_URL}/matches/v1/recent"

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30
    )

    response.raise_for_status()

    return response.json()
def get_scorecard(match_id):
    """
    Fetch the scorecard for a specific match.
    """

    url = f"{BASE_URL}/mcenter/v1/{match_id}/scard"

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30
    )

    response.raise_for_status()

    return response.json()