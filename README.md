# Data mining

This repository contains analysis code for scraped product listings.

## Daily listing analysis

[`price_changes_product_analysis.py`](./price_changes_product_analysis.py) and [`price changes.ipynb`](./price%20changes.ipynb) contain two daily analyses: a stacked chart of listing observations by category, and a chart of median listing prices by category with day-to-day percentage changes and summary ranges.

Both expect the cleaned `clean` dataframe, category list `CATS`, category palette `PAL`, and the `numpy` (`np`) and `matplotlib.pyplot` (`plt`) imports from the calling workflow. The median-price analysis also expects `pandas` as `pd` and a `KSH` currency-axis formatter.

The input dataset and upstream cleaning workflow are not included in this repository.
