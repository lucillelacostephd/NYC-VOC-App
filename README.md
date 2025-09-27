# NYC-VOC-App

## Project title : NYC VOC Source Apportionment (2000–2021): DN-PMF Trends, PD–SID Similarity, and Risk Metrics

### Summary

This project hosts analysis-ready datasets and helper scripts for an interactive app that communicates long-term VOC source dynamics across six NYC-metro sites. We combine dispersion-normalized PMF (DN-PMF), seasonal/weekday structure, and cross-site similarity (PD–SID) to clarify which sources declined, which persisted (evaporative, natural gas, biogenic), and how profiles compare across locations. Bronx includes both 24-h canister and PAMS (hourly) results; other sites are canister only.

### Methods (brief)

DN-PMF on 24-h canister VOCs (six sites) + Bronx PAMS hourly VOCs.
Seasonality/weekday summaries computed from daily long-form contributions.
PD–SID similarity: for each factor, pair sites​

### Files provided

voc_daily.parquet — Long-form daily source contributions; cols: Date, Site, Factor, Contribution.
voc_seasonal.parquet — Seasonal means by Site×Factor×Season.
voc_weekday_weekend.parquet — Weekday/Weekend means by Site×Factor×DoW.
pd_sid_pairs.parquet — Pairwise site comparisons per factor; cols: Factor, Site1, Site2, Pearson_Correlation, Pearson_Distance, SID, n_species.
pd_sid_summary.parquet — Per-factor PD_mean, PD_ci, SID_mean, SID_ci, Site_count.

### Notes

Sites: Queens, Bronx, Kings, Richmond, Elizabeth, Chester; Bronx_PAMS denotes Bronx hourly PAMS analysis.
Ordering: seasons fixed (Winter, Spring, Summer, Fall); weekday first in any WD/WE split.
Units: Contribution in the same units as PMF outputs (fraction or concentration-equivalent as documented in the manuscript).
CSV fallbacks exist for Parquet-limited environments.

### Intended use

Supports a public Streamlit app (NYC VOC Explorer) for trends, factor exploration, PD–SID similarity, and (optionally) health-risk visualizations with 95% CIs.

### Citation
If you use these data, please cite the associated manuscript(s) and this OSF project.
Borlaza-Lacoste, L. et al. NYC VOC Source Apportionment (2000–2021): DN-PMF Trends and PD–SID Similarity. OSF, 2025. DOI/URL: DOI 10.17605/OSF.IO/QJC8N.

Borlaza-Lacoste L, Aynul Bari M, Lu CH, Hopke PK. Long-term contributions of VOC sources and their link to ozone pollution in Bronx, New York City. Environ Int. 2024 Sep;191:108993. doi: 10.1016/j.envint.2024.108993. Epub 2024 Sep 3. PMID: 39278045.
