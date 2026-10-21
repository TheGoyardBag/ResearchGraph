from __future__ import annotations
import numpy as np
import torch
from .common import ASSETS,load,verify
from .encoding import LocalEncoder,CandidateIndex
from .graph import ScholarlyGraph
from .model import RelevanceRanker
class ResearchSearch:
    def __init__(self,folder=ASSETS/"artifacts",backend="numpy"):
        verify(folder); torch.set_num_threads(2); self.corpus=load(folder/"corpus.json"); self.config=load(folder/"config.json")
        self.encoder=LocalEncoder.restore(folder); self.graph=ScholarlyGraph(self.corpus,self.encoder); self.index=CandidateIndex(self.graph.author_vectors,backend)
        self.ranker=RelevanceRanker(); self.ranker.load_state_dict(torch.load(folder/"model.pt",map_location="cpu",weights_only=True)); self.ranker.eval()
    def search(self,query,k=10,min_year=2019,institution=None,mode="hybrid_pairwise_ranker"):
        if not isinstance(query,str) or not query.strip() or len(query)>1000: raise ValueError("Query must contain 1–1,000 characters")
        if not 1<=k<=25 or not 2019<=min_year<=2026: raise ValueError("Invalid count or year")
        institutions={a["institution"] for a in self.corpus["authors"]}
        if institution is not None and institution not in institutions: raise ValueError("Unknown institution")
        features,work_scores,q=self.graph.features(query)
        if float(np.linalg.norm(q))<1e-8: return {"results":[],"mode":mode,"warning":"No vocabulary overlap with the demonstration corpus.","encoder":"tfidf_svd"}
        # Filter before top-k retrieval so a small allowed subset is not lost after truncation.
        candidates=[i for i in self.index.search(q,120) if (institution is None or self.corpus["authors"][i]["institution"]==institution) and any(self.corpus["works"][j]["year"]>=min_year for j in self.graph.author_works[i])][:40]
        if mode=="hybrid_pairwise_ranker":
            values=(features-np.asarray(self.config["mean"]))/np.asarray(self.config["scale"])
            with torch.inference_mode(): scores=self.ranker(torch.tensor(values,dtype=torch.float32)).numpy()
        elif mode=="lexical_svd_only": scores=features[:,0]
        elif mode=="graph_neighbor_only": scores=features[:,4]
        else: raise ValueError("Unknown ranking mode")
        ordered=sorted(candidates,key=lambda i:float(scores[i]),reverse=True)[:k]; results=[]
        for i in ordered:
            evidence=self.graph.evidence(i,work_scores,min_year)
            if not evidence: continue
            results.append({**self.corpus["authors"][i],"ranking_score":float(scores[i]),"score_is_probability":False,"evidence":evidence,"features":{key:float(val) for key,val in zip(self.config["feature_names"],features[i])},"explanation":"Ranked using publication text and coauthor support; inspect the cited fixture works."})
        return {"query":query,"results":results,"mode":mode,"encoder":"tfidf_svd","retrieval_backend":self.index.backend,"warning":"All researchers and publications in this demo are fictional. This is research relevance, not a hiring recommendation or a verified biography."}

def demo(): return ResearchSearch().search("computer vision and robotics",k=3)
