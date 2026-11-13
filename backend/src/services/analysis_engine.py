import itertools
import math
from datetime import datetime, timedelta, timezone

import numpy as np
from scipy import stats
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer


def _metric(label, value, unit="", tone="neutral"):
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    return {"label": label, "value": value, "unit": unit, "tone": tone}


def _series(label, value):
    return {"label": str(label), "value": float(value)}


def _envelope(headline, narrative, metrics, series, table, method, caveat):
    return {
        "headline": headline,
        "narrative": narrative,
        "metrics": metrics,
        "series": series,
        "table": table,
        "method": method,
        "caveat": caveat,
    }


def run_primary(rows: list[dict], config: dict) -> dict:
    cohorts = sorted({str(row.get("cohort", "2026-01")) for row in rows})
    periods = sorted({int(row.get("period", 0)) for row in rows})
    matrix = []
    for cohort in cohorts:
        row_map = {int(item.get("period", 0)): item for item in rows if str(item.get("cohort")) == cohort}
        base = float(row_map.get(0, {}).get("at_risk", 1))
        matrix.append({"label": cohort, "values": [
            round(float(row_map.get(period, {}).get("retained", 0)) / max(base, 1) * 100, 2)
            if period in row_map else 0 for period in periods
        ]})
    survival = 1.0
    curve = []
    for period in periods:
        at_risk = sum(float(row.get("at_risk", 0)) for row in rows if int(row.get("period", 0)) == period)
        retained = sum(float(row.get("retained", 0)) for row in rows if int(row.get("period", 0)) == period)
        events = max(at_risk - retained, 0)
        if at_risk > 0:
            survival *= 1 - events / at_risk
        curve.append({"label": f"P{period}", "value": round(survival * 100, 2)})
    latest_period = max(periods)
    latest = np.mean([item["values"][periods.index(latest_period)] for item in matrix])
    return _envelope(
        f"P{latest_period} 平均留存 {latest:.1f}%",
        f"共 {len(cohorts)} 个注册队列；Kaplan-Meier 用于处理尚未观察到的删失。",
        [
            _metric("队列数", len(cohorts), "个", "neutral"),
            _metric("最新留存", latest, "%", "positive" if latest > 30 else "neutral"),
            _metric("观察周期", len(periods), "期", "neutral"),
            _metric("生存概率", curve[-1]["value"], "%", "neutral"),
        ],
        curve,
        [{"label": item["label"], **{f"P{periods[i]}": value for i, value in enumerate(item["values"])}}
         for item in matrix],
        "cohort_matrix + kaplan_meier",
        "不同渠道获得用户的观察窗不一致；营销活动期需要单独标注。",
    )



def run_algorithm(rows: list[dict], config: dict) -> dict:
    return run_primary(rows or [], config or {})
