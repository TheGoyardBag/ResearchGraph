# ResearchGraph: model card

## Intended use
Search for research expertise, rank candidate researchers, inspect the publications supporting a match, and browse a small research graph.

## Model and training
An unsupervised TF-IDF/SVD encoder is fitted on publication text, not query labels. Candidate features measure author-text similarity, strongest/recent paper support, coauthor support and recency. A small neural ranker learns pairwise preferences using only training queries; validation NDCG selects its checkpoint. Service results retrieve up to 40 candidates before reranking and expose original evidence records. Metadata constraints qualify authors before candidate truncation.

## Dataset and partitioning
120 fictional researchers, 720 fictional works and 132 query paraphrases. Topic-pair intents, rather than individual paraphrases, are split into training/validation/test (84/24/24 queries). Relevance grades are weak labels derived from fixture topic coverage; they are not judgments by domain experts. The fixed publication corpus is visible at indexing time; this is transductive retrieval, not new-author generalization.

## Evaluation
NDCG@10 against the synthetic relevance judgments and grade≥2 candidate Recall@40, compared with lexical/SVD-only and coauthor-graph baselines. Relative model scores are not confidence, suitability or compatibility probabilities.

Metrics are recorded in `reports/metrics.json` and in the artifact directory.
Full epoch histories are in `src/researchgraph/assets/artifacts/history.json`.
The model checkpoint and artifact files have SHA256 checksums in `manifest.json`.
Checkpoint loading uses `torch.load(..., weights_only=True)` and evaluation mode.

## Limitations and out-of-scope use
Default vectors are local TF-IDF/SVD, not pretrained semantic embeddings. All demonstration people and papers are fictional. This repository does not claim verified current employment, complete employment history, researcher availability, contact information or hiring suitability. It does not replace the user’s existing people-discovery startup or prescribe changes to that system.

## Model selection vs test evaluation
All learned preprocessing, training weights and decision thresholds are selected
before test reporting. Validation is used for checkpoint/model/threshold selection
where stated; test metrics must not be used to tune the model and still described
as an untouched test. Synthetic tests should be replaced with a locked, realistic
evaluation before making real-world performance claims.

## Updating the model
Run training with the server stopped, inspect the new report, keep a record of the
previous model, and restart the service. There is no automatic online retraining,
promotion gate, drift-monitoring service or rollback deployment controller.
