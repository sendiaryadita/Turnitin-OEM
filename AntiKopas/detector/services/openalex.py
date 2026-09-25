import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENALEX_URL = "https://api.openalex.org/works"
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY")

def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""

    words = []

    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort()

    return " ".join(
        word for position, word in words
    )


def search_literature(query, per_page=20):

    params = {
        "search": query,
        "per_page": per_page,
        "api_key": OPENALEX_API_KEY,
    }

    response = requests.get(
        OPENALEX_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for work in data.get("results", []):

        abstract = reconstruct_abstract(
            work.get("abstract_inverted_index")
        )

        results.append({
            "source_id": work.get("id"),
            "title": work.get("display_name"),
            "year": work.get("publication_year"),
            "doi": work.get("doi"),
            "url": work.get("primary_location", {}).get(
                "landing_page_url"
            ),
            "text": abstract,
        })

    return results