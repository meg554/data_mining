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
