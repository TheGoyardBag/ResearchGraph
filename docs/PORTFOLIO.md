# Portfolio use

## Accurate current description

**ResearchGraph — Evidence-Linked Researcher Discovery** — Developed an evidence-linked researcher discovery workbench using Python, PyTorch, NetworkX, and FastAPI, combining vector retrieval, coauthor relationships, and pairwise relevance learning with publication-level explanations.

This wording describes the implemented local workflow. Only claim technologies you
have personally run and understood. Do not list optional external integrations as
verified production experience. Do not claim these projects were delivered during
an earlier internship or for real customers.

## What to demonstrate
Open the dashboard, run one example, inspect the result, compare a baseline and
explain a failure case. Show the training script, partition tests, persisted state,
API validation and model/data cards. Explain why the reported metric is appropriate
and why synthetic performance does not establish deployment readiness.

## Interview questions to prepare
- Which component actually learns, and which is deterministic application logic?
- What data could leak the answer, and how did the partition tests prevent it?
- What did the simple baseline do better, and what would you change next?
- What happens to invalid input, stale state and unavailable optional services?
- What would need to change before the application could serve real users safely?

## Original plan vs delivered implementation
Default technologies: Python, PyTorch, scikit-learn, NetworkX, NumPy, FastAPI, SQLite, HTML/CSS/JavaScript.

`scripts/import_openalex.py` normalizes a locally saved works API response without network calls. `integrations.semantic_index` builds a separate Sentence Transformers index from a trusted local model. `VECTOR_BACKEND=faiss` enables exact FAISS retrieval for the demo. `sync_neo4j` uses parameterized, namespaced upserts. Sentence Transformers, FAISS and Neo4j runtimes were not live-tested. The synthetic-trained reranker is not automatically applied to imported real profiles.

Default vectors are local TF-IDF/SVD, not pretrained semantic embeddings. All demonstration people and papers are fictional. This repository does not claim verified current employment, complete employment history, researcher availability, contact information or hiring suitability. It does not replace the user’s existing people-discovery startup or prescribe changes to that system.
