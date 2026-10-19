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
