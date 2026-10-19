# Data mining

This repository contains analysis code for scraped product listings.

## Daily listing analysis

[`price_changes_product_analysis.py`](./price_changes_product_analysis.py) and [`price changes.ipynb`](./price%20changes.ipynb) contain daily listing counts and median prices by category, matched-listing analyses comparing earliest and latest observed prices and consecutive collection days, a chart of matched-listing coverage and price-change direction, and a keyword-based analysis of common Furniture and Fashion product types in listing titles. The product-type counts are keyword matches, not brand or seller dominance; titles can match multiple groups.

The analyses expect the cleaned `clean` dataframe, category list `CATS`, category palette `PAL`, source listing dataframe `df` with listing IDs and scrape timestamps, and the `numpy` (`np`), `pandas` (`pd`), and `matplotlib.pyplot` (`plt`) imports from the calling workflow. The median-price chart also expects a `KSH` currency-axis formatter.

The input dataset and upstream cleaning workflow are not included in this repository.
