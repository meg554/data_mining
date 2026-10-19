# Data mining

This repository contains analysis code for scraped product listings.

## Daily listing collection chart

[`price_changes_product_analysis.py`](./price_changes_product_analysis.py) creates a stacked chart of listing observations collected per day and category. It expects the cleaned `clean` dataframe, category list `CATS`, category palette `PAL`, and the `numpy` (`np`) and `matplotlib.pyplot` (`plt`) imports to be defined by the calling analysis workflow.

The supplied script contains this collection-volume visualization only; it does not calculate product price changes. The input dataset and upstream cleaning workflow are not included in this repository yet.
