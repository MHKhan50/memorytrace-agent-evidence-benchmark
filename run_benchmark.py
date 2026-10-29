#!/usr/bin/env python3
import argparse
from benchmark import generate_rows, run, write_csv
from noise import sweep
from plot_results import create_chart, create_noise_chart
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
noise = sweep(generate_rows(args.n, args.seed))
write_csv("outputs/noise_sweep.csv", noise)
create_chart()
create_noise_chart()
print("\nConflicts and noisy labels (rates over all scenarios)")
for r in noise:
    print(f"noise={r['label_noise']:.2f} {r['policy']:17s} coverage={r['coverage']:.3f} correct={r['correct_rate']:.3f} "
          f"wrong={r['wrong_answer_rate']:.3f} unsupported={r['unsupported_rate']:.3f} "
          f"nonconsensual={r['nonconsensual_rate']:.3f} stale={r['stale_rate']:.3f} conflict_pool={r['conflicting_pool_rate']:.3f}")
print("Wrote outputs/noise_sweep.csv and outputs/noise_effects.svg")
