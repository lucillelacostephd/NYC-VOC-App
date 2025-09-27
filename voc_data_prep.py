
"""
VOC NYC Data Prep — long-form frames for the Dash app.
Python 3.7 compatible.

Usage:
  python voc_data_prep.py --excel "Source_Contributions_named_with Bronx PAMS.xlsx" --outdir ./data

Outputs:
  - voc_daily.parquet             (Date, Site, Factor, Contribution)
  - voc_seasonal.parquet          (Seasonal means by Site × Factor)
  - voc_weekday_weekend.parquet   (Weekday/Weekend means by Site × Factor)

PD-SIC:
  A hook is provided via `compute_pd_sic()` but left unimplemented until we confirm the exact definition.
  You can later join the PD-SIC results to any of the frames as needed.

Assumptions:
  - Each worksheet corresponds to a site (e.g., Bronx, Queens, ...; including Bronx_PAMS as a site).
  - One date column exists (named 'Date' or sometimes 'Unnamed: 0').
  - All other columns are VOC factors / sources (wide). They are melted to long-form.
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True, help=r"C:\Users\LB945465\OneDrive - University at Albany - SUNY\Desktop Files\DN PMF Optimal")
    ap.add_argument("--outdir", default=".", help=r"C:\Users\LB945465\OneDrive - University at Albany - SUNY\Desktop Files\DN PMF Optimal\NYC VOC App")
    return ap.parse_args()


def coerce_date_column(df):
    # Standardize date column
    if "Date" in df.columns:
        date_col = "Date"
    elif "Unnamed: 0" in df.columns:
        date_col = "Unnamed: 0"
    else:
        # Fallback: try to detect a date-like column
        candidates = [c for c in df.columns if "date" in str(c).lower()]
        if candidates:
            date_col = candidates[0]
        else:
            raise ValueError("No recognizable Date column found.")
    df = df.rename(columns={date_col: "Date"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    return df


def season_from_month(m):
    # Winter, Spring, Summer, Fall (fixed order)
    if m in (12, 1, 2):
        return "Winter"
    elif m in (3, 4, 5):
        return "Spring"
    elif m in (6, 7, 8):
        return "Summer"
    else:
        return "Fall"  # 9,10,11


def weekday_or_weekend(d):
    return "Weekend" if d.weekday() >= 5 else "Weekday"


def compute_pd_sic(df_long):
    """
    Placeholder for PD-SIC computation.

    Parameters
    ----------
    df_long : DataFrame
        Columns required: Date, Site, Factor, Contribution (numeric).

    Returns
    -------
    DataFrame
        Example schema (to be finalized):
        Site, Factor, PD_SIC (float), optional breakdown fields

    Notes
    -----
    TODO: Implement once PD-SIC is formally defined for this study.
    """
    # For now, return an empty frame with the expected columns to avoid downstream breakage.
    cols = ["Site", "Factor", "PD_SIC"]
    return pd.DataFrame(columns=cols)


_SAFE_TO_PARQUET_PATCH = True

# --- PATCH: add safe_to_parquet helper (fallback to CSV) ---
def _safe_to_parquet(df, path):
    path = Path(path)
    try:
        df.to_parquet(path, index=False)
        return str(path)
    except Exception:
        # Fallback to CSV if parquet engine is missing
        csv_path = path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        return str(csv_path)

# Replace direct to_parquet calls with _safe_to_parquet


def main():
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Read all sheets
    xls = pd.ExcelFile(args.excel)
    frames = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(args.excel, sheet_name=sheet)
        df = coerce_date_column(df)

        # Melt wide factor columns to long
        factor_cols = [c for c in df.columns if c != "Date"]
        if not factor_cols:
            continue

        # Keep only numeric contribution columns
        # Non-numeric columns (if any) are dropped
        df_numeric = df[["Date"] + factor_cols].copy()
        for c in factor_cols:
            df_numeric[c] = pd.to_numeric(df_numeric[c], errors="coerce")

        df_long = df_numeric.melt(id_vars="Date", var_name="Factor", value_name="Contribution")
        df_long["Site"] = sheet  # sheet name as site
        frames.append(df_long)

    if not frames:
        raise RuntimeError("No valid data found in the workbook.")

    all_long = pd.concat(frames, ignore_index=True)
    all_long = all_long.dropna(subset=["Contribution"])

    # Sort for consistency
    all_long = all_long.sort_values(["Site", "Factor", "Date"]).reset_index(drop=True)

    # Basic time features
    all_long["Month"] = all_long["Date"].dt.month
    all_long["Season"] = all_long["Month"].apply(season_from_month)
    all_long["DoW"] = all_long["Date"].apply(weekday_or_weekend)

    # Save full daily
    _safe_to_parquet(all_long[["Date", "Site", "Factor", "Contribution"]], outdir / "voc_daily.parquet")

    # Seasonal means
    seasonal = (all_long
                .groupby(["Site", "Factor", "Season"], as_index=False)["Contribution"]
                .mean()
                .rename(columns={"Contribution": "Contribution_mean"}))
    _safe_to_parquet(seasonal, outdir / "voc_seasonal.parquet")

    # Weekday vs Weekend means
    wdwe = (all_long
            .groupby(["Site", "Factor", "DoW"], as_index=False)["Contribution"]
            .mean()
            .rename(columns={"Contribution": "Contribution_mean"}))
    _safe_to_parquet(wdwe, outdir / "voc_weekday_weekend.parquet")

    # PD-SIC hook (placeholder)
    # pd_sic = compute_pd_sic(all_long)
    # pd_sic.to_parquet(outdir / "voc_pd_sic.parquet", index=False)

    print("Wrote:",
          outdir / "voc_daily.parquet",
          outdir / "voc_seasonal.parquet",
          outdir / "voc_weekday_weekend.parquet",
          sep="\n")


if __name__ == "__main__":
    main()

