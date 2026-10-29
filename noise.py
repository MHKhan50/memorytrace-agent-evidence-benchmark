"""MemoryTrace part 2: conflicts and noisy labels (Python 3.9+).

Two problems with the base benchmark:

1. The gates are tested with perfect labels. A real system has to decide
   whether a source is verified, consented and current, and those labels can
   be wrong. Here each label is flipped with probability e, the gate decides on
   the noisy labels, and we score on the true labels.
2. In most scenarios the gate's pool still holds two verified, consented,
   current memories that disagree. Picking one by score is then a guess.
   `conflict_abstain` answers only when every memory left in the pool agrees.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List

from benchmark import MAX_AGE_DAYS, select_candidate

NOISE_LEVELS = (0.0, 0.05, 0.1, 0.2)
POLICIES = ("provenance_gate", "strict_evidence", "conflict_abstain")


def _current(r: Dict[str, object]) -> bool:
    return int(r["age_days"]) <= min(MAX_AGE_DAYS, int(r["validity_days"]))


def add_noise(candidates: List[Dict[str, object]], e: float) -> List[Dict[str, object]]:
    """Flip source_verified, consented and the current/expired status, each with probability e.

    The draw is fixed per memory, so a higher e only adds flips.
    """
    out = []
    for r in candidates:
        rng = random.Random("noise-" + str(r["memory_id"]))
        n = dict(r)
        if rng.random() < e:
            n["source_verified"] = 1 - int(r["source_verified"])
        if rng.random() < e:
            n["consented"] = 1 - int(r["consented"])
        if rng.random() < e:
            n["age_days"] = 0 if not _current(r) else MAX_AGE_DAYS + 30
        out.append(n)
    return out


def gate_pool(candidates: List[Dict[str, object]]) -> List[Dict[str, object]]:
    return [r for r in candidates
            if int(r["relevant"]) and int(r["source_verified"]) and int(r["consented"]) and _current(r)]


def choose(candidates: List[Dict[str, object]], policy: str):
    if policy == "conflict_abstain":
        pool = gate_pool(candidates)
        if not pool or len({r["answer"] for r in pool}) > 1:
            return None
        return pool[0]
    return select_candidate(candidates, policy)


def sweep(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for r in rows:
        grouped[str(r["scenario_id"])].append(r)
    truth = {str(r["memory_id"]): r for r in rows}
    out = []
    for e in NOISE_LEVELS:
        for policy in POLICIES:
            n = answered = correct = wrong = unsupported = nonconsensual = stale = conflict = 0
            for cands in grouped.values():
                noisy = add_noise(cands, e)
                n += 1
                if len({r["answer"] for r in gate_pool(noisy)}) > 1:
                    conflict += 1
                pick = choose(noisy, policy)
                if pick is None:
                    continue
                t = truth[str(pick["memory_id"])]
                answered += 1
                ok = t["answer"] == t["gold_answer"]
                correct += ok
                wrong += not ok
                unsupported += not int(t["source_verified"])
                nonconsensual += not int(t["consented"])
                stale += not _current(t)
            out.append({
                "label_noise": e, "policy": policy, "scenarios": n,
                "coverage": round(answered / n, 4),
                "correct_rate": round(correct / n, 4),
                "wrong_answer_rate": round(wrong / n, 4),
                "unsupported_rate": round(unsupported / n, 4),
                "nonconsensual_rate": round(nonconsensual / n, 4),
                "stale_rate": round(stale / n, 4),
                "conflicting_pool_rate": round(conflict / n, 4),
            })
    return out
