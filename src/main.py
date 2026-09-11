import time
from pathlib import Path

import requests

URL = "https://books.toscrape.com/"
CACHE_FILE = Path("cache/catalogue-page-1.html")
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/YOUR_USERNAME/YOUR_REPO)"

def fetch_page():
    if CACHE_FILE.exists():
        content = CACHE_FILE.read_text(encoding="utf-8")
        print(f"CACHE HIT: {CACHE_FILE}")
        print(f"response_size={len(content)}")
        return content

    headers = {"User-Agent": USER_AGENT}

    print(f"FETCH: {URL}")

    response = requests.get(
        URL,
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        raise RuntimeError(f"Unexpected status code: {response.status_code}")

    content = response.text

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(content, encoding="utf-8")

    print(f"response_size={len(content)}")
    print(f"cached={CACHE_FILE}")

    time.sleep(0.5)

    return content


if __name__ == "__main__":
    fetch_page()