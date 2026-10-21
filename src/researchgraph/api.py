import os
from pathlib import Path
from typing import Literal
from fastapi import FastAPI,Depends,HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field,ConfigDict
from .common import Settings,Store,authorization,security_headers,load
from .service import ResearchSearch
class Query(BaseModel):
    model_config=ConfigDict(extra="forbid")
    query:str=Field(min_length=1,max_length=1000)
    k:int=Field(default=10,ge=1,le=25)
    min_year:int=Field(default=2019,ge=2019,le=2026)
    institution:str|None=Field(default=None,max_length=150)
    mode:Literal["hybrid_pairwise_ranker","lexical_svd_only","graph_neighbor_only"]="hybrid_pairwise_ranker"
class Review(BaseModel):
    decision:Literal["correct","incorrect","unsure"]
    note:str=Field(default="",max_length=2000)
def create_app(settings=None):
    settings=settings or Settings.environment(); app=FastAPI(title="ResearchGraph",version="0.1.0",docs_url=None,redoc_url=None); app.middleware("http")(security_headers)
    auth=authorization(settings); service=ResearchSearch(settings.artifacts,os.getenv("VECTOR_BACKEND","numpy")); store=Store(settings.state)
    static=Path(__file__).parent/"static"; app.mount("/static",StaticFiles(directory=static),name="static")
    @app.get("/")
    def index(): return FileResponse(static/"index.html")
    @app.get("/health")
    def health(): return {"status":"ok","encoder":"tfidf_svd","corpus":"fictional"}
    @app.get("/api/metrics",dependencies=[Depends(auth)])
    def metrics(): return load(settings.artifacts/"metrics.json")
    @app.get("/api/catalog",dependencies=[Depends(auth)])
    def catalog(): return {"institutions":sorted({a["institution"] for a in service.corpus["authors"]}),"topics":list(service.corpus["topics"]),"authors":len(service.corpus["authors"]),"works":len(service.corpus["works"])}
    @app.post("/api/search",dependencies=[Depends(auth)])
    def search(req:Query):
        try: result=service.search(**req.model_dump())
        except ValueError as exc: raise HTTPException(422,str(exc))
        key=store.add("search",result); return {"id":key,**result}
    @app.get("/api/graph/{author_id}",dependencies=[Depends(auth)])
    def graph(author_id:str):
        try: return service.graph.neighborhood(author_id)
        except KeyError: raise HTTPException(404,"Author not found")
    @app.post("/api/review/{key}",dependencies=[Depends(auth)])
    def review(key:str,body:Review):
        try: store.review(key,body.decision,body.note)
        except KeyError: raise HTTPException(404,"Search not found")
        return {"status":"recorded"}
    @app.get("/api/history",dependencies=[Depends(auth)])
    def history(): return store.list("search")
    return app
