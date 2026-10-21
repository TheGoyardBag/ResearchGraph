# ResearchGraph: architecture

```text
Browser dashboard (HTML/CSS/JavaScript)
      | bearer-authenticated JSON / optional bounded image upload
FastAPI route validation
      |                        |
Product service          SQLite history / feedback
      |
Trusted artifact loader + SHA256 integrity checks
      |
Learned model + task-specific baseline / policy / ranking
      |
Structured evidence and measured outputs → browser
```

## Product behavior
Search for research expertise, rank candidate researchers, inspect the publications supporting a match, and browse a small research graph.

## Learned component
An unsupervised TF-IDF/SVD encoder is fitted on publication text, not query labels. Candidate features measure author-text similarity, strongest/recent paper support, coauthor support and recency. A small neural ranker learns pairwise preferences using only training queries; validation NDCG selects its checkpoint. Service results retrieve up to 40 candidates before reranking and expose original evidence records. Metadata constraints qualify authors before candidate truncation.

## Offline experiment vs application state
Model assets are immutable while the application is running. Application state is
stored separately under `APP_STATE_DIR` (default `var/`). No training labels are
accepted as inference features. Human feedback is recorded separately; it does not
silently become training data or alter model weights. A future training workflow
must version and validate any newly collected labels.

## Deployment scope
The service is synchronous CPU inference and a single local operator, not a
horizontally scaled, multi-tenant SaaS. SQLite writes use parameterized transactions.
API and model errors fail visibly. Optional dependencies are imported lazily;
explicitly requesting a missing external backend does not silently switch modes.

## Integration scope
`scripts/import_openalex.py` normalizes a locally saved works API response without network calls. `integrations.semantic_index` builds a separate Sentence Transformers index from a trusted local model. `VECTOR_BACKEND=faiss` enables exact FAISS retrieval for the demo. `sync_neo4j` uses parameterized, namespaced upserts. Sentence Transformers, FAISS and Neo4j runtimes were not live-tested. The synthetic-trained reranker is not automatically applied to imported real profiles.

## Design tradeoffs
A small real model and inspectable baseline make the full workflow reproducible
without a GPU or external account. Plain JavaScript keeps the dashboard executable
without a Node build. These choices favor transparent experiments over framework
count. Scaling, SSO, cloud provisioning and production observability are not claimed.
