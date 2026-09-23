/* Reads the chart JSON Flask embedded in #chart-data and turns each
 * entry into a Chart.js chart. Kept deliberately flat (one block per
 * chart, not a generic factory) so it's easy to see which canvas id
 * maps to which backend/charts.py key. */

const CHARTS = JSON.parse(document.getElementById("chart-data").textContent);

const style = getComputedStyle(document.documentElement);
const COLOR_TEXT_MUTED = style.getPropertyValue("--text-muted").trim();
const COLOR_BORDER = style.getPropertyValue("--border").trim();
const COLOR_TEAL = style.getPropertyValue("--teal").trim();
const COLOR_AMBER = style.getPropertyValue("--amber").trim();
const COLOR_CLAY = style.getPropertyValue("--clay").trim();
const FONT_BODY = "'IBM Plex Sans', sans-serif";

Chart.defaults.font.family = FONT_BODY;
Chart.defaults.font.size = 12;
Chart.defaults.color = COLOR_TEXT_MUTED;

const grid = { color: COLOR_BORDER, drawTicks: false };
const noLegend = { legend: { display: false } };

function palette(n, base) {
  // Single hue, stepped opacity -- avoids a rainbow of unrelated colors
  // across bars that all mean the same kind of thing.
  return Array.from({ length: n }, (_, i) => {
    const alpha = 1 - (i / Math.max(n, 6)) * 0.55;
    return base === "amber"
      ? `rgba(232, 163, 61, ${alpha.toFixed(2)})`
      : `rgba(79, 183, 179, ${alpha.toFixed(2)})`;
  });
}

/* ---------- Sales ---------- */

new Chart(document.getElementById("chart-category-revenue"), {
  type: "bar",
  data: {
    labels: CHARTS.category_revenue.labels,
    datasets: [{
      data: CHARTS.category_revenue.data,
      backgroundColor: palette(CHARTS.category_revenue.labels.length, "teal"),
      borderRadius: 2,
      maxBarThickness: 40,
    }],
  },
  options: {
    plugins: noLegend,
    scales: {
      x: { grid: { display: false } },
      y: { grid, ticks: { callback: (v) => (v / 1e6).toFixed(0) + "M" } },
    },
  },
});

new Chart(document.getElementById("chart-category-share"), {
  type: "doughnut",
  data: {
    labels: CHARTS.category_share.labels,
    datasets: [{
      data: CHARTS.category_share.data,
      backgroundColor: palette(CHARTS.category_share.labels.length, "teal"),
      borderColor: style.getPropertyValue("--panel").trim(),
      borderWidth: 2,
    }],
  },
  options: {
    plugins: {
      legend: { position: "right", labels: { boxWidth: 12, padding: 12 } },
    },
  },
});

new Chart(document.getElementById("chart-top-products"), {
  type: "bar",
  data: {
    labels: CHARTS.top_products.labels,
    datasets: [{
      data: CHARTS.top_products.data,
      backgroundColor: COLOR_TEAL,
      borderRadius: 2,
    }],
  },
  options: {
    indexAxis: "y",
    plugins: noLegend,
    scales: {
      x: { grid, ticks: { callback: (v) => (v / 1e6).toFixed(1) + "M" } },
      y: { grid: { display: false } },
    },
  },
});

new Chart(document.getElementById("chart-region-revenue"), {
  type: "bar",
  data: {
    labels: CHARTS.region_revenue.labels,
    datasets: [{
      data: CHARTS.region_revenue.data,
      backgroundColor: palette(CHARTS.region_revenue.labels.length, "teal"),
      borderRadius: 2,
      maxBarThickness: 48,
    }],
  },
  options: {
    plugins: noLegend,
    scales: {
      x: { grid: { display: false } },
      y: { grid, ticks: { callback: (v) => (v / 1e6).toFixed(0) + "M" } },
    },
  },
});

new Chart(document.getElementById("chart-store-revenue"), {
  type: "bar",
  data: {
    labels: CHARTS.store_revenue.labels,
    datasets: [{
      data: CHARTS.store_revenue.data,
      backgroundColor: palette(CHARTS.store_revenue.labels.length, "teal"),
      borderRadius: 2,
      maxBarThickness: 48,
    }],
  },
  options: {
    plugins: noLegend,
    scales: {
      x: { grid: { display: false } },
      y: { grid, ticks: { callback: (v) => (v / 1e6).toFixed(0) + "M" } },
    },
  },
});

/* ---------- Demand drivers ---------- */

new Chart(document.getElementById("chart-monthly-trend"), {
  type: "line",
  data: {
    labels: CHARTS.monthly_trend.labels,
    datasets: [
      {
        label: "Revenue",
        data: CHARTS.monthly_trend.revenue,
        borderColor: COLOR_TEAL,
        backgroundColor: "transparent",
        yAxisID: "y",
        tension: 0.25,
        pointRadius: 2,
      },
      {
        label: "Demand (units)",
        data: CHARTS.monthly_trend.demand,
        borderColor: COLOR_AMBER,
        backgroundColor: "transparent",
        yAxisID: "y1",
        tension: 0.25,
        pointRadius: 2,
      },
    ],
  },
  options: {
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { position: "top", labels: { boxWidth: 10 } } },
    scales: {
      x: { grid: { display: false }, ticks: { maxRotation: 45, minRotation: 45 } },
      y: {
        position: "left",
        grid,
        ticks: { callback: (v) => (v / 1e6).toFixed(0) + "M" },
      },
      y1: {
        position: "right",
        grid: { display: false },
        ticks: { callback: (v) => (v / 1e3).toFixed(0) + "k" },
      },
    },
  },
});

new Chart(document.getElementById("chart-seasonal-demand"), {
  type: "bar",
  data: {
    labels: CHARTS.seasonal_demand.labels,
    datasets: [{
      data: CHARTS.seasonal_demand.data,
      backgroundColor: palette(CHARTS.seasonal_demand.labels.length, "teal"),
      borderRadius: 2,
      maxBarThickness: 48,
    }],
  },
  options: { plugins: noLegend, scales: { x: { grid: { display: false } }, y: { grid } } },
});

new Chart(document.getElementById("chart-weather-demand"), {
  type: "bar",
  data: {
    labels: CHARTS.weather_demand.labels,
    datasets: [{
      data: CHARTS.weather_demand.data,
      backgroundColor: palette(CHARTS.weather_demand.labels.length, "teal"),
      borderRadius: 2,
      maxBarThickness: 48,
    }],
  },
  options: { plugins: noLegend, scales: { x: { grid: { display: false } }, y: { grid } } },
});

new Chart(document.getElementById("chart-month-demand"), {
  type: "line",
  data: {
    labels: CHARTS.month_demand.labels,
    datasets: [{
      data: CHARTS.month_demand.data,
      borderColor: COLOR_TEAL,
      backgroundColor: "rgba(79, 183, 179, 0.12)",
      fill: true,
      tension: 0.3,
      pointRadius: 2,
    }],
  },
  options: {
    plugins: noLegend,
    scales: { x: { grid: { display: false } }, y: { grid } },
  },
});

new Chart(document.getElementById("chart-weekday-demand"), {
  type: "bar",
  data: {
    labels: CHARTS.weekday_demand.labels,
    datasets: [{
      data: CHARTS.weekday_demand.data,
      backgroundColor: palette(7, "teal"),
      borderRadius: 2,
      maxBarThickness: 40,
    }],
  },
  options: { plugins: noLegend, scales: { x: { grid: { display: false } }, y: { grid } } },
});

/* ---------- Pricing & promotion ---------- */

new Chart(document.getElementById("chart-discount-band"), {
  type: "bar",
  data: {
    labels: CHARTS.discount_band_demand.labels,
    datasets: [{
      data: CHARTS.discount_band_demand.data,
      backgroundColor: palette(CHARTS.discount_band_demand.labels.length, "amber"),
      borderRadius: 2,
      maxBarThickness: 48,
    }],
  },
  options: { plugins: noLegend, scales: { x: { grid: { display: false } }, y: { grid } } },
});

new Chart(document.getElementById("chart-promotion"), {
  type: "bar",
  data: {
    labels: CHARTS.promotion_demand.labels,
    datasets: [{
      data: CHARTS.promotion_demand.data,
      backgroundColor: [COLOR_TEXT_MUTED, COLOR_AMBER],
      borderRadius: 2,
      maxBarThickness: 60,
    }],
  },
  options: { plugins: noLegend, scales: { x: { grid: { display: false } }, y: { grid } } },
});

new Chart(document.getElementById("chart-price-position"), {
  type: "bar",
  data: {
    labels: CHARTS.price_position_demand.labels,
    datasets: [{
      data: CHARTS.price_position_demand.data,
      backgroundColor: palette(CHARTS.price_position_demand.labels.length, "teal"),
      borderRadius: 2,
      maxBarThickness: 60,
    }],
  },
  options: { plugins: noLegend, scales: { x: { grid: { display: false } }, y: { grid } } },
});

/* ---------- Correlation & risk ---------- */

new Chart(document.getElementById("chart-correlation"), {
  type: "bar",
  data: {
    labels: CHARTS.correlation.labels,
    datasets: [{
      data: CHARTS.correlation.data,
      backgroundColor: CHARTS.correlation.data.map((v) =>
        v >= 0 ? COLOR_TEAL : COLOR_CLAY
      ),
      borderRadius: 2,
    }],
  },
  options: {
    indexAxis: "y",
    plugins: noLegend,
    scales: {
      x: { grid, min: -0.6, max: 1 },
      y: { grid: { display: false } },
    },
  },
});

new Chart(document.getElementById("chart-stock-out"), {
  type: "bar",
  data: {
    labels: CHARTS.stock_out_by_category.labels,
    datasets: [{
      data: CHARTS.stock_out_by_category.data,
      backgroundColor: CHARTS.stock_out_by_category.data.map((v) =>
        v >= 15 ? COLOR_CLAY : COLOR_AMBER
      ),
      borderRadius: 2,
      maxBarThickness: 48,
    }],
  },
  options: {
    plugins: noLegend,
    scales: {
      x: { grid: { display: false } },
      y: { grid, ticks: { callback: (v) => v + "%" } },
    },
  },
});

/* ---------- Sidebar scrollspy ---------- */

const navLinks = document.querySelectorAll(".sidebar__nav a");
const sections = Array.from(navLinks).map((link) =>
  document.querySelector(link.getAttribute("href"))
);

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = "#" + entry.target.id;
      navLinks.forEach((link) => {
        link.classList.toggle("is-active", link.getAttribute("href") === id);
      });
    });
  },
  { rootMargin: "-20% 0px -70% 0px" }
);

sections.forEach((section) => section && observer.observe(section));