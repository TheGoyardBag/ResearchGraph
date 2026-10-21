# Security and deployment boundaries

This application is a local, single-operator portfolio prototype. It binds to
loopback by default. All data and write APIs require a bearer token generated
by `setup`; health and static UI are public. Tokens are kept in a file excluded
from Git; the browser holds a token only for the current session. There is no
account management, tenant isolation, SSO, TLS termination, or production SLA.
Do not publish the server directly on the internet. A reverse proxy must enforce
TLS, real authentication, request-body limits and rate limiting before deployment.

SQLite operations are parameterized. Reviews are append-only. User text is rendered
with textContent, never as HTML. Third-party content is data, not authority.
Artifacts are loaded only from a configured, trusted local directory. PyTorch uses
weights_only=True. SHA256 manifests catch accidental corruption, not malicious
replacement of both model and manifest. Do not load untrusted checkpoints.

The code makes no paid model calls and provisions no cloud resources by default.
External integrations are opt-in, use environment variables for credentials,
and are separately documented. Never put API keys or real sensitive data in Git.
Imported data may have different privacy, consent and licensing requirements.
Review the dependency versions and supply-chain risks before public deployment.

The request Content-Length guard is advisory; it does not replace an ingress
byte limit for chunked requests. Individual input fields also have length bounds.
