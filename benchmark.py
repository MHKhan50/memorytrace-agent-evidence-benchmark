"""MemoryTrace synthetic benchmark; Python standard library only."""
from __future__ import annotations
import csv, json, random
from collections import defaultdict
from pathlib import Path

ANSWERS = ["active", "paused", "complete", "blocked"]
POLICIES = ("keyword_only", "latest_relevant", "provenance_gate", "strict_evidence")
MAX_AGE_DAYS = 7
STRICT_MIN_QUALITY = 0.72

def generate_rows(n_scenarios=600, seed=20261028):
    rng = random.Random(seed)
    rows = []
    for i in range(n_scenarios):
        sid = f"MT-{seed}-{i:05d}"
        query_day = rng.randint(60, 180)
        gold = rng.choice(ANSWERS)
        wrong = [a for a in ANSWERS if a != gold]
        stale_answer = rng.choice(wrong)
        unverified_answer = rng.choice(wrong)
        unconsented_answer = rng.choice(ANSWERS)
        # Candidate mix intentionally includes realistic failure modes.
        candidates = [
            dict(slot="current_verified", answer=gold, age=rng.randint(0, 2),
                 relevant=True, verified=rng.random() < .82, consented=rng.random() < .96,
                 quality=round(rng.uniform(.68, .99), 3), lexical=round(rng.uniform(.48, .78), 3),
                 validity=10),
            dict(slot="stale_archive", answer=stale_answer, age=rng.randint(8, 35),
                 relevant=True, verified=rng.random() < .95, consented=True,
                 quality=round(rng.uniform(.72, .98), 3), lexical=round(rng.uniform(.65, .95), 3),
                 validity=7),
            dict(slot="recent_unverified", answer=unverified_answer, age=rng.randint(0, 2),
                 relevant=True, verified=False, consented=True,
                 quality=round(rng.uniform(.15, .58), 3), lexical=round(rng.uniform(.72, .99), 3),
                 validity=30),
            dict(slot="restricted_note", answer=unconsented_answer, age=rng.randint(0, 3),
                 relevant=True, verified=True, consented=False,
                 quality=round(rng.uniform(.65, .95), 3), lexical=round(rng.uniform(.52, .90), 3),
                 validity=30),
            dict(slot="lexical_distractor", answer=rng.choice(ANSWERS), age=rng.randint(0, 2),
                 relevant=False, verified=rng.random() < .5, consented=True,
                 quality=round(rng.uniform(.3, .9), 3), lexical=round(rng.uniform(.82, 1.0), 3),
                 validity=30),
            # A source can be authentic and permitted yet still contain a conflicting/incorrect claim.
            dict(slot="verified_conflict", answer=rng.choice(wrong), age=rng.randint(0, 3),
                 relevant=True, verified=True, consented=True,
                 quality=round(rng.uniform(.70, .98), 3), lexical=round(rng.uniform(.48, .82), 3),
                 validity=10),
        ]
        rng.shuffle(candidates)
        for j, c in enumerate(candidates):
            rows.append({
                "scenario_id": sid, "query_day": query_day,
                "query": f"What is the current status of project {i:05d}?",
                "gold_answer": gold, "memory_id": f"{sid}-C{j}",
                "slot": c["slot"], "answer": c["answer"], "age_days": c["age"],
                "relevant": int(c["relevant"]), "source_verified": int(c["verified"]),
                "consented": int(c["consented"]), "evidence_quality": c["quality"],
                "lexical_match": c["lexical"], "validity_days": c["validity"],
            })
    return rows

def _is_current(row):
    return int(row["age_days"]) <= min(MAX_AGE_DAYS, int(row["validity_days"]))

def select_candidate(candidates, policy):
    if policy == "keyword_only":
        pool = candidates
        key = lambda r: (float(r["lexical_match"]), int(r["source_verified"]), -int(r["age_days"]))
    elif policy == "latest_relevant":
        pool = [r for r in candidates if int(r["relevant"])]
        key = lambda r: (-int(r["age_days"]), float(r["lexical_match"]))
    elif policy in ("provenance_gate", "strict_evidence"):
        pool = [r for r in candidates
                if int(r["relevant"]) and int(r["source_verified"]) and int(r["consented"]) and _is_current(r)]
        if policy == "strict_evidence":
            pool = [r for r in pool if float(r["evidence_quality"]) >= STRICT_MIN_QUALITY]
        key = lambda r: (float(r["evidence_quality"]) * .65 + float(r["lexical_match"]) * .35,
                         -int(r["age_days"]))
    else:
        raise ValueError(f"Unknown policy: {policy}")
    if not pool:
        return None
    return max(pool, key=key)

def evaluate(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["scenario_id"]].append(row)
    decisions = []
    for sid, candidates in sorted(grouped.items()):
        gold = candidates[0]["gold_answer"]
        for policy in POLICIES:
            selected = select_candidate(candidates, policy)
            answered = selected is not None
            correct = bool(answered and selected["answer"] == gold)
            decisions.append({
                "scenario_id": sid, "policy": policy,
                "answered": int(answered), "correct": int(correct),
                "answer": selected["answer"] if answered else "",
                "selected_memory_id": selected["memory_id"] if answered else "",
                "selected_verified": int(selected["source_verified"]) if answered else 0,
                "selected_consented": int(selected["consented"]) if answered else 1,
                "selected_age_days": int(selected["age_days"]) if answered else "",
                "selected_stale": int(not _is_current(selected)) if answered else 0,
                "selected_quality": selected["evidence_quality"] if answered else "",
            })
    return decisions

def summarize(decisions):
    by_policy = defaultdict(list)
    for d in decisions:
        by_policy[d["policy"]].append(d)
    out = []
    for policy in POLICIES:
        ds = by_policy[policy]
        n = len(ds)
        answered = [d for d in ds if d["answered"]]
        na = len(answered)
        out.append({
            "policy": policy,
            "scenarios": n,
            "coverage": round(na / n if n else 0, 4),
            "accuracy_among_answered": round(sum(d["correct"] for d in answered) / na if na else 0, 4),
            "correct_rate_all_scenarios": round(sum(d["correct"] for d in ds) / n if n else 0, 4),
            "stale_selection_rate": round(sum(d["selected_stale"] for d in ds) / n if n else 0, 4),
            "unsupported_selection_rate": round(sum(d["answered"] and not d["selected_verified"] for d in ds) / n if n else 0, 4),
            "nonconsensual_selection_rate": round(sum(d["answered"] and not d["selected_consented"] for d in ds) / n if n else 0, 4),
        })
    return out

def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def run(n_scenarios=600, seed=20261028, root=None):
    root = Path(root or Path(__file__).resolve().parent)
    data = root / "data" / "scenarios.csv"
    outdir = root / "outputs"
    rows = generate_rows(n_scenarios, seed)
    write_csv(data, rows)
    decisions = evaluate(rows)
    summary = summarize(decisions)
    write_csv(outdir / "episode_results.csv", decisions)
    write_csv(outdir / "summary.csv", summary)
    (outdir / "summary.json").write_text(json.dumps({
        "benchmark": "MemoryTrace", "seed": seed, "n_scenarios": n_scenarios,
        "candidate_rows": len(rows), "policy_rows": len(decisions),
        "results": summary,
        "interpretation_warning": "Synthetic simulation only; not a real LLM or production-agent evaluation."
    }, indent=2) + "\n", encoding="utf-8")
    return summary
