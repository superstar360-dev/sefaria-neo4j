import requests
from config import *

INDEX_URL = "https://www.sefaria.org/api/index"
LINKS_URL = "https://www.sefaria.org/api/links/{}"
TEXT_URL = "https://www.sefaria.org/api/v3/texts/{}?version=hebrew&version=translation"

def fetch_json(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def get_all_refs():
    """
    Extracts all book-level 'title' strings from the nested
    /api/index response structure.
    """
    data = fetch_json(INDEX_URL)
    titles = []

    # The top-level response is a list of category objects
    for category in data:
        for subcat in category.get("contents", []):
            for book in subcat.get("contents", []):
                title = book.get("title")
                if title:
                    titles.append(title)

    return titles

def fetch_links(ref):
    return fetch_json(LINKS_URL.format(ref))

def fetch_text(ref):
    return fetch_json(TEXT_URL.format(ref))
