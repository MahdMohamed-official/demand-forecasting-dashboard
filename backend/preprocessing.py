"""Load, assess, clean and feature-engineer the demand forecasting dataset.

The raw file has 16 columns per store/product/day: identifiers (Date,
Store ID, Product ID, Category, Region), stock figures (Inventory Level,
Units Sold, Units Ordered), pricing (Price, Discount, Competitor Pricing),
external conditions (Weather Condition, Seasonality, Promotion, Epidemic)
and the target column, Demand.

`preprocess_data()` is the single entry point app.py calls. It returns one
cleaned, feature-engineered DataFrame -- but it also runs a quality check
on the data *before* cleaning it, and attaches that report to
`df.attrs["quality_report"]` so analytics.py can surface what was actually
wrong with the source file without re-deriving it.
"""

import numpy as np
import pandas as pd

NUMERIC_COLUMNS = [
    "inventory_level",
    "units_sold",
    "units_ordered",
    "price",
    "discount",
    "competitor_pricing",
    "demand",
]

CATEGORICAL_FILL_COLUMNS = ["category", "region", "weather_condition", "seasonality"]


def load_raw_data(path):
    """Read the CSV and standardise column names to lower_snake_case.

    The column names are the only thing normalised here -- values are left
    exactly as they appear in the file so `assess_quality` sees the data
    the way it actually arrived.
    """
    df = pd.read_csv(path)
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    )
    return df


def assess_quality(df):
    """Profile the RAW (not-yet-cleaned) data and return a plain dict.

    Mirrors a standard data-quality checklist: missing values, duplicate
    records (both a full-row check and a date+store+product "business key"
    check), and a handful of business-rule violations that would make a
    row untrustworthy even if every cell is technically filled in.
    """
    numeric = df.copy()
    for column in NUMERIC_COLUMNS:
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")

    missing_counts = df.isnull().sum()
    missing_values = {
        column: int(count) for column, count in missing_counts.items() if count > 0
    }

    invalid_records = {
        "price_not_positive": int((numeric["price"] <= 0).sum()),
        "negative_inventory": int((numeric["inventory_level"] < 0).sum()),
        "negative_units_sold": int((numeric["units_sold"] < 0).sum()),
        "discount_out_of_range": int((~numeric["discount"].between(0, 100)).sum()),
        "demand_not_positive": int((numeric["demand"] <= 0).sum()),
        "sold_more_than_stock": int(
            (numeric["units_sold"] > numeric["inventory_level"]).sum()
        ),
    }

    dates = pd.to_datetime(df["date"], errors="coerce")

    return {
        "rows_in_file": int(len(df)),
        "columns_in_file": int(df.shape[1]),
        "missing_values": missing_values,
        "total_missing_cells": int(missing_counts.sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_business_key": int(
            df.duplicated(subset=["date", "store_id", "product_id"]).sum()
        ),
        "invalid_records": invalid_records,
        "date_range": {
            "start": str(dates.min().date()),
            "end": str(dates.max().date()),
            "unique_dates": int(dates.nunique()),
        },
    }


def clean_data(df):
    """Drop duplicates and fill missing values.

    Numeric columns are filled with the column median (robust to the
    outliers a demand series naturally has); the small set of categorical
    columns that had gaps are filled with the column mode. Both choices
    only matter for a small minority of rows -- see the quality report for
    exactly how many.
    """
    clean = df.drop_duplicates().copy()

    for column in NUMERIC_COLUMNS:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
        if clean[column].isnull().any():
            clean[column] = clean[column].fillna(clean[column].median())

    for column in CATEGORICAL_FILL_COLUMNS:
        if clean[column].isnull().any():
            clean[column] = clean[column].fillna(clean[column].mode()[0])

    clean["date"] = pd.to_datetime(clean["date"])
    clean = clean.sort_values(["date", "store_id", "product_id"]).reset_index(
        drop=True
    )
    return clean


def engineer_features(df):
    """Add the derived business columns the analytics module relies on."""
    out = df.copy()

    # Pricing and revenue
    out["effective_price"] = (out["price"] * (1 - out["discount"] / 100)).round(2)
    out["gross_revenue"] = (out["units_sold"] * out["price"]).round(2)
    out["revenue"] = (out["units_sold"] * out["effective_price"]).round(2)
    out["discount_value"] = (out["gross_revenue"] - out["revenue"]).round(2)

    out["price_gap"] = (out["price"] - out["competitor_pricing"]).round(2)
    out["price_position"] = np.where(
        out["price_gap"] > 0,
        "Costlier than competitor",
        np.where(out["price_gap"] < 0, "Cheaper than competitor", "Same price"),
    )

    # Demand fulfilment and inventory
    out["unmet_demand"] = (out["demand"] - out["units_sold"]).clip(lower=0)
    out["fulfilment_rate"] = (out["units_sold"] / out["demand"] * 100).round(2)
    out["stock_out_risk"] = (out["demand"] > out["inventory_level"]).astype(int)
    out["inventory_coverage"] = (out["inventory_level"] / out["demand"]).round(2)
    out["sell_through_rate"] = (
        out["units_sold"] / out["inventory_level"].replace(0, np.nan) * 100
    ).round(2)

    # Date parts
    out["year"] = out["date"].dt.year
    out["month"] = out["date"].dt.month
    out["month_name"] = out["date"].dt.month_name().str[:3]
    out["month_start"] = out["date"].dt.to_period("M").dt.to_timestamp()
    out["quarter"] = "Q" + out["date"].dt.quarter.astype(str)
    out["day_name"] = out["date"].dt.day_name().str[:3]
    out["is_weekend"] = (out["date"].dt.dayofweek >= 5).astype(int)

    # Bands used for grouping in the dashboard
    out["demand_level"] = pd.qcut(
        out["demand"], q=4, labels=["Low", "Medium", "High", "Very High"]
    )
    out["discount_band"] = pd.cut(
        out["discount"],
        bins=[-1, 0, 9, 19, 100],
        labels=["No Discount", "Low (1-9%)", "Medium (10-19%)", "High (20%+)"],
    )

    return out


def preprocess_data(path):
    """Load -> assess -> clean -> engineer. Returns one analysis-ready DataFrame.

    The pre-cleaning quality report is attached to `df.attrs["quality_report"]`
    so `analytics.compute_quality()` can report on it without re-reading the
    raw file.
    """
    raw = load_raw_data(path)
    quality_report = assess_quality(raw)

    clean = clean_data(raw)
    quality_report["rows_after_cleaning"] = int(len(clean))
    quality_report["duplicates_removed"] = int(len(raw) - len(clean))
    quality_report["missing_values_imputed"] = quality_report["total_missing_cells"]

    ready = engineer_features(clean)
    ready.attrs["quality_report"] = quality_report
    return ready