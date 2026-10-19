
# Jiji Kenya Web Scraper

A polite, ethics-conscious web scraper that collects second-hand marketplace listings from [Jiji Kenya](https://jiji.co.ke) for three categories: **Mobile Phones**, **Furniture**, and **Fashion**. The scraper respects `robots.txt`, rate-limits its requests, and saves data to both CSV and JSON formats.

---

## Table of Contents

- [Purpose](#purpose)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Output Files](#output-files)
- [How It Works](#how-it-works)
- [Data Fields](#data-fields)
- [Ethical and Legal Notes](#ethical-and-legal-notes)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)

---

## Purpose

This project was built for the **DSC2107 course project** to demonstrate responsible web scraping. It collects structured data about publicly listed items from Jiji Kenya so that it can be analysed for trends in pricing, condition, and location across categories.

---

## Features

- **Robots.txt compliance** — the scraper checks `robots.txt` before making any category requests and stops if access is disallowed.
- **Polite rate limiting** — enforces a 3-second delay between every HTTP request.
- **Domain restriction** — refuses to follow links outside `jiji.co.ke` and enforces HTTPS.
- **Graceful stop on blocking** — if the site returns HTTP 403 or 429, the scraper stops immediately rather than retrying or attempting to bypass restrictions.
- **Multi-level extraction** — extracts fields from listing cards first, then visits the detail page only when a field is missing.
- **Deduplication** — uses a canonicalised advert URL as the unique key so the same advert is never recorded twice.
- **Incremental saving** — writes the raw CSV after each advert and after each category, so no data is lost if the run is interrupted.
- **JSON backup** — produces a JSON copy of the final dataset alongside the CSV.
- **Logging** — writes a log file with timestamps, warnings, and errors.
- **Robust field parsing** — handles multiple HTML layouts, labelled values, and numeric price normalisation.

---

## Requirements

- **Python 3.8+**
- The following Python packages:

| Package | Purpose |
| `requests` | HTTP requests to Jiji |
| `beautifulsoup4` | HTML parsing |
| `pandas` | Tabular output and CSV writing |

> `csv`, `json`, `re`, `time`, `logging`, `datetime`, and `urllib` are part of the Python standard library and do not need to be installed.

---

## Installation

1. **Clone or download** this project into a local folder.

2. **(Recommended) Create a virtual environment:**

   ```bash
   python -m venv venv
   ```

   Activate it:

   - **Windows:** `venv\Scripts\activate`
   - **macOS / Linux:** `source venv/bin/activate`

3. **Install dependencies:**

   ```bash
   pip install requests beautifulsoup4 pandas
   ```

4. **Save the script** as `jiji_scraper.py` (or run it as a Jupyter notebook, as the original comments suggest).

---

## Usage

Run the scraper from the terminal:

```bash
python jiji_scraper.py
```

The script will:

1. Check `robots.txt` for each category URL.
2. Scrape each category up to the configured page and advert limits.
3. Save the results to `jiji_raw.csv` and `jiji_raw.json`.
4. Log all activity to `jiji_scraper.log`.
5. Print progress messages to the console.

---

## Configuration

All settings live in the **Configuration** section at the top of the script. Edit them to adjust behaviour:

| Variable | Default | Description |
| `CATEGORY_URLS` | 3 categories | Dictionary of category names → starting URLs. Add or remove categories here. |
| `MAX_PAGES_PER_CATEGORY` | `10` | Maximum number of listing pages to scrape per category. |
| `MAX_ADS_PER_CATEGORY` | `200` | Maximum number of unique adverts to collect per category. |
| `REQUEST_DELAY` | `3` | Seconds to wait between requests (assignment requires 2–5 s). |
| `USER_AGENT` | DSC2107 string | Identifies the scraper and provides contact info. **Change the email to your own.** |
| `BASE_DOMAIN` | `jiji.co.ke` | Domain the scraper is allowed to visit. |
| `FIELDS` | 9 fields | Column order for the output files. |
| `OUTPUT_RAW` | `jiji_raw.csv` | Raw output CSV path. |
| `OUTPUT_JSON` | `jiji_raw.json` | JSON backup path. |
| `OUTPUT_LOG` | `jiji_scraper.log` | Log file path. |

### Suggested workflow

Start with **small limits** to verify the scraper works:

```python
MAX_PAGES_PER_CATEGORY = 1
MAX_ADS_PER_CATEGORY = 5
```

Once you've confirmed the output looks correct, increase them to the full assignment values.

---

## Output Files

| File | Format | Contents |
| `jiji_raw.csv` | CSV (UTF-8 with BOM) | The main dataset, one row per advert. |
| `jiji_raw.json` | JSON | A pretty-printed JSON backup of the same records. |
| `jiji_scraper.log` | Plain text | Timestamped log of warnings and errors. |

> `OUTPUT_CLEAN` (`jiji_cleaned.csv`) is defined but not written by this script — it is reserved for a separate cleaning stage.

---

## How It Works

The scraper runs in **eight logical stages**:

1. **Configuration** — categories, limits, delays, and file paths are declared.
2. **Logging and HTTP session** — a single `requests.Session` with identifying headers is created; a timestamp tracks the last request for rate limiting.
3. **Robots check** — `robots.txt` is fetched and parsed; the scraper aborts if any category URL is disallowed.
4. **Extraction helpers** — small utilities (`first_text`, `first_attribute`, `canonical_url`, `normalise_price`, etc.) that try multiple CSS selectors in order.
5. **Finding advert cards** — the scraper tries several known card selectors and extracts canonical advert URLs.
6. **Field extraction** — title, price, condition, location, and posting date are extracted from the card. If any are missing, the advert's detail page is fetched as a fallback.
7. **Scraping one category** — pages through the listing, deduplicates adverts, and saves incrementally.
8. **Running all categories** — iterates each category in a `try/except/finally` block so partial data is always preserved.

---

## Data Fields

Each row in the output contains the following columns:

| Field | Description |
| `advert_id` | Canonical advert URL (used as a stable unique key). |
| `category` | One of the configured category names. |
| `title` | The advert's title. |
| `price` | Numeric price (float) derived from the displayed price, or empty. |
| `condition` | Item condition (e.g. "Brand New", "Used"). |
| `location` | Region or location shown in the advert. |
| `posting_date` | Date or datetime the advert was posted, if available. |
| `advert_url` | Full public URL of the advert. |
| `scraped_at` | ISO 8601 timestamp (UTC) of when the record was collected. |

---

## Ethical and Legal Notes

This scraper was designed with responsible use in mind:

- **Always check the site's Terms of Service** before scraping. Public availability of data does not automatically mean it is permitted to be collected.
- **Respect `robots.txt`** — the script does so automatically.
- **Do not remove or reduce the request delay** below the assignment minimum of 2 seconds.
- **Do not attempt to bypass** HTTP 403 or 429 responses. If the site blocks you, stop and review the rules.
- **Only collect publicly visible fields.** Do not attempt to access private data, log in, or scrape contact details.
- **Use the data for academic purposes only** and do not redistribute it.
- **Provide accurate contact information** in the `USER_AGENT` so site administrators can reach you if needed.

---

## Troubleshooting

| Problem | Possible Cause | Solution |
| `HTTP 403` or `HTTP 429` | Site is rate-limiting or blocking the scraper | Stop the run, wait some time, and review the site's rules. Do not retry repeatedly. |
| `No cards found` | HTML layout has changed, or the page structure is different | Open the page in a browser, inspect the HTML, and update `CARD_SELECTORS`. |
| Most fields are empty | Selectors no longer match | Update the selector lists (`TITLE_SELECTORS`, `PRICE_SELECTORS`, etc.) using the browser's DevTools. |
| `ModuleNotFoundError` | Missing dependency | Run `pip install requests beautifulsoup4 pandas`. |
| Output CSV is empty | All adverts failed to fetch, or `robots.txt` blocked access | Check `jiji_scraper.log` for errors. |
| Script hangs | Slow network or site response | `timeout=25` in `fetch_page` should prevent indefinite hangs; if not, check your connection. |

---

## Limitations

- **Selector fragility** — the CSS selectors are based on Jiji's current HTML layout and will break if the site changes its markup.
- **No JavaScript rendering** — the scraper uses `requests` and BeautifulSoup, so it cannot see content loaded dynamically by JavaScript. If Jiji moves to client-side rendering, the scraper will need Selenium or Playwright.
- **Single-threaded** — requests are strictly sequential to preserve politeness. This is intentional.
- **Partial data is possible** — some fields (especially `condition` and `posting_date`) may be empty if the advert page does not display them in a recognisable format.
- **No cleaning stage in this script** — `OUTPUT_CLEAN` is declared but not generated; cleaning (e.g. standardising prices or dates) is left for a separate step.

---

## License and Attribution

This script was written for the **DSC2107 course project**. Use of the data collected is subject to Jiji Kenya's Terms of Service and the academic integrity policies of the course. Please cite the data source appropriately in any report that uses it.

