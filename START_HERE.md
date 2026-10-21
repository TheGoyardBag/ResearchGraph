# Start here — ResearchGraph

1. Read the README's status and limitations.
2. Create and activate a Python virtual environment.
3. Run `python -m pip install -e ".[dev]"`.
4. Run `python -m researchgraph setup` and copy the printed local token.
5. Run `python -m researchgraph serve`.
6. Open `http://127.0.0.1:8105`, paste the token and click Connect.
7. Try `python -m researchgraph demo` and `python -m pytest -q`.

The demo works with included weights; retraining is optional. The training data
is synthetic, and optional integration dependencies are separate from the default
workflow. This repository is independent of the other four projects.
