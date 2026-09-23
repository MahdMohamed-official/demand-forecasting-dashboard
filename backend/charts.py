"""Reshape analytics results into Chart.js-ready dicts.

This module never touches the DataFrame -- it only rearranges the plain
Python structures analytics.py already computed into
`{"labels": [...], "data": [...]}` shapes that static/js/dashboard.js
feeds straight into `new Chart(...)`. Keeping the pandas work out of this
file is deliberate: it's the one module a student could hand a frontend
teammate without also handing them pandas.
"""

TOP_PRODUCTS_LIMIT = 10


def _labels_values(d, limit=None, sort_desc=True):
    items = list(d.items())
    if sort_desc:
        items.sort(key=lambda pair: (pair[1] is None, -(pair[1] or 0)))
    if limit:
        items = items[:limit]
    labels = [str(label) for label, _ in items]
    values = [value for _, value in items]
    return {"labels": labels, "data": values}


def prepare_chart_data(metrics, ranking, performance, statistics):
    """Build every chart the dashboard renders, keyed by the id
    static/js/dashboard.js looks each one up with.
    """
    charts = {}

    # --- Sales: revenue and demand by category -----------------------------
    category = performance["category"]
    charts["category_revenue"] = {
        "labels": [row["name"] for row in category],
        "data": [row["total_revenue"] for row in category],
    }
    charts["category_share"] = {
        "labels": [row["name"] for row in category],
        "data": [row["total_revenue"] for row in category],
    }

    # --- Top products by revenue -------------------------------------------
    top_products = ranking.head(TOP_PRODUCTS_LIMIT)
    charts["top_products"] = {
        "labels": [
            f"{row.product_id} ({row.category})" for row in top_products.itertuples()
        ],
        "data": top_products["total_revenue"].tolist(),
    }

    # --- Region / store performance -----------------------------------------
    region = performance["region"]
    charts["region_revenue"] = {
        "labels": [row["name"] for row in region],
        "data": [row["total_revenue"] for row in region],
    }
    store = performance["store"]
    charts["store_revenue"] = {
        "labels": [row["name"] for row in store],
        "data": [row["total_revenue"] for row in store],
    }

    # --- Demand trend over time -----------------------------------------------
    monthly = statistics["monthly_trend"]
    charts["monthly_trend"] = {
        "labels": [row["month_start"] for row in monthly],
        "revenue": [row["total_revenue"] for row in monthly],
        "demand": [row["total_demand"] for row in monthly],
        "units_sold": [row["total_units_sold"] for row in monthly],
    }

    # --- Demand drivers ---------------------------------------------------
    charts["seasonal_demand"] = _labels_values(statistics["seasonal_demand"])
    charts["weather_demand"] = _labels_values(statistics["weather_demand"])
    charts["month_demand"] = {
        "labels": list(statistics["month_demand"].keys()),
        "data": list(statistics["month_demand"].values()),
    }
    charts["weekday_demand"] = {
        "labels": list(statistics["weekday_demand"].keys()),
        "data": list(statistics["weekday_demand"].values()),
    }

    # --- Pricing & promotion -------------------------------------------------
    charts["discount_band_demand"] = _labels_values(
        statistics["discount_band_demand"], sort_desc=False
    )
    charts["promotion_demand"] = _labels_values(
        statistics["promotion_demand"], sort_desc=False
    )
    charts["price_position_demand"] = _labels_values(statistics["price_position_demand"])

    # --- Correlation with demand -----------------------------------------
    charts["correlation"] = _labels_values(statistics["correlation_with_demand"])

    # --- Risk: stock-out rate and unmet demand by category ------------------
    charts["stock_out_by_category"] = {
        "labels": [row["name"] for row in category],
        "data": [row["stock_out_rate"] for row in category],
    }

    return charts