import numpy as np
import pytest
from fastapi.testclient import TestClient
from researchgraph.data import generate,relevance
from researchgraph.model import ndcg
from researchgraph.service import ResearchSearch
from researchgraph.common import Settings
from researchgraph.api import create_app
from researchgraph.integrations import normalize_openalex,abstract_from_inverted,openalex_id
@pytest.fixture(scope="module")
def search(): return ResearchSearch()
@pytest.fixture
def client(tmp_path): return TestClient(create_app(Settings(tmp_path,"test-token")))
H={"Authorization":"Bearer test-token"}
def test_intent_split():
    c=generate(); groups={s:{q["intent"] for q in c["queries"] if q["split"]==s} for s in ["train","validation","test"]}
    assert not groups["train"]&groups["test"] and not groups["train"]&groups["validation"]
def test_graph_integrity(search):
    g=search.graph; assert all(a in g.author_lookup for w in g.works for a in w["authors"])
    assert len(g.graph)>len(g.authors)+len(g.works)
def test_ndcg(): assert ndcg([3,2,0],[0,1,2])==1
@pytest.mark.parametrize("mode",["hybrid_pairwise_ranker","lexical_svd_only","graph_neighbor_only"])
def test_search_evidence(search,mode):
    r=search.search("robotics and computer vision",mode=mode,k=5)
    assert len(r["results"])==5
    for a in r["results"]:
        assert not a["score_is_probability"] and a["evidence"]
        assert all(a["id"] in w["authors"] for w in a["evidence"])
def test_institution_filter(search):
    r=search.search("robotics",institution="Demo Institute 2")
    assert all(a["institution"]=="Demo Institute 2" for a in r["results"])
def test_year_filter(search):
    r=search.search("robotics",min_year=2025)
    assert all(w["year"]>=2025 for a in r["results"] for w in a["evidence"])
def test_unknown_vocabulary(search): assert search.search("zxqvnmblrr") ["results"]==[]
def test_neighborhood(search):
    g=search.graph.neighborhood("demo:author:000"); ids={r["id"] for r in g["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in g["edges"])
def test_abstract_positions(): assert abstract_from_inverted({"world":[1],"hello":[0]})=="hello world"
def test_import():
    row={"id":"https://openalex.org/W123","display_name":"Example","publication_year":2023,"authorships":[{"author":{"id":"https://openalex.org/A42","display_name":"A"},"institutions":[{"display_name":"Institute"}]}],"topics":[{"display_name":"ML"}]}
    c=normalize_openalex({"results":[row,row]}); assert len(c["works"])==1 and c["authors"][0]["id"].endswith("A42")
@pytest.mark.parametrize("bad",["http://evil.test/W1","../../token","https://openalex.org/A1"])
def test_id_validation(bad):
    with pytest.raises(ValueError): openalex_id(bad,"W")
def test_api(client):
    assert client.get("/api/catalog").status_code==401
    r=client.post("/api/search",json={"query":"vision robotics"},headers=H)
    assert r.status_code==200 and r.json()["results"]
    aid=r.json()["results"][0]["id"]
    assert client.get("/api/graph/"+aid,headers=H).status_code==200
    assert client.post("/api/review/"+r.json()["id"],json={"decision":"unsure"},headers=H).status_code==200
