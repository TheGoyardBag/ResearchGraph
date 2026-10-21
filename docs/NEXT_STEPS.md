# Next experiments

Collect consent-appropriate, domain-expert relevance labels; evaluate a real scholarly corpus; validate source freshness and affiliation interpretation; benchmark pretrained retrieval, hybrid keyword retrieval and graph signals; audit popularity bias; and keep contact enrichment separate from scholarly relevance.

Before expanding infrastructure, reproduce the baseline and identify which failure
modes actually matter. Keep data collection, model changes and UI changes in separate
commits. Record rejected approaches and negative results, not just best-case demos.

## Before a public deployment
Add individual identities and authorization, TLS, durable external storage, reverse
proxy request limits, rate limiting, operational monitoring, an appropriate secrets
manager, dependency scanning, a recovery procedure, and realistic load tests.
