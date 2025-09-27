
# -*- coding: utf-8 -*-
"""
PD–SID prep aligned with user's implementation (Py3.7)

Inputs:
  --profiles  Path to Source_Profiles_named.xlsx (sheets = sites; must contain 'Species' column)

Outputs (to --outdir):
  - pd_sid_pairs.parquet    (Factor, Site1, Site2, Pearson_Correlation, Pearson_Distance, SID, n_species)
  - pd_sid_summary.parquet  (Factor, PD_mean, PD_ci, SID_mean, SID_ci, Site_count)

Definitions:
  Pearson_Distance (PD) = 1 - r^2, where r is the Pearson correlation of species contributions for a factor between two sites.
  SID = (sqrt(2)/n) * sum_i |x_i - y_i| / (x_i + y_i), over merged species with x_i + y_i > 0.

Notes:
  - Falls back to CSV if parquet engines are missing.
  - Tested with pandas 1.3.5 / Python 3.7.
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def _safe_to_parquet(df, path):
    path = Path(path)
    try:
        df.to_parquet(path, index=False)
        return str(path)
    except Exception:
        csv_path = path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        return str(csv_path)


def _read_profiles_excel(path):
    # Explicit engine optional; auto-detect works when openpyxl is installed.
    return pd.ExcelFile(path)


def _compute_pairs(profiles_xls: pd.ExcelFile) -> pd.DataFrame:
    # Read sheets -> long
    frames = []
    for site in profiles_xls.sheet_names:
        df = pd.read_excel(profiles_xls, sheet_name=site)
        if "Species" not in df.columns:
            candidates = [c for c in df.columns if str(c).strip().lower() == "species"]
            if candidates:
                df = df.rename(columns={candidates[0]: "Species"})
            else:
                raise ValueError("No 'Species' column in sheet %s" % site)
        df["Site"] = site
        frames.append(df)

    wide = pd.concat(frames, ignore_index=True)

    # Melt to long format
    factor_cols = [c for c in wide.columns if c not in ("Species", "Site")]
    long_ = wide.melt(id_vars=["Species", "Site"], var_name="Factor", value_name="Contribution")
    long_["Contribution"] = pd.to_numeric(long_["Contribution"], errors="coerce")

    results = []
    for factor in long_["Factor"].dropna().unique():
        sub = long_[long_["Factor"] == factor]
        sites = [s for s in sub["Site"].dropna().unique() if str(s).strip() != ""]
        for i, s1 in enumerate(sites):
            for s2 in sites[i+1:]:
                a = sub[sub["Site"] == s1][["Species","Contribution"]].rename(columns={"Contribution":"A"})
                b = sub[sub["Site"] == s2][["Species","Contribution"]].rename(columns={"Contribution":"B"})
                m = pd.merge(a, b, on="Species", how="inner").dropna(subset=["A","B"])
                if len(m) < 2:
                    continue

                r = m["A"].corr(m["B"])
                if pd.isna(r):
                    continue
                pd_metric = 1 - (r**2)  # Pearson Distance

                denom = m["A"].abs() + m["B"].abs()
                valid = denom > 0
                if valid.sum() == 0:
                    continue
                sid = (np.sqrt(2) / float(valid.sum())) * np.sum(np.abs(m.loc[valid, "A"] - m.loc[valid, "B"]) / denom.loc[valid])

                results.append({
                    "Factor": factor,
                    "Site1": s1,
                    "Site2": s2,
                    "Pearson_Correlation": float(r),
                    "Pearson_Distance": float(pd_metric),
                    "SID": float(sid),
                    "n_species": int(valid.sum())
                })

    return pd.DataFrame(results)


def _summarize(df_pairs: pd.DataFrame) -> pd.DataFrame:
    # 95% CI via 1.96 * SEM
    def _ci(x):
        x = pd.to_numeric(x, errors="coerce").dropna()
        if len(x) <= 1:
            return np.nan
        return 1.96 * (x.std(ddof=1) / np.sqrt(len(x)))

    # Count unique sites per factor
    sites_long = pd.concat([
        df_pairs[["Factor","Site1"]].rename(columns={"Site1":"Site"}),
        df_pairs[["Factor","Site2"]].rename(columns={"Site2":"Site"})
    ], ignore_index=True).drop_duplicates()
    site_count = sites_long.groupby("Factor")["Site"].nunique().reset_index(name="Site_count")

    g = df_pairs.groupby("Factor")
    out = pd.DataFrame({
        "PD_mean": g["Pearson_Distance"].mean(),
        "PD_ci": g["Pearson_Distance"].apply(_ci),
        "SID_mean": g["SID"].mean(),
        "SID_ci": g["SID"].apply(_ci),
    }).reset_index()

    out = out.merge(site_count, on="Factor", how="left")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True, help="Path to Source_Profiles_named.xlsx")
    ap.add_argument("--outdir", default=".", help="Output directory")
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    xls = _read_profiles_excel(args.profiles)
    pairs = _compute_pairs(xls)
    summary = _summarize(pairs)

    p1 = _safe_to_parquet(pairs, outdir / "pd_sid_pairs.parquet")
    p2 = _safe_to_parquet(summary, outdir / "pd_sid_summary.parquet")

    print("Wrote:"); print(p1); print(p2)


if __name__ == "__main__":
    main()
