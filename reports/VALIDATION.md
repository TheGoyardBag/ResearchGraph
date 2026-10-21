# ResearchGraph — validation report

## Executed checks

| Check | Result |
|---|---|
| Python tests | 43 passed; 0 skipped |
| Measured Python statement coverage | 74.5% |
| JavaScript unit tests | 6 passed |
| Browser interaction checks | 11 passed |
| Model training | Executed locally on CPU; weights and metrics included |
| Editable installation | Verified with --no-deps --no-build-isolation, using installed runtime dependencies |
| Fresh archive test run | Passed: Python tests, JS tests, setup and command-line demo |

Coverage is the result of the pytest run, not a claim that every training or optional
integration path is unit-tested. The training scripts were separately executed.
See `tests.xml`, `coverage.json`, `browser.json`, `environment.json` and `metrics.json`.

## Browser test method

The repository's actual HTML, CSS and JavaScript were exercised in Chromium with
Playwright. The environment blocks browser navigation to local URLs. The harness
therefore loads the UI into a local DOM, uses a fetch bridge to an actual running
Uvicorn HTTP backend, and emulates sessionStorage for the opaque origin. It performs
real inference requests, writes and reloads local feedback, and checks desktop/mobile
horizontal overflow. JavaScript module syntax is separately imported by the Node tests.

This does **not** validate native browser ESM transport, browser CSP enforcement,
network authentication boundaries, a public deployment or a production reverse proxy.
No UI data or model responses were fabricated by the test harness.

## Not executed / not claimed

- A clean online dependency resolver install, Docker image build or cloud deployment.
- Remote GitHub Actions execution or publication to a GitHub account.
- Real-world accuracy, production performance, business savings or security guarantees.
- Optional external dependencies/services that are unavailable in this environment.

The exact integration boundaries are in the README and model card. The default
workflow is offline. Included metrics are from authored synthetic data, not a public
benchmark or customer data. `constraints-tested.txt` lists direct package versions;
it is not a complete dependency lock.
