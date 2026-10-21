# API reference

Base URL: `http://127.0.0.1:8105`. All `/api/` requests need the local bearer token.

| Method | Path | Request / behavior |
|---|---|---|
| GET | `/api/catalog` | `Fictional corpus metadata.` |
| POST | `/api/search` | `{"query":"computer vision and robotics","k":10,"min_year":2023}` |
| GET | `/api/graph/demo:author:000` | `An author-publication-topic neighborhood.` |
| POST | `/api/review/EVENT_ID` | `{"decision":"unsure","note":"Check supporting work"}` |
| GET | `/api/history` | `Saved searches and ranked results.` |
| GET | `/api/metrics` | Saved model evaluation JSON. |

Pydantic rejects invalid types, unsupported enum choices and out-of-range fields. A missing token returns 401; an uninitialized server returns 503 for protected routes. `GET /openapi.json` provides machine-readable request schemas. The public Swagger UI is disabled because the application uses a self-only content security policy.

```python
import requests
response = requests.get(
    "http://127.0.0.1:8105/api/metrics",
    headers={"Authorization": "Bearer YOUR_LOCAL_TOKEN"},
    timeout=30,
)
response.raise_for_status()
print(response.json())
```