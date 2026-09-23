from flask import Flask, render_template
import math
from numbers import Number

from backend.preprocessing import preprocess_data
from backend.analytics import analyze_data
from backend.charts import prepare_chart_data


app = Flask(__name__)

@app.template_filter("commas")
def commas(value, decimals=0):
    if value is None:
        return ""

    try:
        decimals = int(decimals)
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return value
    
DATA_PATH = "data/demand_forecasting.csv"


def clean_for_json(obj):
    """Convert NaN/Infinity and NumPy scalar values to JSON-safe values."""
    if isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [clean_for_json(value) for value in obj]

    # NumPy scalar -> native Python scalar
    if hasattr(obj, "item") and type(obj).__module__.startswith("numpy"):
        return clean_for_json(obj.item())

    if isinstance(obj, Number) and not isinstance(obj, bool):
        value = float(obj)
        if not math.isfinite(value):
            return None
        return obj

    return obj


@app.route("/")
def dashboard():
    # Load, clean and feature-engineer the dataset
    df = preprocess_data(DATA_PATH)

    # Analytics
    metrics, ranking, performance, statistics, quality = analyze_data(df)

    # Chart data
    charts = prepare_chart_data(metrics, ranking, performance, statistics)

    # Make data safe for JSON/Jinja
    metrics = clean_for_json(metrics)
    ranking_records = clean_for_json(ranking.to_dict(orient="records"))
    performance = clean_for_json(performance)
    statistics = clean_for_json(statistics)
    charts = clean_for_json(charts)
    quality = clean_for_json(quality)

    return render_template(
        "index.html",
        metrics=metrics,
        ranking=ranking_records,
        ranking_json=ranking_records,
        performance=performance,
        statistics=statistics,
        charts=charts,
        quality=quality,
    )


if __name__ == "__main__":
    app.run(debug=True)