# MemoryTrace: which memory should an AI assistant trust?

**Area:** agentic AI, agent memory, evidence and consent
**Version:** 1.1.0 (29 October 2026)
**Runs on:** Python 3.9+, standard library only. Part 3 needs Ollama with `qwen2.5:3b` and `llama3.1:8b`.

## Research questions
1. Retrieval gates (verified source, consent, not expired) remove unsafe memories when their labels are perfect. How much unsafe memory gets through when the labels are sometimes wrong, and how many wrong answers remain?
2. When a real local LLM reads six memories about the same project, which one does it rely on, and does a short rule in the prompt make it skip stale, unverified or non-consented memories, in English and Roman Urdu?

## What is in the repository
| Part | File | What it measures |
|---|---|---|
| 1. Base policies | `benchmark.py` | Four retrieval policies on 600 synthetic questions, 6 candidate memories each (3,600 rows). |
| 2. Conflicts and noisy labels | `noise.py` | The two gates, plus `conflict_abstain` (answer only if the remaining memories agree), with each label flipped at 0%, 5%, 10% and 20%. Scored on the true labels. |
| 3. Real agents | `llm_probe/` | 20 of the scenarios as text prompts. The model names the memory it used, or says unknown or CONFLICT. Two prompts (`plain`, `rule`), English and Roman Urdu questions. |

Part 1 is a sanity check: the gates filter on exactly the labels used to score them, so with perfect labels their unsafe-memory rates are 0% by construction.

**A design finding from part 2:** in the base data the correct memory is never the only one that passes the gate. In about 80% of questions a verified, consented, current memory with a different answer passes too, and in the rest the correct memory is unverified and only the wrong one passes. So the base accuracy (about 37%) comes from a tie-break on the quality score, not from the gate. `conflict_abstain` makes this visible.

## Run
```bash
python3 run_benchmark.py                 # parts 1 and 2 (seconds)
python3 -m unittest discover -s tests -v # offline tests, no model needed
python3 llm_probe/probe.py               # part 3: 160 prompts with two local models (Ollama running)
```

## Results
From my run on a MacBook M4 (16 GB). Parts 1 and 2 are deterministic; part 3 is one run at temperature 0 on 20 scenarios per row. "Unsafe memory used" adds unverified, non-consented and stale picks, scored on the true labels.

### Part 2: conflicts and noisy labels
| Label error | Policy | Coverage | Wrong answers | Unsafe memory used |
|---|---|---|---|---|
| 0% | `provenance_gate` | 100.0% | 62.8% | 0.0% |
| 0% | `strict_evidence` | 96.8% | 60.8% | 0.0% |
| 0% | `conflict_abstain` | 19.8% | 19.8% | 0.0% |
| 5% | `provenance_gate` | 96.3% | 59.5% | 5.0% |
| 5% | `strict_evidence` | 91.2% | 56.7% | 4.8% |
| 5% | `conflict_abstain` | 31.7% | 23.8% | 1.2% |
| 10% | `provenance_gate` | 91.5% | 56.2% | 9.5% |
| 10% | `strict_evidence` | 85.5% | 53.0% | 8.2% |
| 10% | `conflict_abstain` | 38.3% | 25.2% | 3.0% |
| 20% | `provenance_gate` | 81.7% | 49.2% | 21.3% |
| 20% | `strict_evidence` | 73.0% | 44.3% | 17.8% |
| 20% | `conflict_abstain` | 43.8% | 27.8% | 10.5% |

![Effect of label errors](outputs/noise_effects.svg)

### Part 3: which memory the models used
| Model | Language | Prompt | Current verified | Verified conflict | Stale | Unverified | No consent | Other project | CONFLICT | Unknown |
|---|---|---|---|---|---|---|---|---|---|---|
| llama3.1:8b | English | plain | 11 | 6 | 0 | 1 | 2 | 0 | 0 | 0 |
| llama3.1:8b | English | rule | 12 | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| llama3.1:8b | Roman Urdu | plain | 9 | 6 | 0 | 2 | 3 | 0 | 0 | 0 |
| llama3.1:8b | Roman Urdu | rule | 11 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen2.5:3b | English | plain | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| qwen2.5:3b | English | rule | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |
| qwen2.5:3b | Roman Urdu | plain | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 19 |
| qwen2.5:3b | Roman Urdu | rule | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 16 |

`qwen2.5:3b` also gave a few answers that could not be scored (an id that was not in the list); see `outputs/llm_probe_summary.csv`.

## My notes
- With the rule in the prompt, `llama3.1:8b` stopped using unverified and non-consented memories (3 to 0 in English, 5 to 0 in Roman Urdu). But it could not spot verified memories that disagree, and picked them more often: 6 to 8 in English and 6 to 9 in Roman Urdu. No model said CONFLICT even once, so this check belongs in code, like `conflict_abstain`, not in the model.
- In the simulator, with 20% of labels wrong, unsafe memory got past the gate in about 21% of questions. `conflict_abstain` held it to about 10%, but answered only 44% of questions.
- `qwen2.5:3b` never picked a stale or wrong memory, but it answered "unknown" in 71 of 80 questions across both languages. It looks safe on the risk metrics, but it is not useful.

## Article
[Labels go wrong, and models do not say CONFLICT](https://masmatixinnovations.co.uk/insights/memorytrace-agent-evidence-benchmark.html)

## Limitations
- Parts 1 and 2 are a simulator with hand-set distributions; labels are flipped independently, while real label errors are often correlated.
- Answers are four status words, so a wrong memory can still give the right word by chance; part 3 scores the memory the model names, not only the word.
- Part 3 uses 20 scenarios, two small local models, one run at temperature 0, and memories written as structured lines rather than natural notes.
- No real people, projects or records are involved.

## Related work
- Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS 2020*.
- Packer, C. et al. (2023). MemGPT: towards LLMs as operating systems. arXiv:2310.08560.
- See also [`memtrust-agent-memory-benchmark/`](https://github.com/MHKhan50/agentic-ai-research-log/tree/main/memtrust-agent-memory-benchmark) in my research log (planted memories and a trust filter).

## Licence
Code: MIT (`LICENSE`). Generated data: CC BY 4.0 (`dataset_card.md`).
