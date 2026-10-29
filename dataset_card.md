# Dataset card: MemoryTrace Synthetic Candidate Memories

- **Dataset name:** MemoryTrace Synthetic Candidate Memories
- **Version:** 1.1.0
- **Generation:** `benchmark.generate_rows(n_scenarios, seed)`; default 600 scenarios × 6 candidates = 3,600 rows.
- **Content:** Synthetic query IDs, categorical project-status answers, age, relevance, source-verification flag, consent flag, evidence-quality score, lexical-match score, and validity period, and a verified-but-conflicting candidate.
- **Personal data:** None intended; no real people, accounts, documents, or user logs.
- **Source:** Generated entirely by this repository; no third-party dataset is bundled.
- **Licence:** CC BY 4.0 for generated CSV data; code is MIT-licensed.
- **Intended use:** Reproducible experiments on memory retrieval policy trade-offs.
- **Out-of-scope use:** Production security/privacy assurance, measuring real user preferences, or claims about a particular LLM.
- **Known limitations:** Hand-designed distributions; labels are oracle values; no natural-language retrieval model; no missing/forged metadata in the default condition; the verified-but-conflicting candidate tests that source authenticity does not guarantee factual correctness; synthetic categorical answers are not representative of real research facts.
- **Reproduction:** `python3 generate_dataset.py --n 600 --seed 20261028`.
- **Citation:** Cite the GitHub repository and exact release/commit actually used. Do not claim a DOI unless a deposit has been completed.
