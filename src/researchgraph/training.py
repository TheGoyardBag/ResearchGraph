from __future__ import annotations
import copy,time
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from .common import ASSETS,dump,manifest
from .data import generate,relevance
from .encoding import LocalEncoder
from .graph import ScholarlyGraph
from .model import RelevanceRanker,ndcg

def train(output=None,epochs=50):
    start=time.perf_counter(); torch.set_num_threads(2); torch.manual_seed(61); rng=np.random.default_rng(61)
    folder=output or ASSETS/"artifacts"; folder.mkdir(parents=True,exist_ok=True)
    corpus=generate(); encoder=LocalEncoder().fit([w["title"]+" "+w["abstract"] for w in corpus["works"]]); graph=ScholarlyGraph(corpus,encoder)
    queries=corpus["queries"]; features=np.array([graph.features(q["text"])[0] for q in queries]); labels=np.array([relevance(corpus,q) for q in queries])
    split={s:np.array([i for i,q in enumerate(queries) if q["split"]==s]) for s in ["train","validation","test"]}; tr,va,te=(split[s] for s in ["train","validation","test"])
    scaler=StandardScaler().fit(features[tr].reshape(-1,7)); scaled=scaler.transform(features.reshape(-1,7)).reshape(features.shape); x=torch.tensor(scaled,dtype=torch.float32)
    pairs=[]
    for qi in tr:
        eligible=[(a,b) for a in range(120) for b in range(120) if labels[qi,a]>labels[qi,b]]
        for choice in rng.choice(len(eligible),size=min(80,len(eligible)),replace=False):
            a,b=eligible[choice]; pairs.append((qi,a,b))
    pairs=np.asarray(pairs); model=RelevanceRanker(); opt=torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=.01)
    best=None; best_ndcg=-1; history=[]
    for epoch in range(epochs):
        model.train(); losses=[]
        for batch in np.array_split(rng.permutation(len(pairs)),max(1,len(pairs)//256)):
            q,a,b=pairs[batch].T; opt.zero_grad(); diff=model(x[q,a])-model(x[q,b]); loss=torch.nn.functional.softplus(-diff).mean(); loss.backward(); opt.step(); losses.append(float(loss.detach()))
        model.eval()
        with torch.inference_mode(): scores=model(x[va]).numpy()
        metric=float(np.mean([ndcg(labels[qi],np.argsort(-score)) for qi,score in zip(va,scores)]))
        history.append({"epoch":epoch+1,"pairwise_loss":float(np.mean(losses)),"validation_ndcg@10":metric})
        if metric>best_ndcg: best_ndcg=metric; best=copy.deepcopy(model.state_dict())
    model.load_state_dict(best); model.eval()
    with torch.inference_mode(): all_scores=model(x).numpy()
    results={}
    for split_name,ix in [("validation",va),("test",te)]:
        modes={"lexical_svd_only":features[ix,:,0],"graph_neighbor_only":features[ix,:,4],"hybrid_pairwise_ranker":all_scores[ix]}
        values={}
        for name,score_rows in modes.items():
            vals=[]; candidate_recall=[]
            for qi,score in zip(ix,score_rows):
                # Match service behavior: retrieve top 40 author vectors before learned reranking.
                candidates=np.argsort(-features[qi,:,0],kind="stable")[:40]
                ranked=candidates[np.argsort(-score[candidates],kind="stable")]
                vals.append(ndcg(labels[qi],ranked))
                rel=set(np.flatnonzero(labels[qi]>=2)); candidate_recall.append(len(rel&set(candidates))/max(len(rel),1))
            values[name]={"ndcg@10":float(np.mean(vals)),"candidate_recall_grade2@40":float(np.mean(candidate_recall)),"queries":len(ix)}
        results[split_name]=values
    encoder.save(folder); torch.save(model.state_dict(),folder/"model.pt"); dump(folder/"corpus.json",corpus); dump(folder/"history.json",history)
    dump(folder/"config.json",{"seed":61,"mean":scaler.mean_,"scale":scaler.scale_,"feature_names":["author_similarity","best_work_similarity","top3_work_similarity","recent_work_similarity","coauthor_support","fraction_relevant_works","best_work_recency"],"encoder":"tfidf_svd (not pretrained)","selected_by":"validation NDCG@10","candidates":40})
    result={"data":"120 fictional researchers, 720 fictional works, 132 queries; labels derived from fixture topics","splits":{s:len(ix) for s,ix in split.items()},"evaluation":"Unseen topic-pair intents; paraphrases stay together. Transductive fixed-catalog ranking, not new-author generalization.","results":results,"training_seconds":time.perf_counter()-start,"limitations":["Synthetic labels are not human relevance judgments", "Default TF-IDF/SVD is lexical latent retrieval, not Sentence Transformers", "No employment history, availability, contact details or protected-attribute inference", "Ranking score is not a confidence or compatibility probability"]}
    dump(folder/"metrics.json",result); manifest(folder); return result
