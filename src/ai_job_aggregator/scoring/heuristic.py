from __future__ import annotations

import re

from ai_job_aggregator.schemas.scoring import ScoreResult


def _norm_skill(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _haystack(*parts: str | None) -> str:
    return "\n".join([p for p in parts if p]).lower()


def score_job(
    *,
    profile_skills: list[str],
    job_title: str | None,
    company: str | None,
    url: str | None,
    raw: dict,
) -> ScoreResult:
    """Heuristic scorer.

    Uses profile skills and a text blob built from job fields + raw JSON.
    """

    skills = [_norm_skill(s) for s in profile_skills if s and s.strip()]
    skills = list(dict.fromkeys(skills))  # stable unique

    raw_text = str(raw) if raw is not None else ""
    blob = _haystack(job_title, company, url, raw_text)

    matched: list[str] = []
    missing: list[str] = []

    for sk in skills:
        if sk and sk in blob:
            matched.append(sk)
        else:
            missing.append(sk)

    ratio = (len(matched) / len(skills)) if skills else 0.0
    base = ratio * 100.0

    # Small qualitative signals; keep simple + explainable.
    bonus = 0.0
    if job_title:
        t = job_title.lower()
        if any(k in t for k in ["senior", "lead", "staff", "principal"]):
            bonus -= 5.0
        if any(k in t for k in ["junior", "intern"]):
            bonus += 2.0

    score = max(0.0, min(100.0, base + bonus))

    reasons = {
        "match_ratio": ratio,
        "counts": {"skills_total": len(skills), "matched": len(matched), "missing": len(missing)},
        "signals": {"title": job_title, "company": company},
    }

    return ScoreResult(score=score, skills_matched=matched, skills_missing=missing, reasons=reasons)
