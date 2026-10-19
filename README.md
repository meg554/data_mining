# Marketplace Listing Price Analysis

This branch contains an exploratory analysis of listings collected over seven days, 13-19 October 2026. The notebook compares Mobile Phones, Furniture, and Fashion listings, with prices in Kenyan shillings (KSh).

## Contents

- [another.ipynb](another.ipynb): coverage and scraper-log review, observation and unique-listing counts, price summaries, outlier inspection, and price-distribution charts.

## Findings

- The analysis reports 3,600 observations across 2,778 unique listings. A listing observed on multiple days contributes multiple observations, so use unique listings for product counts and observations for day-by-day analysis.
- The overall median price is KSh 12,000, compared with a mean of KSh 29,030. Prices are strongly right-skewed, making the median a more representative measure of a typical listing.
- Reported category medians are KSh 35,000 for Mobile Phones, KSh 9,999 for Furniture, and KSh 1,700 for Fashion.
- Collection coverage is incomplete on 14 October (Furniture and Fashion) and 18 October (Fashion). The notebook attributes these gaps to scraper DNS errors. Missing category-days are treated as missing data, not as zero-priced listings.
- The notebook flags a Fashion listing priced at KSh 400,350 as a possible seller-entry or wholesale-price anomaly. It is retained in the analysis rather than silently removed.

## Running the Notebook

The notebook contains analysis and reporting cells, but this branch does not include the raw listing data or the data-loading and preparation code. It therefore is not self-contained. Before running the analysis cells, provide the prepared data and initialize the variables they use, including `df`, `clean`, `CATS`, `PAL`, `KSH`, `LOG_PATH`, and the required imports.

The analysis uses Python with pandas, NumPy, Matplotlib, Seaborn, and SciPy. Install these packages in the notebook's selected Python environment if they are not already available.

## Interpretation Notes

- The seven-day sample is geographically concentrated: the notebook reports that 95.4% of observations are in Nairobi County.
- High-price outliers are inspected by category. Some appear plausible for premium products or large furniture; the notebook does not remove them automatically.
- Summary figures describe the collected sample and should not be treated as estimates for all listings or the wider market.

