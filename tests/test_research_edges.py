import pytest
from researchgraph.integrations import abstract_from_inverted,normalize_openalex
from researchgraph.service import ResearchSearch
from researchgraph.encoding import LocalEncoder

def test_malformed_abstract_safe():
    assert abstract_from_inverted(None)==""
    assert abstract_from_inverted({"ok":[0,-1,999999],"bad":"oops"})=="ok"
def test_import_limit():
    with pytest.raises(ValueError): normalize_openalex([{}]*1001)
def test_invalid_payload():
    with pytest.raises(ValueError): normalize_openalex({"results":"wrong"})
def test_encoder_save_load_roundtrip(tmp_path):
    e=LocalEncoder().fit(["robotics vision methods", "language processing models", "privacy security methods"],dimensions=2)
    e.save(tmp_path); loaded=LocalEncoder.restore(tmp_path)
    import numpy as np
    assert np.allclose(e.encode(["robotics"]),loaded.encode(["robotics"]))
@pytest.mark.parametrize("args",[{"query":" "},{"query":"x","k":0},{"query":"x","institution":"unknown"},{"query":"vision","mode":"unknown"}])
def test_bad_search_arguments(args):
    with pytest.raises(ValueError): ResearchSearch().search(**args)
def test_year_with_no_evidence_returns_empty(): assert ResearchSearch().search("vision",min_year=2026)["results"]==[]
