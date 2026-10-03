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
    query = " ".join(query.split())

    # OpenAlex search jangan dikasih seluruh isi chunk
    query_words = query.split()

    # Buang karakter aneh dan ambil query pendek
    query_words = [
        word.strip(".,;:!?()[]{}\"'")
        for word in query_words
        if len(word.strip(".,;:!?()[]{}\"'")) > 2
    ]

    query = " ".join(query_words[:8])

    params = {
        "search": query,
        "per-page": per_page,
    }

    if OPENALEX_API_KEY:
        params["api_key"] = OPENALEX_API_KEY

    response = requests.get(
        OPENALEX_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("results", []):
        results.append({
            "source_id": item.get("id"),
            "title": item.get("display_name"),
            "year": item.get("publication_year"),
            "doi": item.get("doi"),
            "url": item.get("primary_location", {}).get("landing_page_url"),
            "text": reconstruct_abstract(
                item.get("abstract_inverted_index")
            )
        })

    return results