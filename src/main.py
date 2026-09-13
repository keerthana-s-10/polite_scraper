import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, field_validator

BASE_URL = "https://books.toscrape.com/"
CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")
BOOKS_FILE = OUTPUT_DIR / "books.json"
ERRORS_FILE = OUTPUT_DIR / "errors.json"

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/keerthana-s-10/polite_scraper)"


class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https(cls, value):
        if not value.startswith("https://"):
            raise ValueError("URL must start with https://")
        return value


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
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as error:
        print(f"REQUEST FAILED: {url}")
        print(f"REASON: {error}")
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

        if html is None:
            continue

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

    print(f"catalogue_pages=3")
    print(f"discovered={len(all_books)}")
    print(f"unique_urls={len(seen_urls)}")

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

    price_text = price.get_text(strip=True) if price else ""

    return {
        "title": title.get_text(strip=True) if title else "",
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": (
            availability.get_text(" ", strip=True)
            if availability
            else ""
        ),
        "rating_text": rating_text,
        "description": (
            description.get_text(" ", strip=True)
            if description
            else None
        ),
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def normalize_record(record):
    price_text = record["price_text"]

    price_text = (
        price_text
        .replace("Ã‚Â£", "")
        .replace("Â£", "")
        .replace("£", "")
        .strip()
    )

    price_gbp = float(price_text)

    return {
        **record,
        "price_gbp": price_gbp
    }

def scrape_books(book_urls):
    records = []

    for index, (product_url, source_page) in enumerate(book_urls, start=1):
        print(f"[{index}/{len(book_urls)}] {product_url}")

        response = None

        for attempt in range(2):
            try:
                response = requests.get(
                    product_url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=30
                )

                if response.status_code == 200:
                    break

                if response.status_code >= 500 and attempt == 0:
                    print(f"SERVER ERROR {response.status_code}, retrying...")
                    time.sleep(1)
                    continue

                print(f"FAILED: {response.status_code}: {product_url}")
                response = None
                break

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError
            ) as error:
                if attempt == 0:
                    print("REQUEST FAILED, retrying...")
                    time.sleep(1)
                else:
                    print(f"REQUEST FAILED: {product_url}")
                    print(f"REASON: {error}")

        if response is None:
            continue

        record = extract_book(
            response.text,
            product_url,
            source_page
        )

        records.append(record)

        if index < len(book_urls):
            time.sleep(0.5)

    return records


def validate_and_store(records):
    valid_records = []
    errors = []

    for record in records:
        try:
            normalized = normalize_record(record)
            book = Book(**normalized)
            valid_records.append(book.model_dump())

        except (ValueError, ValidationError) as error:
            errors.append({
                "record": record,
                "reason": str(error)
            })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    BOOKS_FILE.write_text(
        json.dumps(valid_records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    ERRORS_FILE.write_text(
        json.dumps(errors, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(errors)}")


if __name__ == "__main__":
    book_urls = discover_books()
    records = scrape_books(book_urls)

    print()
    print(f"detail_pages={len(records)}")

    if records:
        print()
        print("First raw record:")
        print(records[0])

    validate_and_store(records)