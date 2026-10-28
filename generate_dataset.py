"""Regenerate the synthetic candidate-level dataset without evaluating policies."""
import argparse
from benchmark import generate_rows, write_csv
p = argparse.ArgumentParser()
p.add_argument("--n", type=int, default=600)
p.add_argument("--seed", type=int, default=20261028)
a = p.parse_args()
if a.n < 1:
    p.error("--n must be >= 1")
write_csv("data/scenarios.csv", generate_rows(a.n, a.seed))
print(f"Wrote {a.n * 6} synthetic candidate rows to data/scenarios.csv")
