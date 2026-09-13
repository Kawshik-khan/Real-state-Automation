"""Deterministic Evaluation Metrics & Statistical Aggregators."""

from __future__ import annotations

import math
from typing import Any, Sequence


def calculate_classification_metrics(predictions: Sequence[str], targets: Sequence[str]) -> dict[str, float]:
    """Calculate accuracy, macro precision, recall, and F1 score."""
    if not predictions or len(predictions) != len(targets):
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    total = len(targets)
    correct = sum(1 for p, t in zip(predictions, targets) if p.lower() == t.lower())
    accuracy = correct / total if total > 0 else 0.0

    # Collect unique classes
    classes = set(t.lower() for t in targets)
    precisions, recalls, f1s = [], [], []

    for c in classes:
        tp = sum(1 for p, t in zip(predictions, targets) if p.lower() == c and t.lower() == c)
        fp = sum(1 for p, t in zip(predictions, targets) if p.lower() == c and t.lower() != c)
        fn = sum(1 for p, t in zip(predictions, targets) if p.lower() != c and t.lower() == c)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    macro_precision = sum(precisions) / len(precisions) if precisions else 0.0
    macro_recall = sum(recalls) / len(recalls) if recalls else 0.0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(macro_precision, 4),
        "recall": round(macro_recall, 4),
        "f1": round(macro_f1, 4),
    }


def calculate_latency_percentiles(latencies_ms: Sequence[float]) -> dict[str, float]:
    """Calculate p50, p90, p95, p99, and mean latency in milliseconds."""
    if not latencies_ms:
        return {"mean_ms": 0.0, "p50_ms": 0.0, "p90_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}

    sorted_l = sorted(latencies_ms)
    n = len(sorted_l)

    def percentile(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_l[int(k)]
        d0 = sorted_l[int(f)] * (c - k)
        d1 = sorted_l[int(c)] * (k - f)
        return d0 + d1

    return {
        "mean_ms": round(sum(sorted_l) / n, 2),
        "p50_ms": round(percentile(50), 2),
        "p90_ms": round(percentile(90), 2),
        "p95_ms": round(percentile(95), 2),
        "p99_ms": round(percentile(99), 2),
    }


def verify_numeric_exactness(
    property_price: float,
    down_payment_pct: float,
    tenure_months: int,
    candidate_down_payment: float,
    candidate_monthly_installment: float,
) -> dict[str, Any]:
    """Verify candidate financial installment calculation against exact arithmetic oracle."""
    expected_down = (down_payment_pct / 100.0) * property_price
    remaining = property_price - expected_down
    expected_monthly = remaining / float(tenure_months) if tenure_months > 0 else 0.0

    down_exact = math.isclose(candidate_down_payment, expected_down, rel_tol=1e-4)
    monthly_exact = math.isclose(candidate_monthly_installment, expected_monthly, rel_tol=1e-4)

    return {
        "is_exact": down_exact and monthly_exact,
        "expected_down_payment": expected_down,
        "actual_down_payment": candidate_down_payment,
        "expected_monthly": expected_monthly,
        "actual_monthly": candidate_monthly_installment,
    }
