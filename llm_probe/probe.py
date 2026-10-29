"""MemoryTrace part 3: which memory does a real local LLM rely on?

Each scenario from the benchmark becomes a short prompt with six memories
(current and verified, a stale archive, a recent unverified note, a note
without consent, a note about a different project, and a verified note that
disagrees). The model must answer the project's status in JSON and name the
memory it used, or say "unknown" or "CONFLICT". We score the memory it chose.

Prompts:
  plain  answer the question from the memories
  rule   use only memories that are verified, have consent and are at most 7 days old;
         if those disagree, answer CONFLICT

Usage (Python 3.9, standard library only; Ollama running):
    python3 llm_probe/probe.py
    python3 llm_probe/probe.py --models qwen2.5:3b --n 10
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark import generate_rows  # noqa: E402

OUT = ROOT / "outputs"
OLLAMA_URL = "http://localhost:11434/api/chat"
OUTCOMES = ("current_verified", "verified_conflict", "stale_archive", "recent_unverified",
            "restricted_note", "lexical_distractor", "flagged_conflict", "abstained", "invalid")
SYSTEM = {
    "plain": "You answer questions for a team assistant using the memories provided.",
    "rule": ("You answer questions for a team assistant using the memories provided. "
             "Use only memories that are verified, have consent to use, and are at most 7 days old. "
             "If those memories disagree, answer CONFLICT. If none qualify, answer unknown."),
}
QUESTION = {
    "en": "What is the current status of project {p}?",
    "ru": "Project {p} ka current status kya hai?",
}
FORMAT = ('Reply only with JSON: {"memory_id": "<id you used, or NONE>", '
          '"answer": "<active, paused, complete, blocked, unknown or CONFLICT>"}')

Chat = Callable[[str, str, str], str]


def ollama_chat(model: str, system: str, user: str) -> str:
    body = json.dumps({"model": model, "stream": False, "format": "json",
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                       "options": {"temperature": 0.0, "seed": 42}}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))["message"]["content"]


def build_prompt(cands: List[Dict[str, Any]], lang: str) -> Dict[str, Any]:
    project = str(cands[0]["scenario_id"]).split("-")[-1]
    lines, ids = [], {}
    for k, r in enumerate(cands, 1):
        mid = "M{}".format(k)
        ids[mid] = r["slot"]
        about = project if int(r["relevant"]) else "{:05d}".format((int(project) + 1) % 100000)
        lines.append("[{}] Project {} status: {}. Written {} days ago. Source: {}. Consent to use: {}.".format(
            mid, about, r["answer"], r["age_days"],
            "verified" if int(r["source_verified"]) else "unverified",
            "yes" if int(r["consented"]) else "no"))
    user = "Memories:\n" + "\n".join(lines) + "\n\n" + QUESTION[lang].format(p=project) + "\n" + FORMAT
    return {"user": user, "ids": ids, "gold": cands[0]["gold_answer"]}


def score(raw: str, ids: Dict[str, str]) -> Dict[str, str]:
    try:
        data = json.loads(raw)
        mid = str(data.get("memory_id", "")).strip().upper()
        ans = str(data.get("answer", "")).strip()
    except (ValueError, AttributeError):
        m = re.search(r"\bM[1-6]\b", raw or "")
        mid, ans = (m.group(0) if m else ""), ""
    if ans.upper() == "CONFLICT":
        return {"outcome": "flagged_conflict", "memory_id": mid, "answer": ans}
    if ans.lower() == "unknown" or mid in ("", "NONE"):
        return {"outcome": "abstained", "memory_id": mid, "answer": ans}
    return {"outcome": ids.get(mid, "invalid"), "memory_id": mid, "answer": ans}


def summarise(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["language"], r["prompt"])].append(r)
    out = []
    for key, g in sorted(groups.items()):
        c = Counter(r["outcome"] for r in g)
        row = {"model": key[0], "language": key[1], "prompt": key[2], "scenarios": len(g),
               "correct_answer": sum(r["correct"] for r in g)}
        row.update({o: c.get(o, 0) for o in OUTCOMES})
        out.append(row)
    return out


def main(chat: Chat = ollama_chat, argv: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["qwen2.5:3b", "llama3.1:8b"])
    ap.add_argument("--n", type=int, default=20, help="scenarios (default 20)")
    args = ap.parse_args(argv)
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in generate_rows():
        grouped[r["scenario_id"]].append(r)
    scenarios = [grouped[k] for k in sorted(grouped)][: args.n]
    OUT.mkdir(exist_ok=True)
    rows = []
    with (OUT / "llm_probe_answers.jsonl").open("w", encoding="utf-8") as fh:
        for model in args.models:
            for prompt in SYSTEM:
                for lang in ("en", "ru"):
                    for cands in scenarios:
                        p = build_prompt(cands, lang)
                        t0 = time.time()
                        raw = chat(model, SYSTEM[prompt], p["user"])
                        s = score(raw, p["ids"])
                        row = {"model": model, "prompt": prompt,
                               "language": "English" if lang == "en" else "Roman Urdu",
                               "scenario_id": cands[0]["scenario_id"], "outcome": s["outcome"],
                               "memory_id": s["memory_id"], "answer": s["answer"],
                               "correct": s["answer"].lower() == p["gold"],
                               "seconds": round(time.time() - t0, 1), "raw": (raw or "")[:300]}
                        rows.append(row)
                        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    done = [r for r in rows if r["model"] == model and r["prompt"] == prompt
                            and r["language"] == ("English" if lang == "en" else "Roman Urdu")]
                    print("{:12s} {:5s} {:10s} {}".format(model, prompt, done[0]["language"],
                                                          dict(Counter(r["outcome"] for r in done))))
    summary = summarise(rows)
    with (OUT / "llm_probe_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    print("\n" + ", ".join(summary[0].keys()))
    for s in summary:
        print(", ".join(str(v) for v in s.values()))
    print("\nSaved outputs/llm_probe_answers.jsonl and outputs/llm_probe_summary.csv")
    return rows


if __name__ == "__main__":
    main()
