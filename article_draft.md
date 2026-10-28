# MemoryTrace: Measuring Evidence-Aware Memory Retrieval in Agentic Workflows

## Abstract

Agentic assistants may retrieve stored notes while answering a current query. A note can be topically relevant yet stale, weakly sourced, or retained without the user's permission. MemoryTrace is a lightweight synthetic benchmark that compares four retrieval policies under controlled combinations of relevance, freshness, provenance, and consent. It reports answer coverage and correctness alongside stale, unsupported, and non-consensual selections. The package is intended as a reproducible test harness rather than a claim about production agents.

## Research question

How much do provenance, freshness, and consent gates change the trade-off between answer coverage and unsafe memory use in a multi-step assistant workflow?

## Method

A deterministic generator creates scenarios with a known current answer and six candidate memory records: a potentially verified current record, a stale archive, a recent unverified record, a non-consensual note, a lexical distractor, and an authentic but conflicting record. Four policies select a candidate or abstain. The benchmark computes per-scenario decisions and aggregate rates using only the Python standard library.

## Results

For the bundled default run (600 scenarios; seed 20261028), the generated summary was:

| Policy | Coverage | Correct rate over all scenarios | Stale selections | Unsupported selections | Non-consensual selections |
|---|---:|---:|---:|---:|---:|
| `keyword_only` | 1.0000 | 0.1617 | 0.1017 | 0.5650 | 0.0167 |
| `latest_relevant` | 1.0000 | 0.2133 | 0.0000 | 0.5217 | 0.1700 |
| `provenance_gate` | 1.0000 | 0.3717 | 0.0000 | 0.0000 | 0.0000 |
| `strict_evidence` | 0.9683 | 0.3600 | 0.0000 | 0.0000 | 0.0000 |

These are deterministic outputs of this synthetic simulator, not estimates of real-world agent performance. The policy gates have access to simulator labels, so the zero-risk rates are a property of the experiment design, not evidence that a deployed system would achieve zero risk. Independently rerun the experiment and verify `outputs/summary.csv` before publishing.

## Interpretation and limitations

The simulator makes evidence and consent labels available to the policy; real systems must infer provenance and enforce access controls through external mechanisms. It also includes a verified-but-conflicting record to show that source authenticity does not guarantee claim correctness. A synthetic retrieval score is not an LLM's semantic understanding. The generated distribution is hand-designed and may favour policies whose assumptions match it. Results do not establish safety, privacy compliance, or generalisation to real users. A follow-up study should test multiple LLMs, preregister scenario families, report uncertainty intervals, and include adversarial cases where metadata are missing or forged.

## Reproducibility

The project uses Python's standard library, deterministic seeds, generated data, unit tests, CSV/JSON outputs, and an SVG plotting script. No user data or external corpus is used.

## Research context

The topic is motivated by current UK research activity in privacy-aware AI agents, LLM memorisation risk, and secure agent execution. These pages establish research interest, not proof that this particular benchmark is novel:
- Brunel University of London, “AI Agents for Privacy-Aware Web Interactions” (accessed 28 October 2026).
- University of Southampton, “Mitigating memorisation risks in Large Language Models” (project page lists a 31 December 2027 closing date; check current status before acting).
- University of Surrey, “Surrey leads £3.2m project … to develop provably secure sandbox for AI agents” (15 October 2026).

## Conclusion

MemoryTrace offers a small, auditable baseline for studying whether evidence-aware retrieval reduces stale or unsupported memory use, and what coverage it sacrifices. Any claim about real agent behaviour requires a separate empirical evaluation with real models and clearly documented protocols.
