"""Turn the cleaned, feature-engineered DataFrame into dashboard data.

`analyze_data(df)` is the single entry point app.py calls. It returns a
5-tuple -- (metrics, ranking, performance, statistics, quality) -- the
same shape the analytics module in the student-performance example
returns, adapted to what a demand-forecasting dataset actually has:

  metrics      overall KPI numbers for the hero strip (dict)
  ranking      one row per product+category, sorted by revenue (DataFrame)
  performance  category / region / store scorecards (dict of lists)
  statistics   trends, correlations and distribution summaries (dict)
  quality      what was wrong with the source file, and what got fixed (dict)
"""

import numpy as np
import pandas as pd

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

CORRELATION_COLUMNS = [
    "inventory_level", "units_sold", "units_ordered", "price", "discount",
    "promotion", "competitor_pricing", "epidemic", "revenue", "demand",
]


def _safe_round(value, digits=2):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return None
    return round(float(value), digits)


def compute_metrics(df):
    """Headline KPI numbers for the dashboard's top strip."""
    total_demand = df["demand"].sum()
    total_units_sold = df["units_sold"].sum()

    with_promo = df.loc[df["promotion"] == 1, "demand"].mean()
    without_promo = df.loc[df["promotion"] == 0, "demand"].mean()
    promotion_lift = (with_promo / without_promo - 1) * 100 if without_promo else None

    normal_demand = df.loc[df["epidemic"] == 0, "demand"].mean()
    epidemic_demand = df.loc[df["epidemic"] == 1, "demand"].mean()
    epidemic_impact = (
        (epidemic_demand / normal_demand - 1) * 100 if normal_demand else None
    )

    top_category = (
        df.groupby("category")["revenue"].sum().sort_values(ascending=False).index[0]
    )
    top_season = (
        df.groupby("seasonality")["demand"].mean().sort_values(ascending=False).index[0]
    )

    return {
        "total_records": int(len(df)),
        "total_revenue": _safe_round(df["revenue"].sum()),
        "total_units_sold": int(total_units_sold),
        "total_demand": int(total_demand),
        "total_unmet_demand": int(df["unmet_demand"].sum()),
        "average_inventory": _safe_round(df["inventory_level"].mean()),
        "average_demand": _safe_round(df["demand"].mean()),
        "fulfilment_rate": _safe_round(total_units_sold / total_demand * 100),
        "stock_out_rate": _safe_round(df["stock_out_risk"].mean() * 100),
        "average_discount": _safe_round(df["discount"].mean()),
        "promotion_lift": _safe_round(promotion_lift),
        "epidemic_impact": _safe_round(epidemic_impact),
        "top_category": top_category,
        "top_season": top_season,
    }


def compute_ranking(df):
    """One row per product+category (some product IDs span categories),
    sorted by total revenue, with a 1-based rank column."""
    ranking = (
        df.groupby(["product_id", "category"])
        .agg(
            total_revenue=("revenue", "sum"),
            total_units_sold=("units_sold", "sum"),
            average_demand=("demand", "mean"),
            stock_out_rate=("stock_out_risk", "mean"),
            fulfilment_rate=("fulfilment_rate", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
        .reset_index(drop=True)
    )

    ranking["total_revenue"] = ranking["total_revenue"].round(2)
    ranking["average_demand"] = ranking["average_demand"].round(1)
    ranking["stock_out_rate"] = (ranking["stock_out_rate"] * 100).round(2)
    ranking["fulfilment_rate"] = ranking["fulfilment_rate"].round(2)
    ranking.insert(0, "rank", ranking.index + 1)

    return ranking


def _group_scorecard(df, key):
    grouped = (
        df.groupby(key)
        .agg(
            total_revenue=("revenue", "sum"),
            total_units_sold=("units_sold", "sum"),
            average_demand=("demand", "mean"),
            average_inventory=("inventory_level", "mean"),
            average_coverage=("inventory_coverage", "mean"),
            stock_out_rate=("stock_out_risk", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    grouped["total_revenue"] = grouped["total_revenue"].round(2)
    grouped["average_demand"] = grouped["average_demand"].round(1)
    grouped["average_inventory"] = grouped["average_inventory"].round(1)
    grouped["average_coverage"] = grouped["average_coverage"].round(2)
    grouped["stock_out_rate"] = (grouped["stock_out_rate"] * 100).round(2)
    grouped = grouped.rename(columns={key: "name"})
    return grouped.to_dict(orient="records")


def compute_performance(df):
    """Scorecards grouped by category, region and store."""
    return {
        "category": _group_scorecard(df, "category"),
        "region": _group_scorecard(df, "region"),
        "store": _group_scorecard(df, "store_id"),
    }


def compute_statistics(df):
    """Trends, correlations and distribution summaries."""
    correlation = df[CORRELATION_COLUMNS].corr()["demand"].drop("demand")
    correlation = correlation.round(3).sort_values(ascending=False)

    monthly = (
        df.groupby("month_start")
        .agg(
            total_revenue=("revenue", "sum"),
            total_units_sold=("units_sold", "sum"),
            total_demand=("demand", "sum"),
        )
        .reset_index()
        .sort_values("month_start")
    )
    monthly["month_start"] = monthly["month_start"].dt.strftime("%Y-%m")
    monthly["total_revenue"] = monthly["total_revenue"].round(2)

    seasonal = (
        df.groupby("seasonality")["demand"].mean().round(2).sort_values(ascending=False)
    )

    weather = (
        df.groupby("weather_condition")["demand"]
        .mean()
        .round(2)
        .sort_values(ascending=False)
    )

    discount_band = (
        df.groupby("discount_band", observed=True)["demand"].mean().round(2)
    )

    promotion = (
        df.groupby("promotion")["demand"].mean().round(2).rename(
            index={0: "No Promotion", 1: "Promotion"}
        )
    )

    price_position = (
        df.groupby("price_position")["demand"].mean().round(2).sort_values(ascending=False)
    )

    month_demand = (
        df.groupby("month_name")["demand"].mean().reindex(MONTH_ORDER).round(2)
    )

    weekday_demand = (
        df.groupby("day_name")["demand"].mean().reindex(DAY_ORDER).round(2)
    )

    weekend_vs_weekday = (
        df.groupby("is_weekend")["demand"]
        .mean()
        .round(2)
        .rename(index={0: "Weekday", 1: "Weekend"})
    )

    outlier_summary = {}
    for column in ["inventory_level", "units_sold", "price", "demand", "revenue"]:
        q1, q3 = df[column].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_summary[column] = int(((df[column] < lower) | (df[column] > upper)).sum())

    return {
        "correlation_with_demand": correlation.to_dict(),
        "monthly_trend": monthly.to_dict(orient="records"),
        "seasonal_demand": seasonal.to_dict(),
        "weather_demand": weather.to_dict(),
        "discount_band_demand": {str(k): v for k, v in discount_band.to_dict().items()},
        "promotion_demand": promotion.to_dict(),
        "price_position_demand": price_position.to_dict(),
        "month_demand": month_demand.to_dict(),
        "weekday_demand": weekday_demand.to_dict(),
        "weekend_vs_weekday": weekend_vs_weekday.to_dict(),
        "outlier_counts": outlier_summary,
        "numeric_summary": df[CORRELATION_COLUMNS].describe().round(2).to_dict(),
    }


def compute_quality(df):
    """Pull the pre-cleaning report attached by preprocessing.py and add
    a short, plain-language summary of what cleaning actually did."""
    report = dict(df.attrs.get("quality_report", {}))

    notes = []
    if report.get("duplicate_rows"):
        notes.append(
            f"Removed {report['duplicate_rows']} duplicate rows "
            f"({report['rows_in_file']} -> {report.get('rows_after_cleaning', len(df))})."
        )
    if report.get("total_missing_cells"):
        missing_cols = ", ".join(report.get("missing_values", {}).keys())
        notes.append(
            f"Filled {report['total_missing_cells']} missing cells across "
            f"{missing_cols} (median for numbers, mode for categories)."
        )
    invalid_total = sum(report.get("invalid_records", {}).values())
    if invalid_total:
        notes.append(f"Flagged {invalid_total} rows breaking a business rule.")
    else:
        notes.append("No business-rule violations found (prices, discounts, stock all in range).")

    report["cleaning_notes"] = notes
    return report


def analyze_data(df):
    metrics = compute_metrics(df)
    ranking = compute_ranking(df)
    performance = compute_performance(df)
    statistics = compute_statistics(df)
    quality = compute_quality(df)
    return metrics, ranking, performance, statistics, quality