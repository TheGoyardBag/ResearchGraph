import numpy as np
import pytest
from researchgraph.common import Store, Settings, dump, load, manifest, verify, jsonable
def test_store_roundtrip(tmp_path):
    db=Store(tmp_path); key=db.add("unit",{"x":1})
    assert db.get(key)["payload"]=={"x":1}
    assert db.list("unit")[0]["id"]==key
def test_review_requires_existing_event(tmp_path):
    with pytest.raises(KeyError): Store(tmp_path).review("missing","correct","")
@pytest.mark.parametrize("decision",["correct","incorrect","unsure"])
def test_append_review(tmp_path,decision):
    db=Store(tmp_path); key=db.add("run",{}); db.review(key,decision,"note")
    with db.connect() as con: assert con.execute("SELECT count(*) FROM reviews").fetchone()[0]==1
def test_review_validation(tmp_path):
    with pytest.raises(ValueError): Store(tmp_path).review("x","other","")
def test_setup_is_idempotent(tmp_path):
    s=Settings(tmp_path,""); assert s.initialize()==s.initialize(); assert len(s.initialize())>=32
def test_checksum_rejects_corruption(tmp_path):
    dump(tmp_path/"a.json",{"a":1}); manifest(tmp_path); verify(tmp_path)
    (tmp_path/"a.json").write_text("bad")
    with pytest.raises(ValueError): verify(tmp_path)
def test_json_handles_numpy_and_nan(tmp_path):
    dump(tmp_path/"a.json",{"x":np.array([1,2]),"missing":float("nan")})
    assert load(tmp_path/"a.json")=={"x":[1,2],"missing":None}
def test_store_sql_parameterization(tmp_path):
    s=Store(tmp_path); s.add("' OR 1=1 --",{"text":"<script>"})
    assert len(s.list("' OR 1=1 --"))==1
    assert s.list("not-found")==[]


def test_long_review_rejected(tmp_path):
    with pytest.raises(ValueError): Store(tmp_path).review("x","correct","x"*2001)

def test_connection_closed_after_context(tmp_path):
    import sqlite3
    store=Store(tmp_path)
    with store.connect() as db: db.execute("SELECT 1")
    with pytest.raises(sqlite3.ProgrammingError): db.execute("SELECT 1")

def test_manifest_missing_fails_closed(tmp_path):
    with pytest.raises(ValueError): verify(tmp_path)

def test_manifest_rejects_path_traversal(tmp_path):
    dump(tmp_path/"manifest.json",{"../outside":"fakehash"})
    with pytest.raises(ValueError): verify(tmp_path)

def test_environment_token_precedence(tmp_path,monkeypatch):
    monkeypatch.setenv("APP_STATE_DIR",str(tmp_path)); Settings(tmp_path,"").initialize()
    monkeypatch.setenv("APP_TOKEN","explicit-token")
    assert Settings.environment().token=="explicit-token"
    assert Settings.environment().initialize()=="explicit-token"

def test_api_security_headers(tmp_path):
    from fastapi.testclient import TestClient
    from researchgraph.api import create_app
    with TestClient(create_app(Settings(tmp_path,"token"))) as client:
        response=client.get("/health")
        assert response.headers["x-content-type-options"]=="nosniff"
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert response.headers["cache-control"]=="no-store"
        assert client.get("/api/metrics",headers={"Authorization":"Bearer wrong"}).status_code==401

def test_api_missing_token_fails_closed(tmp_path):
    from fastapi.testclient import TestClient
    from researchgraph.api import create_app
    with TestClient(create_app(Settings(tmp_path,""))) as client:
        assert client.get("/api/metrics").status_code==503

def test_artifact_metrics_match_manifest():
    from researchgraph.common import ASSETS
    verify(ASSETS/"artifacts")
