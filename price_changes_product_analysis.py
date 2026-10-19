# Chart C1: observations collected each day, by category
daily = clean.groupby(["collection_date", "category"]).size().unstack(fill_value=0).reindex(columns=CATS)
daily.index = daily.index.strftime("%a %d %b")
fig, ax = plt.subplots(figsize=(10, 5))
bottom = np.zeros(len(daily))
for c in CATS:
    ax.bar(daily.index, daily[c], bottom=bottom, color=PAL[c], label=c, width=.65)
    for i, v in enumerate(daily[c]):
        if v: ax.text(i, bottom[i] + v / 2, f"{v}", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    bottom += daily[c].values
for i, t in enumerate(bottom): ax.text(i, t + 8, f"{int(t)}", ha="center", fontweight="bold")
ax.grid(axis="x", visible=False)
for i, d in enumerate(daily.index):
    missing_c = [c for c in CATS if daily.loc[d, c] == 0]
    if missing_c: ax.text(i, bottom[i] + 45, "not collected:\n" + "\n".join(missing_c), ha="center", fontsize=7.5, color="firebrick")
ax.set_ylim(0, 760); ax.set_xlabel("Collection date (file date, 2026)"); ax.set_ylabel("Number of observations collected")
ax.set_title("C1. Listings collected per day, stacked by category"); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.12))
plt.tight_layout(); plt.show()

# Chart C2: daily MEDIAN price per category; gaps = no data (never zero)
med = clean.groupby(["collection_date", "category"])["price_num"].median().unstack().reindex(columns=CATS)
cnt = clean.groupby(["collection_date", "category"]).size().unstack().reindex(columns=CATS)
fig, ax = plt.subplots(figsize=(11, 5.6))
for c in CATS:
    ax.plot(med.index, med[c], marker="o", lw=2, color=PAL[c], label=c)
    for d, m, n in zip(med.index, med[c], cnt[c]):
        if pd.notna(m):
            ax.annotate(f"{m:,.0f}\n(n={int(n)})", (d, m), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=7.5, color=PAL[c])
    for d in med.index[med[c].isna()]:
        ax.plot(d, 1000, marker="x", color=PAL[c], ms=10, mew=2, ls="none")
        ax.annotate("not collected", (d, 1000), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=7, color=PAL[c])
ax.set_yscale("log"); ax.yaxis.set_major_formatter(KSH); ax.set_ylim(700, 90000)
ax.set_xticks(med.index); ax.set_xticklabels(med.index.strftime("%d %b"))
ax.set_xlabel("Collection date (2026)"); ax.set_ylabel("Median listing price (KSh, log scale)")
ax.set_title("C2. Daily median price by category (x = category not collected that day)"); ax.legend(frameon=False, loc="center right")
plt.tight_layout(); plt.show()
tbl = med.copy(); tbl.index = tbl.index.strftime("%Y-%m-%d"); display(tbl)
chg = (med.pct_change(fill_method=None) * 100).round(1); chg.index = chg.index.strftime("%Y-%m-%d")
print("Day-to-day % change in the median (blank-to-blank steps are NaN when a category is missing):"); display(chg)
print("Range of daily medians per category (min, max, max/min):")
print(pd.DataFrame({"min": med.min(), "max": med.max(), "max/min": med.max() / med.min()}).loc[CATS].to_string())

# Matched-listing analysis: earliest vs latest observed price
obs_sorted = df.sort_values(["listing_key", "collection_date", "scraped_dt"])
g = obs_sorted.groupby("listing_key")
matched = pd.DataFrame({
    "title": g["title"].last(),
    "category": g["category"].last(),
    "n_days": g["collection_date"].nunique(),
    "first_date": g["collection_date"].min(),
    "last_date": g["collection_date"].max(),
    "first_price": g["price_num"].first(),
    "last_price": g["price_num"].last(),
    "titles_seen": g["title"].nunique(),
})
n_all = len(matched)
matched = matched[
    (matched["n_days"] >= 2)
    & matched["first_price"].notna()
    & matched["last_price"].notna()
].copy()
matched["span_days"] = (matched["last_date"] - matched["first_date"]).dt.days
matched["abs_change"] = matched["last_price"] - matched["first_price"]
matched["pct_chg"] = np.where(
    matched["first_price"] > 0,
    100 * matched["abs_change"] / matched["first_price"],
    np.nan,
)
matched["direction"] = np.select(
    [matched["abs_change"] > 0, matched["abs_change"] < 0],
    ["Increase", "Decrease"],
    "No change",
)
matched_pct = 100 * len(matched) / n_all if n_all else np.nan
print(f"Unique listings: {n_all:,} | observed on >= 2 days with prices (matched): {len(matched):,} ({matched_pct:.1f}%)")
print("Matched listings by number of days seen:", matched["n_days"].value_counts().sort_index().to_dict())
print(f"Matched listings whose title text differs between days (ad was edited): {int((matched['titles_seen'] > 1).sum())}")
print("\nDirection of change (latest vs earliest observed price):")
print(matched["direction"].value_counts().to_string())
changed = matched[matched["direction"] != "No change"]
changed_share = 100 * len(changed) / len(matched) if len(matched) else np.nan
print(f"\nShare of matched listings whose price changed: {changed_share:.1f}%")
print(f"Among changed: median % change {changed['pct_chg'].median():+.1f}% | median absolute change {changed['abs_change'].median():+,.0f} KSh")
by_cat = matched.groupby("category").agg(
    matched=("title", "size"),
    changed=("direction", lambda s: int((s != "No change").sum())),
    increases=("direction", lambda s: int((s == "Increase").sum())),
    decreases=("direction", lambda s: int((s == "Decrease").sum())),
    median_pct_chgd=("pct_chg", lambda s: s[s != 0].median()),
    median_abs_changed=("abs_change", lambda s: s[s != 0].median()),
).reindex(CATS)
by_cat["share_changed_%"] = 100 * by_cat["changed"] / by_cat["matched"]
display(by_cat)

# Day-to-day matched comparison: the same listing on consecutive collected days
rows = []
days = sorted(df["collection_date"].dropna().unique())
piv = df.pivot_table(
    index="listing_key",
    columns="collection_date",
    values="price_num",
    aggfunc="last",
)
for a, b in zip(days[:-1], days[1:]):
    both = piv[[a, b]].dropna()
    ch = both[b].div(both[a]).sub(1).where(both[a] != 0)
    rows.append({
        "from": pd.Timestamp(a).date(),
        "to": pd.Timestamp(b).date(),
        "matched_listings": len(both),
        "price_changed": int((both[b] != both[a]).sum()),
        "median_%_change_all_matched": 100 * ch.median(),
        "median_%_change_changed_only": 100 * ch[ch.notna() & (both[b] != both[a])].median(),
    })
pairs = pd.DataFrame(rows)
display(pairs)

# Chart C3: how many listings could be compared, and how many changed price?
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
cc = (
    matched.groupby(["category", "direction"])
    .size()
    .unstack(fill_value=0)
    .reindex(CATS)
    .reindex(columns=["Decrease", "No change", "Increase"], fill_value=0)
)
cc.plot(
    kind="bar",
    stacked=True,
    ax=axes[0],
    color=["#D55E00", "#BBBBBB", "#0072B2"],
    width=.65,
)
for i, row in enumerate(cc.values):
    run = 0
    for value in row:
        if value:
            axes[0].text(i, run + value / 2, str(value), ha="center", va="center", fontsize=9)
        run += value
axes[0].grid(axis="x", visible=False)
axes[1].grid(axis="x", visible=False)
axes[0].set_xticklabels(CATS, rotation=0)
axes[0].set_xlabel("Category")
axes[0].set_ylabel("Matched listings (seen on >= 2 days)")
axes[0].set_title("Direction of observed price change")
axes[0].legend(title="", frameon=False)
labels = [f"{start:%d %b}\u2192{end:%d %b}" for start, end in zip(pairs["from"], pairs["to"])]
bars = axes[1].bar(labels, pairs["matched_listings"], color="#999999", width=.6)
for bar, changed_count in zip(bars, pairs["price_changed"]):
    axes[1].text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 3,
        f"{int(changed_count)} changed",
        ha="center",
        fontsize=9,
    )
axes[1].set_xlabel("Pair of consecutive collection days (2026)")
axes[1].set_ylabel("Listings present on both days")
axes[1].set_title("Matched listings between consecutive collection days")
plt.setp(axes[1].get_xticklabels(), rotation=25, ha="right")
fig.suptitle("C3. Matched-listing price changes: coverage and direction", fontsize=12, y=1.03)
plt.tight_layout()
plt.show()

# Chart D2: common product types in Furniture and Fashion listing titles
FURN_TYPES = {
    "Chair": r"chair|seat(?!er)",
    "Table": r"table",
    "Desk": r"desk",
    "Sofa / couch": r"sofa|couch|seater|recliner",
    "Bed / mattress": r"\bbed|mattress",
    "Cabinet / shelf / wardrobe": r"cabinet|shelf|shelves|wardrobe|rack|drawer",
    "Stool / bench": r"stool|bench",
    "Fittings / accessories": r"handle|hinge|leg|accessor",
}
FASH_TYPES = {
    "T-shirt / polo / shirt": r"t-?shirt|polo|shirt|tee\b|jersey",
    "Jacket / coat / hoodie": r"jacket|coat|hoodie|sweater|vest",
    "Uniform / overall": r"uniform|overall|apron|coverall|suit",
    "Dress / skirt": r"dress|skirt|gown",
    "Trousers / shorts": r"trouser|jean|short|pant|tracksuit",
    "Shoes": r"shoe|sneaker|boot|sandal|loafer",
    "Cap / hat / scarf": r"\bcap|hat|scarf|beanie",
}


def type_share(cat, types):
    listings = df[df["category"] == cat].drop_duplicates("listing_key")
    titles = listings["title"].fillna("").astype(str)
    counts = {
        label: int(titles.str.contains(pattern, case=False, regex=True, na=False).sum())
        for label, pattern in types.items()
    }
    covered = titles.str.contains(
        "|".join(types.values()), case=False, regex=True, na=False
    ).mean() * 100 if len(titles) else 0
    return pd.Series(counts).sort_values(), len(listings), covered


fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
for ax, (category, types) in zip(
    axes, [("Furniture", FURN_TYPES), ("Fashion", FASH_TYPES)]
):
    shares, listing_count, coverage = type_share(category, types)
    ax.barh(shares.index, shares.values, color=PAL[category])
    for i, value in enumerate(shares.values):
        percent = 100 * value / listing_count if listing_count else 0
        ax.text(value + 1, i, f"{value} ({percent:.0f}%)", va="center", fontsize=8.5)
    ax.set_xlim(0, max(shares.max() * 1.25, 1))
    ax.set_xlabel("Unique listings whose title contains the product-type word")
    ax.set_ylabel("Product type (keyword group)")
    ax.set_title(
        f"{category}: {listing_count:,} unique listings\n"
        f"(keywords cover {coverage:.0f}% of titles; a title can match several groups)",
        fontsize=11,
    )
fig.suptitle(
    "D2. Alternative analysis - common product types in titles "
    "(NOT brand or seller dominance)",
    fontsize=12,
    y=1.04,
)
plt.tight_layout()
plt.show()
