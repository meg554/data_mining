
import csv
import json
import re
import time
import logging
from datetime import datetime, timezone
from urllib.parse import (
    urljoin, urlparse, parse_qs, urlencode, urlunparse
)
from urllib.robotparser import RobotFileParser

import requests
import pandas as pd
from bs4 import BeautifulSoup


# ============================================================
# 1. CONFIGURATION
# ============================================================

CATEGORY_URLS = {
    "Mobile Phones": "https://jiji.co.ke/mobile-phones",
    "Furniture": "https://jiji.co.ke/furniture",
    "Fashion": "https://jiji.co.ke/clothing",
}

OUTPUT_RAW = "jiji_raw.csv"
OUTPUT_CLEAN = "jiji_cleaned.csv"
OUTPUT_JSON = "jiji_raw.json"
OUTPUT_LOG = "jiji_scraper.log"

# Start with a small test. Increase after verifying the output.
MAX_PAGES_PER_CATEGORY = 10
MAX_ADS_PER_CATEGORY = 200

# Assignment requires 2–5 seconds between requests.
REQUEST_DELAY = 3

USER_AGENT = (
    "DSC2107-Course-Project "
    "(student research; gracetalwana13@gmail.com)"
)

BASE_DOMAIN = "jiji.co.ke"

FIELDS = [
    "advert_id",
    "category",
    "title",
    "price",
    "condition",
    "location",
    "posting_date",
    "advert_url",
    "scraped_at",
]


# ============================================================
# 2. LOGGING AND HTTP SESSION
# ============================================================

logging.basicConfig(
    filename=OUTPUT_LOG,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-KE,en;q=0.9",
})

last_request_time = 0


class StopScraping(Exception):
    """Raised when the site blocks access or rules prohibit a URL."""
    pass


def fetch_page(url):
    """Fetch one public page politely, with a delay between requests."""
    global last_request_time

    parsed = urlparse(url)

    if parsed.scheme != "https" or parsed.hostname != BASE_DOMAIN:
        raise StopScraping(f"Unexpected URL; stopping: {url}")

    elapsed = time.monotonic() - last_request_time
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)

    response = session.get(url, timeout=25)
    last_request_time = time.monotonic()

    if response.status_code in (403, 429):
        logging.error("Access blocked: HTTP %s at %s  jiji_scraper.ipynb:101 - jiji_scraper.py:101",
                      response.status_code, url)
        raise StopScraping(
            f"HTTP {response.status_code}. Stop and review access rules."
        )

    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


# ============================================================
# 3. CHECK ROBOTS.TXT
# ============================================================

def check_robots():
    robots_url = "https://jiji.co.ke/robots.txt"

    response = session.get(robots_url, timeout=20)

    if response.status_code in (403, 429):
        raise StopScraping(
            "Could not safely check robots.txt; access was blocked."
        )

    response.raise_for_status()

    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(response.text.splitlines())

    for category, url in CATEGORY_URLS.items():
        if not parser.can_fetch(USER_AGENT, url):
            raise StopScraping(
                f"robots.txt disallows the starting URL for {category}: {url}"
            )

    print("robots.txt permits the category starting URLs.  jiji_scraper.ipynb:137 - jiji_scraper.py:137")
    print("Continue only if the site's other rules also permit this use.  jiji_scraper.ipynb:138 - jiji_scraper.py:138")


# ============================================================
# 4. GENERAL EXTRACTION HELPERS
# ============================================================

def text_from(element):
    if not element:
        return ""

    return element.get_text(" ", strip=True)


def first_text(soup, selectors):
    """Return text from the first selector that matches."""
    for selector in selectors:
        element = soup.select_one(selector)
        value = text_from(element)

        if value:
            return value

    return ""


def first_attribute(soup, selectors, attribute):
    for selector in selectors:
        element = soup.select_one(selector)

        if element:
            value = element.get(attribute, "")
            if value:
                return str(value).strip()

    return ""


def canonical_url(url):
    """Remove fragments and tracking query parameters."""
    parsed = urlparse(url)
    return urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        "",
        "",
        "",
    ))


def advert_identifier(url):
    # Use the canonical public advert URL as a stable key.
    # Do not use location as the identifier.
    return canonical_url(url)


def normalise_price(price_text):
    """Keep the displayed price and derive a numeric value if possible."""
    if not price_text:
        return None

    value = re.sub(r"[^\d.]", "", price_text.replace(",", ""))

    try:
        return float(value) if value else None
    except ValueError:
        return None


def find_next_page_url(current_url):
    """
    Use the page query pattern observed during reconnaissance.
    The caller stops when a page has no new advertisements.
    """
    parsed = urlparse(current_url)
    params = parse_qs(parsed.query)

    current_page = int(params.get("page", ["1"])[0])
    params["page"] = [str(current_page + 1)]

    query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=query))


# ============================================================
# 5. FIND ADVERTISEMENT CARDS AND THEIR URLS
# ============================================================

CARD_SELECTORS = [
    "a.qa-advert-list-item",
    "a.b-list-advert__item-wrapper",
    ".b-list-advert__item-wrapper a",
]


def find_ad_cards(soup):
    for selector in CARD_SELECTORS:
        cards = soup.select(selector)

        if cards:
            # Return cards from the first selector that matches.
            return cards, selector

    return [], None


def extract_advert_url(card, page_url):
    href = card.get("href", "")

    if not href:
        link = card.select_one("a[href]")
        if link:
            href = link.get("href", "")

    if not href:
        return ""

    full_url = urljoin(page_url, href)
    parsed = urlparse(full_url)

    if parsed.scheme != "https" or parsed.hostname != BASE_DOMAIN:
        return ""

    return canonical_url(full_url)


# ============================================================
# 6. EXTRACT THE REQUIRED FIELDS FROM AN ADVERTISEMENT
# ============================================================

TITLE_SELECTORS = [
    "div.b-advert-title-inner",
    ".qa-advert-title",
    "h1",
    "h2",
    "[itemprop='name']",
]

PRICE_SELECTORS = [
    ".qa-advert-price",
    ".b-advert__price",
    ".b-list-advert__price",
    "[itemprop='price']",
]

LOCATION_SELECTORS = [
    "span.b-list-advert__region__text",
    ".b-list-advert__region__text",
    ".b-list-advert__region",
]

CONDITION_SELECTORS = [
    "[itemprop='itemCondition']",
    ".b-advert-info-statistics__value",
    ".b-advert-attributes__value",
    ".b-advert-attribute__value",
]

DATE_SELECTORS = [
    "time[datetime]",
    "time",
    "[itemprop='datePosted']",
    ".b-advert-info-statistics__date",
    ".b-advert__date",
]


def find_labeled_value(soup, labels):
    """
    Find values displayed beside labels such as Condition or Posted.
    This is a fallback, not a guarantee that every page uses these labels.
    """
    wanted = {label.casefold() for label in labels}

    for row in soup.select(
        "li, tr, .b-advert-info-statistics__item, "
        ".b-advert-attributes__item, .b-advert-attribute"
    ):
        label_element = row.select_one(
            "th, dt, .b-advert-info-statistics__title, "
            ".b-advert-attributes__key, .b-advert-attribute__key"
        )

        if label_element:
            label = text_from(label_element).rstrip(":").casefold()

            if label in wanted:
                value_element = row.select_one(
                    "td, dd, .b-advert-info-statistics__value, "
                    ".b-advert-attributes__value, "
                    ".b-advert-attribute__value"
                )

                value = text_from(value_element)

                if value:
                    return value

        # Generic fallback for text like "Condition: Brand New".
        row_text = text_from(row)

        for label in labels:
            match = re.search(
                rf"\b{re.escape(label)}\s*:\s*(.+)",
                row_text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

    return ""


def extract_condition(soup):
    value = first_text(soup, CONDITION_SELECTORS)

    if not value:
        value = find_labeled_value(
            soup, ["Condition", "Item condition"]
        )

    if value.casefold() in {
        "condition", "attributes", "specifications", "details"
    }:
        return ""

    return value


def extract_posting_date(soup):
    value = first_attribute(
        soup, ["time[datetime]", "[itemprop='datePosted']"], "datetime"
    )

    if not value:
        value = first_attribute(
            soup, ["[itemprop='datePosted']"], "content"
        )

    if not value:
        value = first_text(soup, DATE_SELECTORS)

    if not value:
        value = find_labeled_value(
            soup, ["Date posted", "Posted", "Published", "Date"]
        )

    return value


def extract_product_fields(soup, category, advert_url):
    title = first_text(soup, TITLE_SELECTORS)

    price_text = first_text(soup, PRICE_SELECTORS)

    if not price_text:
        price_text = first_attribute(
            soup, ["[itemprop='price']"], "content"
        )

    location = first_text(soup, LOCATION_SELECTORS)

    if not location:
        location = find_labeled_value(
            soup, ["Location", "Region"]
        )

    condition = extract_condition(soup)
    posting_date = extract_posting_date(soup)

    return {
        "advert_id": advert_identifier(advert_url),
        "category": category,
        "title": title,
        "price": normalise_price(price_text),
        "condition": condition,
        "location": location,
        "posting_date": posting_date,
        "advert_url": advert_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# 7. SCRAPE ONE CATEGORY
# ============================================================

def scrape_category(category, start_url):
    records_by_url = {}
    url = start_url
    visited_pages = set()

    for page_number in range(1, MAX_PAGES_PER_CATEGORY + 1):
        if url in visited_pages:
            print(f"Pagination repeated a URL; stopping {category}.  jiji_scraper.ipynb:434 - jiji_scraper.py:434")
            break

        visited_pages.add(url)

        print(f"\n{category} | page {page_number} | {url}  jiji_scraper.ipynb:439 - jiji_scraper.py:439")

        soup = fetch_page(url)
        cards, used_selector = find_ad_cards(soup)

        print("Card selector:  jiji_scraper.ipynb:444 - jiji_scraper.py:444", used_selector)
        print("Cards found:  jiji_scraper.ipynb:445 - jiji_scraper.py:445", len(cards))

        if not cards:
            logging.warning(
                "No cards found for %s at %s", category, url
            )
            print("No cards found. Check the current page HTML.  jiji_scraper.ipynb:451 - jiji_scraper.py:451")
            break

        new_count = 0

        for card in cards:
            advert_url = extract_advert_url(card, url)

            if not advert_url or advert_url in records_by_url:
                continue

            record = extract_product_fields(
                card, category, advert_url
            )

            # If key fields are missing, inspect the public detail page.
            # Only request detail pages where a field is still missing.
            if (
                not record["title"]
                or record["price"] is None
                or not record["condition"]
                or not record["posting_date"]
                or not record["location"]
            ):
                try:
                    detail_soup = fetch_page(advert_url)
                    detail_record = extract_product_fields(
                        detail_soup, category, advert_url
                    )

                    for field in (
                        "title", "price", "condition",
                        "location", "posting_date"
                    ):
                        if (
                            record[field] is None
                            or record[field] == ""
                        ):
                            record[field] = detail_record[field]

                except requests.RequestException as error:
                    logging.warning(
                        "Detail page failed: %s | %s",
                        advert_url, error
                    )
                # StopScraping is deliberately not caught here.

            records_by_url[advert_url] = record
            new_count += 1

            # Keep an incremental raw backup in case a later page fails.
            pd.DataFrame(
                records_by_url.values(), columns=FIELDS
            ).to_csv(OUTPUT_RAW, index=False, encoding="utf-8-sig")

            if len(records_by_url) >= MAX_ADS_PER_CATEGORY:
                break

        print("New advertisements collected:  jiji_scraper.ipynb:509 - jiji_scraper.py:509", new_count)
        print("Unique advertisements so far:  jiji_scraper.ipynb:510 - jiji_scraper.py:510", len(records_by_url))

        if new_count == 0:
            print("No new advertisements on this page; stopping.  jiji_scraper.ipynb:513 - jiji_scraper.py:513")
            break

        if len(records_by_url) >= MAX_ADS_PER_CATEGORY:
            print("Category limit reached.  jiji_scraper.ipynb:517 - jiji_scraper.py:517")
            break

        url = find_next_page_url(url)

    return list(records_by_url.values())


# ============================================================
# 8. RUN ALL CATEGORIES AND SAVE RAW DATA
# ============================================================

all_records = []

try:
    check_robots()

    for category, start_url in CATEGORY_URLS.items():
        print(f"\nStarting category: {category}  jiji_scraper.ipynb:535 - jiji_scraper.py:535")

        try:
            category_records = scrape_category(category, start_url)
            all_records.extend(category_records)

            # Save after every category to reduce risk of data loss.
            pd.DataFrame(
                all_records, columns=FIELDS
            ).to_csv(
                OUTPUT_RAW, index=False, encoding="utf-8-sig"
            )

        except StopScraping:
            raise

        except requests.RequestException as error:
            logging.error(
                "Request error in %s: %s", category, error
            )
            print("Category stopped due to a request error:  jiji_scraper.ipynb:555 - jiji_scraper.py:555", error)

except StopScraping as error:
    print("\nSCRAPING STOPPED:  jiji_scraper.ipynb:558 - jiji_scraper.py:558", error)
    print("Do not retry repeatedly or attempt to bypass the restriction.  jiji_scraper.ipynb:559 - jiji_scraper.py:559")

finally:
    # Always preserve whatever records have already been collected.
    raw_df = pd.DataFrame(all_records, columns=FIELDS)

    if not raw_df.empty:
        raw_df.to_csv(
            OUTPUT_RAW, index=False, encoding="utf-8-sig"
        )

        with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
            json.dump(
                all_records, file, ensure_ascii=False, indent=2
            )

    print("\nScraping run ended.  jiji_scraper.ipynb:575 - jiji_scraper.py:575")
    print("Records collected:  jiji_scraper.ipynb:576 - jiji_scraper.py:576", len(all_records))
    print("Raw CSV:  jiji_scraper.ipynb:577 - jiji_scraper.py:577", OUTPUT_RAW)
    print("JSON backup:  jiji_scraper.ipynb:578 - jiji_scraper.py:578", OUTPUT_JSON)
    print("Log file:  jiji_scraper.ipynb:579 - jiji_scraper.py:579", OUTPUT_LOG)
