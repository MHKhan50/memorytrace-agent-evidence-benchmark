#!/usr/bin/env python3
import argparse
from benchmark import run
p = argparse.ArgumentParser(description="Run the MemoryTrace synthetic benchmark")
p.add_argument("--n", type=int, default=600, help="number of scenarios (default: 600)")
p.add_argument("--seed", type=int, default=20261028)
args = p.parse_args()
if args.n < 1:
    p.error("--n must be >= 1")
summary = run(args.n, args.seed)
print(f"MemoryTrace: {args.n} scenarios; {args.n * 6} candidate rows; {args.n * 4} policy decisions")
print("Synthetic results (rates are proportions):")
for row in summary:
    print(f"{row['policy']:18s} coverage={row['coverage']:.3f} "
          f"correct_all={row['correct_rate_all_scenarios']:.3f} "
          f"stale={row['stale_selection_rate']:.3f} "
          f"unsupported={row['unsupported_selection_rate']:.3f} "
          f"nonconsensual={row['nonconsensual_selection_rate']:.3f}")
print("Wrote data/scenarios.csv and outputs/{episode_results.csv,summary.csv,summary.json}")
