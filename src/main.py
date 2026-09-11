from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
CACHE_DIR = Path("cache")
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/keerthana-s-10/polite_scraper)"


def get_page(url, cache_file):
    if cache_file.exists():
        print(f"CACHE HIT: {cache_file}")
        return cache_file.read_text(encoding="utf-8")

    print(f"FETCH: {url}")

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=10
    )

    if response.status_code != 200:
        raise RuntimeError(f"Unexpected status code: {response.status_code}")

    content = response.text
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(content, encoding="utf-8")

    return content


def discover_books():
    all_urls = set()
    current_url = BASE_URL

    for page_number in range(1, 4):
        cache_file = CACHE_DIR / f"catalogue-page-{page_number}.html"
        html = get_page(current_url, cache_file)

        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")

            if link and link.get("href"):
                absolute_url = urljoin(current_url, link["href"])
                all_urls.add(absolute_url)

        next_link = soup.select_one("li.next a")

        if page_number < 3 and next_link:
            current_url = urljoin(current_url, next_link["href"])

    print(f"catalogue_pages=3")
    print(f"discovered={len(all_urls)}")
    print(f"unique_urls={len(all_urls)}")


if __name__ == "__main__":
    discover_books()