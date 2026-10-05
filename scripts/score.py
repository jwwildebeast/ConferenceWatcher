"""Reputation scoring, 0-100, always with an auditable signal breakdown.

Two paths:
  - "computed" (aggregator-sourced): derived from CORE/CCF rank (primary) and
    h-index (secondary). Formula and weights are intentionally simple and
    documented here rather than tuned -- the point is transparency, not
    precision.
  - "manual" (seed-sourced, e.g. IISE/MARCON): your own manual_base_score is
    the value of record; we only add a small, capped bonus for how long the
    conference has run. Never overridden by a formula.
"""

CORE_RANK_SCORE = {"A*": 100, "A": 85, "B": 65, "C": 45}
CCF_RANK_SCORE = {"A": 95, "B": 75, "C": 55}
UNRANKED_BASE = 30
RANK_WEIGHT = 0.7
HINDEX_WEIGHT = 0.3
HINDEX_CEILING = 300  # h-index values are clamped here before normalizing to 0-100

MANUAL_YEARS_BONUS_CAP = 5
MANUAL_YEARS_BONUS_DIVISOR = 10  # +1 point per 10 years running, capped


def _clamp(x: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, x))


def score_computed(record: dict) -> dict:
    rankings = record.get("rankings") or {}
    core_rank = rankings.get("core")
    ccf_rank = rankings.get("ccf")

    if core_rank in CORE_RANK_SCORE:
        base = CORE_RANK_SCORE[core_rank]
    elif ccf_rank in CCF_RANK_SCORE:
        base = CCF_RANK_SCORE[ccf_rank]
    else:
        base = UNRANKED_BASE

    hindex = record.get("hindex") or 0
    hindex_norm = _clamp(hindex, 0, HINDEX_CEILING) / HINDEX_CEILING * 100

    score = round(RANK_WEIGHT * base + HINDEX_WEIGHT * hindex_norm)
    return {
        "score": int(_clamp(score)),
        "basis": "computed",
        "signals": {
            "core_rank": core_rank,
            "ccf_rank": ccf_rank,
            "rank_base_score": base,
            "hindex": hindex,
            "hindex_normalized": round(hindex_norm, 1),
        },
    }


def score_manual(record: dict) -> dict:
    base = record.get("manual_base_score")
    if base is None:
        base = UNRANKED_BASE
    years = record.get("years_running") or 0
    years_bonus = min(years // MANUAL_YEARS_BONUS_DIVISOR, MANUAL_YEARS_BONUS_CAP)
    score = round(_clamp(base + years_bonus))
    return {
        "score": int(score),
        "basis": "manual",
        "signals": {
            "manual_base_score": base,
            "years_running": years,
            "years_bonus": years_bonus,
            "rationale": record.get("score_rationale"),
        },
    }


def score_record(record: dict) -> dict:
    if record.get("basis") == "manual":
        return score_manual(record)
    return score_computed(record)


def apply_scores(records: list[dict]) -> None:
    """Mutates each record in place, adding a `reputation` field."""
    for record in records:
        record["reputation"] = score_record(record)
