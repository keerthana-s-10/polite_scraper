from datetime import datetime, timezone
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
        return cache_file.read_text(encoding="utf-8"), True

    print(f"FETCH: {url}")

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=20
        )
    except requests.exceptions.Timeout:
        print(f"TIMEOUT: {url}")
        return None, False

    if response.status_code != 200:
        raise RuntimeError(f"Unexpected status code: {response.status_code}")

    content = response.text

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(content, encoding="utf-8")

    return content, False


def discover_books():
    all_books = []
    seen_urls = set()
    current_url = BASE_URL

    for page_number in range(1, 4):
        cache_file = CACHE_DIR / f"catalogue-page-{page_number}.html"
        html, _ = get_page(current_url, cache_file)

        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")

            if link and link.get("href"):
                product_url = urljoin(current_url, link["href"])

                if product_url not in seen_urls:
                    seen_urls.add(product_url)
                    all_books.append((product_url, current_url))

        next_link = soup.select_one("li.next a")

        if page_number < 3 and next_link:
            current_url = urljoin(current_url, next_link["href"])

    return all_books


def extract_book(html, product_url, source_page):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("div.product_main h1")

    price = soup.select_one("p.price_color")

    availability = soup.select_one("p.instock.availability")

    rating = soup.select_one("p.star-rating")

    description = soup.select_one("#product_description + p")

    rating_text = None
    if rating:
        classes = rating.get("class", [])
        rating_text = next(
            (value for value in classes if value != "star-rating"),
            None
        )

    return {
        "title": title.get_text(strip=True) if title else None,
        "product_url": product_url,
        "price_text": price.get_text(strip=True) if price else None,
        "availability_text": availability.get_text(" ", strip=True) if availability else None,
        "rating_text": rating_text,
        "description": description.get_text(" ", strip=True) if description else None,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def scrape_books(book_urls):
    records = []

    for index, (product_url, source_page) in enumerate(book_urls, start=1):
        print(f"[{index}/{len(book_urls)}] {product_url}")

        try:
            response = requests.get(
                product_url,
                headers={"User-Agent": USER_AGENT},
                timeout=20
            )
        except requests.exceptions.Timeout:
            print(f"TIMEOUT: {product_url}")
            continue

        if response.status_code != 200:
            raise RuntimeError(
                f"Unexpected status code {response.status_code}: {product_url}"
            )

        record = extract_book(
            response.text,
            product_url,
            source_page
        )

        records.append(record)

        if index < len(book_urls):
            import time
            time.sleep(0.5)

    return records

if __name__ == "__main__":
    book_urls = discover_books()
    records = scrape_books(book_urls)

    print()
    print("detail_pages=" + str(len(records)))
    print()
    print("First raw record:")
    print(records[0])