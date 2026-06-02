from __future__ import annotations

import ast
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


PROJECT_DIR = Path(__file__).parent
RESULTS_DIR = Path(r"D:\CE49X_FinalProject\results\outputs\figures")
LEGACY_DIR = Path(r"D:\CE49X_FinalProject\figures")
PACKAGE_ROOT = Path(r"D:\CE49X_FinalProject")
OUTPUT_HTML = RESULTS_DIR / "dashboard.html"
PACKAGE_HTML = PACKAGE_ROOT / "dashboard.html"
ASSET_SUBDIR = "pngs_for_html"
RESULTS_ASSETS_DIR = RESULTS_DIR / ASSET_SUBDIR
LEGACY_ASSETS_DIR = LEGACY_DIR / ASSET_SUBDIR
PACKAGE_ASSETS_DIR = PACKAGE_ROOT / ASSET_SUBDIR


PNG_FILES = [
    "dashboard.png",
    "task2_spatial_events_frp_region.png",
    "task2_temporal_monthly_event_count.png",
    "task3_association_rate_bar.png",
    "ml_model_comparison_f1_recall_precision.png",
    "ml_confusion_matrix_random_forest_tuned.png",
    "ml_geography_robustness_f1_recall.png",
    "drift_monthly_f1_recall.png",
    "drift_retraining_triggers_timeline.png",
    "drift_region_positive_rate_heatmap.png",
]

CSV_FILES = [
    "control_region_diagnostics.csv",
    "dbscan_sensitivity_summary.csv",
    "dbscan_region_summary_main.csv",
    "ml_model_comparison_full.csv",
    "ml_geography_robustness_comparison.csv",
    "drift_monthly_metrics.csv",
    "drift_retraining_triggers.csv",
    "drift_region_monthly_metrics.csv",
    "task3_best_tuned_model_metrics.csv",
    "task3_conflict_association_rate_by_region.csv",
    "task3_event_scores.csv",
]


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def find_file(name: str) -> Path | None:
    candidates = [RESULTS_DIR / name, LEGACY_DIR / name, PROJECT_DIR / name]
    for c in candidates:
        if c.exists():
            return c
    return None


def maybe_copy_to_results(src: Path | None, name: str) -> Path | None:
    if src is None:
        return None
    dst = RESULTS_ASSETS_DIR / name
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
    legacy_dst = LEGACY_ASSETS_DIR / name
    if src.resolve() != legacy_dst.resolve():
        shutil.copy2(src, legacy_dst)
    package_dst = PACKAGE_ASSETS_DIR / name
    if src.resolve() != package_dst.resolve():
        shutil.copy2(src, package_dst)
    return dst


def safe_read_csv(name: str) -> pd.DataFrame:
    fp = find_file(name)
    if not fp:
        return pd.DataFrame()
    try:
        return pd.read_csv(fp)
    except Exception:
        return pd.DataFrame()


def html_escape(x: Any) -> str:
    s = "" if x is None else str(x)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def fmt_num(x: Any, digits: int = 2) -> str:
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return "NA"


def fmt_pct(x: Any) -> str:
    try:
        xv = float(x)
        if xv <= 1:
            xv *= 100
        return f"{xv:.2f}%"
    except Exception:
        return "NA"


def figure_block(title: str, fname: str) -> tuple[str, bool]:
    src = find_file(fname)
    if not src:
        return (
            f"""
            <div class="figure-card">
              <h4>{html_escape(title)}</h4>
              <div class="placeholder">Figure not available: {html_escape(fname)}</div>
            </div>
            """,
            False,
        )
    dst = maybe_copy_to_results(src, fname)
    rel = f"{ASSET_SUBDIR}/{dst.name}" if dst else f"{ASSET_SUBDIR}/{fname}"
    return (
        f"""
        <div class="figure-card">
          <h4>{html_escape(title)}</h4>
          <img src="{html_escape(rel)}" alt="{html_escape(title)}" loading="lazy"/>
        </div>
        """,
        True,
    )


def table_block(title: str, df: pd.DataFrame) -> str:
    if df.empty:
        return f"""
        <div class="table-card">
          <h4>{html_escape(title)}</h4>
          <div class="placeholder">Table not available</div>
        </div>
        """
    return f"""
    <div class="table-card">
      <h4>{html_escape(title)}</h4>
      <div class="table-wrap">{df.to_html(index=False, classes='dash-table', border=0, escape=False)}</div>
    </div>
    """


def safe_sql(engine, query: str) -> pd.DataFrame:
    try:
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame()


def load_data_sources() -> tuple[dict[str, pd.DataFrame], list[str], bool]:
    loaded: list[str] = []
    data: dict[str, pd.DataFrame] = {}

    load_dotenv(PROJECT_DIR / ".env")
    db_url = os.getenv("DATABASE_URL", "postgresql://ce49x@localhost:5432/conflict_monitoring")
    engine = None
    db_available = False
    try:
        engine = create_engine(db_url)
        ping = safe_sql(engine, "SELECT 1 AS ok")
        db_available = not ping.empty
    except Exception:
        engine = None

    if engine is not None and db_available:
        firms = safe_sql(
            engine,
            """
            SELECT latitude, longitude, region, acq_date, frp,
                   COALESCE(bright_ti4, bright_ti5) AS brightness,
                   confidence
            FROM firms_detections
            """,
        )
        events = safe_sql(
            engine,
            """
            SELECT event_id, region, start_date, end_date, duration_days, total_frp,
                   max_brightness, detection_points, centroid_latitude, centroid_longitude
            FROM thermal_events
            """,
        )
        scores = safe_sql(engine, "SELECT event_id, event_score, conflict_associated FROM event_scores")
        if scores.empty:
            scores = safe_sql(engine, "SELECT event_id, event_score FROM event_scores")
            if not scores.empty:
                matches = safe_sql(engine, "SELECT DISTINCT event_id FROM event_matches")
                matched = set(matches["event_id"].astype(str)) if not matches.empty else set()
                scores["conflict_associated"] = scores["event_id"].astype(str).isin(matched).astype(int)
        matches = safe_sql(engine, "SELECT DISTINCT event_id FROM event_matches")
        news = safe_sql(engine, "SELECT source FROM news_articles")

        if not firms.empty:
            loaded.append("db:firms_detections")
        if not events.empty:
            loaded.append("db:thermal_events")
        if not scores.empty:
            loaded.append("db:event_scores")
        if not matches.empty:
            loaded.append("db:event_matches")
        if not news.empty:
            loaded.append("db:news_articles")

        data["firms"] = firms
        data["events"] = events
        data["scores"] = scores
        data["matches"] = matches
        data["news"] = news
    else:
        loaded.append("db:unavailable")
        data["firms"] = pd.DataFrame()
        data["events"] = pd.DataFrame()
        data["scores"] = pd.DataFrame()
        data["matches"] = pd.DataFrame()
        data["news"] = pd.DataFrame()

    # CSV fallback/secondary sources
    for name in CSV_FILES:
        df = safe_read_csv(name)
        key = name.replace(".csv", "")
        data[key] = df
        if not df.empty:
            loaded.append(f"csv:{name}")

    return data, loaded, db_available


def build_map_payload(
    firms: pd.DataFrame,
    events: pd.DataFrame,
    scores: pd.DataFrame,
    max_firms: int = 15000,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    meta: dict[str, Any] = {
        "firms_available": int(len(firms)),
        "firms_plotted": 0,
        "firms_sampled": False,
        "events_plotted": 0,
        "associated_events_plotted": 0,
    }

    firms_layer: list[dict[str, Any]] = []
    if not firms.empty and {"latitude", "longitude"}.issubset(firms.columns):
        fd = firms.copy()
        fd = fd.dropna(subset=["latitude", "longitude"])
        meta["firms_available"] = int(len(fd))
        if len(fd) > max_firms:
            fd = fd.sample(n=max_firms, random_state=42)
            meta["firms_sampled"] = True
        meta["firms_plotted"] = int(len(fd))
        firms_layer = (
            fd.assign(
                acq_date=lambda d: pd.to_datetime(d.get("acq_date"), errors="coerce").dt.date.astype(str),
                frp=lambda d: pd.to_numeric(d.get("frp"), errors="coerce"),
                brightness=lambda d: pd.to_numeric(d.get("brightness"), errors="coerce"),
            )
            .rename(columns={"latitude": "lat", "longitude": "lon"})
            [[c for c in ["lat", "lon", "region", "acq_date", "frp", "brightness", "confidence"] if c in fd.columns or c in ["lat", "lon"]]]
            .to_dict(orient="records")
        )

    events_layer: list[dict[str, Any]] = []
    if not events.empty and {"centroid_latitude", "centroid_longitude"}.issubset(events.columns):
        ev = events.copy()
        ev["event_id"] = ev["event_id"].astype(str)
        ev = ev.dropna(subset=["centroid_latitude", "centroid_longitude"])
        if not scores.empty and "event_id" in scores.columns:
            sc = scores.copy()
            sc["event_id"] = sc["event_id"].astype(str)
            ev = ev.merge(sc[["event_id", "event_score", "conflict_associated"]], on="event_id", how="left")
        else:
            ev["event_score"] = pd.NA
            ev["conflict_associated"] = pd.NA

        ev["conflict_associated"] = ev["conflict_associated"].fillna(0).astype(int)
        ev["total_frp"] = pd.to_numeric(ev.get("total_frp"), errors="coerce").fillna(0)
        ev["marker_radius"] = ev["total_frp"].clip(lower=0).pow(0.5).div(20).clip(lower=4, upper=14)
        ev["start_date"] = pd.to_datetime(ev.get("start_date"), errors="coerce").dt.date.astype(str)
        ev["end_date"] = pd.to_datetime(ev.get("end_date"), errors="coerce").dt.date.astype(str)
        meta["events_plotted"] = int(len(ev))
        meta["associated_events_plotted"] = int((ev["conflict_associated"] == 1).sum())
        events_layer = (
            ev.rename(columns={"centroid_latitude": "lat", "centroid_longitude": "lon"})
            [
                [
                    "lat",
                    "lon",
                    "event_id",
                    "region",
                    "start_date",
                    "end_date",
                    "duration_days",
                    "total_frp",
                    "max_brightness",
                    "detection_points",
                    "event_score",
                    "conflict_associated",
                    "marker_radius",
                ]
            ]
            .to_dict(orient="records")
        )

    return firms_layer, events_layer, meta


def build_kpis(data: dict[str, pd.DataFrame]) -> dict[str, str]:
    firms = data.get("firms", pd.DataFrame())
    events = data.get("events", pd.DataFrame())
    scores = data.get("scores", pd.DataFrame())
    dbscan = data.get("dbscan_sensitivity_summary", pd.DataFrame())
    control = data.get("control_region_diagnostics", pd.DataFrame())
    tuned = data.get("task3_best_tuned_model_metrics", pd.DataFrame())
    model_cmp = data.get("ml_model_comparison_full", pd.DataFrame())

    total_firms = len(firms)
    if total_firms == 0 and not dbscan.empty:
        main = dbscan[dbscan["setting"] == "main"]
        if not main.empty:
            total_firms = int(main["n_total_firms_points"].iloc[0])

    total_events = len(events)
    if total_events == 0 and not dbscan.empty:
        main = dbscan[dbscan["setting"] == "main"]
        if not main.empty:
            total_events = int(main["n_events"].iloc[0])

    conflict_events = 0
    if not scores.empty and "conflict_associated" in scores.columns:
        conflict_events = int(pd.to_numeric(scores["conflict_associated"], errors="coerce").fillna(0).astype(int).sum())
    elif not data.get("task3_event_scores", pd.DataFrame()).empty:
        es = data["task3_event_scores"]
        if "conflict_associated" in es.columns:
            conflict_events = int(pd.to_numeric(es["conflict_associated"], errors="coerce").fillna(0).astype(int).sum())
            if total_events == 0:
                total_events = len(es)

    assoc_rate = (conflict_events / total_events) if total_events else 0

    best_model = "random_forest"
    best_threshold = "NA"
    best_recall = "NA"
    best_f1 = "NA"
    if not tuned.empty:
        row = tuned.iloc[0]
        best_model = str(row.get("model", best_model))
        best_threshold = fmt_num(row.get("threshold"), 1)
        best_recall = fmt_num(row.get("recall"), 3)
        best_f1 = fmt_num(row.get("f1"), 3)
    elif not model_cmp.empty:
        row = model_cmp.sort_values("f1", ascending=False).iloc[0]
        best_model = str(row.get("model", best_model))
        best_recall = fmt_num(row.get("recall"), 3)
        best_f1 = fmt_num(row.get("f1"), 3)

    sahara_rate = "NA"
    rub_rate = "NA"
    if not control.empty and "region" in control.columns:
        sah = control[control["region"] == "sahara_control"]
        rub = control[control["region"] == "rub_al_khali_control"]
        if not sah.empty:
            sahara_rate = fmt_pct(sah["association_rate"].iloc[0])
        if not rub.empty:
            rub_rate = fmt_pct(rub["association_rate"].iloc[0])

    return {
        "Total FIRMS detections": f"{total_firms:,}",
        "Total thermal events": f"{total_events:,}",
        "Conflict-associated events": f"{conflict_events:,}",
        "Overall conflict-association rate": fmt_pct(assoc_rate),
        "Best model": best_model,
        "Best threshold": best_threshold,
        "Best model recall": best_recall,
        "Best model F1": best_f1,
        "Sahara association rate": sahara_rate,
        "Rub al Khali association rate": rub_rate,
    }


def parse_assoc_rate_col(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "association_rate_by_region" in out.columns:
        sah_vals = []
        rub_vals = []
        for v in out["association_rate_by_region"]:
            sah, rub = None, None
            try:
                obj = ast.literal_eval(v) if isinstance(v, str) else v
                if isinstance(obj, dict):
                    sah = obj.get("sahara_control")
                    rub = obj.get("rub_al_khali_control")
            except Exception:
                pass
            sah_vals.append(sah)
            rub_vals.append(rub)
        out["sahara_control_association_rate"] = sah_vals
        out["rub_al_khali_control_association_rate"] = rub_vals
    return out


def main() -> None:
    ensure_dirs()
    data, loaded_sources, db_available = load_data_sources()
    kpis = build_kpis(data)

    firms_layer, events_layer, map_meta = build_map_payload(
        data.get("firms", pd.DataFrame()),
        data.get("events", pd.DataFrame()),
        data.get("scores", pd.DataFrame()),
    )
    if map_meta["firms_plotted"] == 0 and map_meta["events_plotted"] == 0:
        map_status_note = (
            "Map layers are currently empty because PostgreSQL map-source tables are unavailable. "
            "Start the CE49X PostgreSQL service/container and re-run this script."
        )
    elif map_meta["firms_sampled"]:
        map_status_note = "Raw FIRMS detections are sampled for map performance."
    else:
        map_status_note = "Raw FIRMS detections are shown without sampling."

    dbscan_tbl = parse_assoc_rate_col(data.get("dbscan_sensitivity_summary", pd.DataFrame()))
    if not dbscan_tbl.empty:
        keep = [
            "setting",
            "n_events",
            "noise_ratio",
            "median_detection_points_per_event",
            "median_duration_days",
            "median_total_frp",
            "sahara_control_association_rate",
            "rub_al_khali_control_association_rate",
        ]
        dbscan_tbl = dbscan_tbl[[c for c in keep if c in dbscan_tbl.columns]]

    control_tbl = data.get("control_region_diagnostics", pd.DataFrame())
    if not control_tbl.empty:
        keep = [
            "region",
            "number_of_thermal_events",
            "number_of_associated_events",
            "association_rate",
            "mean_event_score",
            "median_event_score",
        ]
        control_tbl = control_tbl[[c for c in keep if c in control_tbl.columns]]

    ml_geo = data.get("ml_geography_robustness_comparison", pd.DataFrame())
    if not ml_geo.empty:
        ml_geo = ml_geo.rename(columns={"best_threshold_f1": "best_threshold", "best_f1": "f1"})
        keep = ["model", "variant", "best_threshold", "accuracy", "precision", "recall", "f1"]
        ml_geo = ml_geo[[c for c in keep if c in ml_geo.columns]]

    drift_tr = data.get("drift_retraining_triggers", pd.DataFrame())
    if not drift_tr.empty and "retraining_recommended" in drift_tr.columns:
        v = drift_tr["retraining_recommended"]
        if v.dtype == object:
            v = v.astype(str).str.lower().isin(["true", "1", "yes"])
        drift_tr = drift_tr[v].copy()
    if not drift_tr.empty:
        keep = [
            "period",
            "region",
            "n_samples",
            "precision",
            "recall",
            "f1",
            "trigger_low_recall",
            "trigger_low_f1_2months",
            "trigger_positive_rate_shift",
            "trigger_event_count_spike",
            "trigger_prediction_shift",
        ]
        drift_tr = drift_tr[[c for c in keep if c in drift_tr.columns]].head(20)

    # Build figure blocks
    figure_html: dict[str, str] = {}
    embedded_figs: list[str] = []
    missing_figs: list[str] = []
    titles = {
        "dashboard.png": "Project Overview Dashboard",
        "task2_spatial_events_frp_region.png": "Spatial Distribution of Thermal Event Intensity",
        "task2_temporal_monthly_event_count.png": "Monthly Thermal Event Count by Region",
        "task3_association_rate_bar.png": "Conflict Association Rate by Region",
        "ml_model_comparison_f1_recall_precision.png": "ML Model Comparison (Precision/Recall/F1)",
        "ml_confusion_matrix_random_forest_tuned.png": "Random Forest Tuned Confusion Matrix",
        "ml_geography_robustness_f1_recall.png": "Full vs No-Geography Robustness",
        "drift_monthly_f1_recall.png": "Drift Monitoring: Monthly F1 and Recall",
        "drift_retraining_triggers_timeline.png": "Retraining Trigger Timeline",
        "drift_region_positive_rate_heatmap.png": "Region-Level Positive Rate Heatmap",
    }
    for f in PNG_FILES:
        block, ok = figure_block(titles.get(f, f), f)
        figure_html[f] = block
        if ok:
            embedded_figs.append(f)
        else:
            missing_figs.append(f)

    embedded_tables: list[str] = []
    for csv_name, df in [
        ("dbscan_sensitivity_summary.csv", dbscan_tbl),
        ("control_region_diagnostics.csv", control_tbl),
        ("ml_geography_robustness_comparison.csv", ml_geo),
        ("drift_retraining_triggers.csv", drift_tr),
    ]:
        if not df.empty:
            embedded_tables.append(csv_name)

    kpi_cards = "\n".join(
        [
            f'<div class="kpi-card"><div class="kpi-title">{html_escape(k)}</div><div class="kpi-value">{html_escape(v)}</div></div>'
            for k, v in kpis.items()
        ]
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Conflict Situation Monitoring for Maritime Shipping</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body {{ margin:0; font-family:Segoe UI, Arial, sans-serif; background:#f7f8fa; color:#1b1f24; }}
    .topbar {{ position:sticky; top:0; z-index:1000; background:#fff; border-bottom:1px solid #e5e7eb; padding:12px 20px; }}
    .nav a {{ margin-right:16px; color:#0f3d75; text-decoration:none; font-size:14px; font-weight:600; }}
    .container {{ max-width:1400px; margin:0 auto; padding:18px; }}
    .section {{ background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:18px; margin-bottom:16px; }}
    h1 {{ margin:0 0 6px 0; font-size:30px; }}
    h2 {{ margin:0 0 8px 0; font-size:23px; }}
    h3 {{ margin:0 0 8px 0; font-size:18px; }}
    .subtitle {{ color:#4b5563; margin-bottom:12px; }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:10px; }}
    .kpi-card {{ background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:10px 12px; }}
    .kpi-title {{ color:#6b7280; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
    .kpi-value {{ font-size:22px; font-weight:700; margin-top:4px; color:#111827; }}
    .method-note {{ background:#f3f4f6; border-left:4px solid #2563eb; padding:10px 12px; margin-top:14px; }}
    #map {{ height:650px; border:1px solid #d1d5db; border-radius:8px; }}
    .fig-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(430px, 1fr)); gap:12px; }}
    .figure-card {{ background:#fafafa; border:1px solid #e5e7eb; border-radius:8px; padding:10px; }}
    .figure-card img {{ width:100%; height:auto; border-radius:6px; border:1px solid #e5e7eb; }}
    .placeholder {{ color:#6b7280; font-style:italic; padding:10px; border:1px dashed #cbd5e1; border-radius:6px; background:#fff; }}
    .table-card {{ background:#fafafa; border:1px solid #e5e7eb; border-radius:8px; padding:10px; margin-top:10px; }}
    .table-wrap {{ overflow:auto; max-height:380px; }}
    table.dash-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    table.dash-table th, table.dash-table td {{ border:1px solid #d1d5db; padding:6px 8px; text-align:left; }}
    table.dash-table th {{ background:#f3f4f6; position:sticky; top:0; }}
    ul.tight li {{ margin:4px 0; }}
    .legend-box {{ background:white; border:1px solid #ddd; border-radius:5px; padding:8px; font-size:12px; }}
  </style>
</head>
<body>
  <div class="topbar">
    <div class="nav">
      <a href="#overview">Overview</a>
      <a href="#mapsec">Map</a>
      <a href="#spatial">Spatial-Temporal</a>
      <a href="#association">Association</a>
      <a href="#ml">ML</a>
      <a href="#drift">Drift</a>
      <a href="#limits">Limitations</a>
    </div>
  </div>

  <div class="container">
    <section class="section" id="overview">
      <h1>Conflict Situation Monitoring for Maritime Shipping</h1>
      <div class="subtitle">Correlating NASA FIRMS thermal anomalies with conflict-related news</div>
      <div class="kpi-grid">{kpi_cards}</div>
      <div class="method-note">
        <ul class="tight">
          <li>This dashboard is an early-warning monitoring tool, not a causal conflict detector.</li>
          <li>FIRMS detects thermal anomalies, not causes.</li>
          <li>Event-news association is a weak-label strategy.</li>
          <li>High recall is prioritized because missing a real conflict-related disruption is more costly than investigating a false alarm.</li>
        </ul>
      </div>
    </section>

    <section class="section" id="mapsec">
      <h2>Interactive FIRMS and Thermal Events Map</h2>
      <div id="map"></div>
      <p style="margin-top:8px;color:#4b5563;">
        {html_escape(map_status_note)}
      </p>
    </section>

    <section class="section" id="project-overview">
      <h2>Project Overview / Existing Dashboard</h2>
      {figure_html["dashboard.png"]}
      <p>Multi-panel summary of thermal events, association rates, temporal behavior, and model/drift performance.</p>
    </section>

    <section class="section" id="spatial">
      <h2>Spatial and Temporal Analysis</h2>
      <div class="fig-grid">
        {figure_html["task2_spatial_events_frp_region.png"]}
        {figure_html["task2_temporal_monthly_event_count.png"]}
      </div>
      <p>DBSCAN converts raw FIRMS pixels into interpretable thermal events. The main setting balances excessive fragmentation and over-merging.</p>
      {table_block("DBSCAN Sensitivity Summary", dbscan_tbl)}
    </section>

    <section class="section" id="association">
      <h2>Conflict Association / Regional Risk</h2>
      {figure_html["task3_association_rate_bar.png"]}
      {table_block("Control Region Diagnostics", control_tbl)}
      <p>Rub al Khali is treated as the cleaner low-conflict/control-like baseline. Sahara is treated as a mixed/stress-test region, not a clean negative control.</p>
    </section>

    <section class="section" id="ml">
      <h2>Machine Learning Performance</h2>
      <div class="fig-grid">
        {figure_html["ml_model_comparison_f1_recall_precision.png"]}
        {figure_html["ml_confusion_matrix_random_forest_tuned.png"]}
        {figure_html["ml_geography_robustness_f1_recall.png"]}
      </div>
      {table_block("ML Geography Robustness Comparison", ml_geo)}
      <p>Random Forest remains the main operational model. Full vs no-geography checks whether model skill depends only on geographic patterns. Performance drop without geography indicates geography helps, while remaining performance indicates thermal/time features still carry signal.</p>
    </section>

    <section class="section" id="drift">
      <h2>Drift Monitoring and Retraining Triggers</h2>
      <div class="fig-grid">
        {figure_html["drift_monthly_f1_recall.png"]}
        {figure_html["drift_retraining_triggers_timeline.png"]}
        {figure_html["drift_region_positive_rate_heatmap.png"]}
      </div>
      {table_block("Rows with retraining_recommended = True", drift_tr)}
      <p>This is a retraining-trigger framework, not automatic deployment. Sample-size safeguards are used to avoid unstable region-month triggers and to detect model degradation and changing conflict regimes.</p>
    </section>

    <section class="section" id="limits">
      <h2>Methodology Notes and Limitations</h2>
      <ul class="tight">
        <li>NASA FIRMS detects thermal anomalies, not conflict causes.</li>
        <li>Thermal anomalies may come from wildfire, industrial activity, agricultural burning, oil/gas flaring, or conflict events.</li>
        <li>News matching improves context but introduces media coverage bias.</li>
        <li>Article count uses log1p(n_articles) to avoid media-volume dominance.</li>
        <li>The 3-day news window is kept as a conservative matching window.</li>
        <li>The dashboard is designed for monitoring and prioritization, not final attribution.</li>
      </ul>
    </section>
  </div>

  <script>
    const firmsData = {json.dumps(firms_layer, ensure_ascii=False)};
    const eventData = {json.dumps(events_layer, ensure_ascii=False)};

    const map = L.map('map', {{ preferCanvas: true }}).setView([28, 35], 4);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }}).addTo(map);

    const firmsLayer = L.layerGroup();
    const eventsLayer = L.layerGroup();
    const assocLayer = L.layerGroup();

    firmsData.forEach(p => {{
      if (p.lat == null || p.lon == null) return;
      const popup = `
        <b>FIRMS detection</b><br/>
        Region: ${{p.region ?? 'NA'}}<br/>
        Date: ${{p.acq_date ?? 'NA'}}<br/>
        FRP: ${{p.frp ?? 'NA'}}<br/>
        Brightness: ${{p.brightness ?? 'NA'}}<br/>
        Confidence: ${{p.confidence ?? 'NA'}}
      `;
      L.circleMarker([p.lat, p.lon], {{
        radius: 2,
        color: '#6b7280',
        fillColor: '#6b7280',
        fillOpacity: 0.15,
        opacity: 0.2,
        weight: 1
      }}).bindPopup(popup).addTo(firmsLayer);
    }});

    eventData.forEach(e => {{
      if (e.lat == null || e.lon == null) return;
      const isAssoc = Number(e.conflict_associated || 0) === 1;
      const color = isAssoc ? '#c1121f' : '#1d4ed8';
      const popup = `
        <b>Thermal event</b><br/>
        Event ID: ${{e.event_id ?? 'NA'}}<br/>
        Region: ${{e.region ?? 'NA'}}<br/>
        Start: ${{e.start_date ?? 'NA'}}<br/>
        End: ${{e.end_date ?? 'NA'}}<br/>
        Duration (days): ${{e.duration_days ?? 'NA'}}<br/>
        Total FRP: ${{e.total_frp ?? 'NA'}}<br/>
        Max brightness: ${{e.max_brightness ?? 'NA'}}<br/>
        Detection points: ${{e.detection_points ?? 'NA'}}<br/>
        Event score: ${{e.event_score ?? 'NA'}}<br/>
        Conflict associated: ${{isAssoc ? 'Yes' : 'No'}}
      `;
      const marker = L.circleMarker([e.lat, e.lon], {{
        radius: Math.max(4, Math.min(14, Number(e.marker_radius || 5))),
        color: color,
        fillColor: color,
        fillOpacity: isAssoc ? 0.75 : 0.45,
        opacity: 0.95,
        weight: 1
      }}).bindPopup(popup);
      marker.addTo(eventsLayer);
      if (isAssoc) marker.addTo(assocLayer);
    }});

    // Default visibility: events visible, raw FIRMS hidden for performance.
    eventsLayer.addTo(map);

    L.control.layers(null, {{
      "FIRMS detections": firmsLayer,
      "Thermal events": eventsLayer,
      "Associated events": assocLayer
    }}, {{ collapsed: false }}).addTo(map);

    const legend = L.control({{position: 'bottomright'}});
    legend.onAdd = function() {{
      const div = L.DomUtil.create('div', 'legend-box');
      div.innerHTML = `
        <b>Legend</b><br/>
        <span style="color:#1d4ed8;">&#9679;</span> Non-associated event<br/>
        <span style="color:#c1121f;">&#9679;</span> Associated event<br/>
        <span style="color:#6b7280;">&#9679;</span> FIRMS detection (low opacity)
      `;
      return div;
    }};
    legend.addTo(map);
  </script>
</body>
</html>
"""

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    shutil.copy2(OUTPUT_HTML, LEGACY_DIR / "dashboard.html")
    shutil.copy2(OUTPUT_HTML, PACKAGE_HTML)

    missing_optional = []
    for f in PNG_FILES:
        if find_file(f) is None:
            missing_optional.append(f)
    for c in CSV_FILES:
        if safe_read_csv(c).empty:
            missing_optional.append(c)

    print("dashboard.html output path:", OUTPUT_HTML)
    print("dashboard.html package path:", PACKAGE_HTML)
    print("database available:", db_available)
    print("successfully loaded data sources:", loaded_sources)
    print("missing optional files:", missing_optional)
    print("number of FIRMS detections available:", map_meta["firms_available"])
    print("number of FIRMS detections plotted:", map_meta["firms_plotted"])
    print("whether FIRMS was sampled:", map_meta["firms_sampled"])
    print("number of thermal events plotted:", map_meta["events_plotted"])
    print("number of associated events plotted:", map_meta["associated_events_plotted"])
    print("list of PNG figures embedded:", embedded_figs)
    print("list of CSV tables embedded:", embedded_tables)


if __name__ == "__main__":
    main()
