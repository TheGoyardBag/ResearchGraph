"""Normalize a saved OpenAlex works API response. This command makes no API calls."""
import argparse,json
from pathlib import Path
from researchgraph.integrations import normalize_openalex
from researchgraph.common import dump
p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("output",type=Path)
a=p.parse_args()
if a.input.stat().st_size>20_000_000: p.error("Input exceeds 20 MB")
result=normalize_openalex(json.loads(a.input.read_text())); dump(a.output,result)
print(f"Normalized {len(result['works'])} works. This does not retrain or validate the ranker.")
