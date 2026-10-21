"""Opt-in import and external-index utilities. No account access on startup."""
from __future__ import annotations
import re
from pathlib import Path
from .common import dump

def abstract_from_inverted(index):
    if not isinstance(index,dict): return ""
    positions={}
    for word,offsets in list(index.items())[:5000]:
        if not isinstance(word,str) or not isinstance(offsets,list): continue
        for pos in offsets[:2000]:
            if isinstance(pos,int) and 0<=pos<10000: positions[pos]=word[:200]
    return " ".join(positions[i] for i in sorted(positions))

def openalex_id(value,letter):
    if not isinstance(value,str): raise ValueError("Missing OpenAlex ID")
    m=re.fullmatch(r"(?:https://openalex\.org/)?("+letter+r"\d+)",value)
    if not m: raise ValueError("Invalid OpenAlex ID")
    return "https://openalex.org/"+m.group(1)

def normalize_openalex(payload,max_works=1000):
    records=payload.get("results",[]) if isinstance(payload,dict) else payload
    if not isinstance(records,list) or len(records)>max_works: raise ValueError("Expected at most 1,000 works")
    authors={}; works=[]; seen=set()
    for row in records:
        wid=openalex_id(row.get("id"),"W")
        if wid in seen: continue
        seen.add(wid); author_ids=[]
        for entry in row.get("authorships",[])[:100]:
            author=entry.get("author",{}); aid=openalex_id(author.get("id"),"A")
            institutions=[i.get("display_name","") for i in entry.get("institutions",[]) if i.get("display_name")]
            # Publication-time affiliation is not current employment or a full employment history.
            authors.setdefault(aid,{"id":aid,"name":author.get("display_name") or "Unknown author","institution":"; ".join(institutions) or "Unknown publication affiliation","source":"OpenAlex works import"})
            author_ids.append(aid)
        year=row.get("publication_year")
        if not isinstance(year,int): continue
        works.append({"id":wid,"title":row.get("display_name") or "Untitled","abstract":abstract_from_inverted(row.get("abstract_inverted_index")),"year":year,"authors":list(dict.fromkeys(author_ids)),"topics":[t["display_name"] for t in row.get("topics",[])[:10] if t.get("display_name")],"url":wid,"source":"OpenAlex works import"})
    return {"authors":list(authors.values()),"works":works,"data_origin":"OpenAlex imported metadata; verify attribution and data terms", "warning":"Normalization only. The synthetic-trained ranker is NOT validated on this corpus."}

def semantic_index(corpus,model_path,output,backend="numpy"):
    from .encoding import SentenceEncoder,CandidateIndex
    import numpy as np
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    texts=[w["title"]+" "+w["abstract"] for w in corpus["works"]]
    if not texts: raise ValueError("No works to index")
    encoder=SentenceEncoder(model_path); vectors=encoder.encode(texts)
    np.save(output/"work-vectors.npy",vectors,allow_pickle=False)
    dump(output/"works.json",corpus["works"])
    dump(output/"index-config.json",{"encoder":"sentence-transformers","model_path":str(model_path),"backend":backend,"learned_ranker":"not applied; evaluate relevance separately"})
    return CandidateIndex(vectors,backend)

def sync_neo4j(corpus,uri,user,password,namespace="researchgraph-demo"):
    from neo4j import GraphDatabase
    if not namespace or len(namespace)>80: raise ValueError("Use a nonempty namespace of at most 80 characters")
    with GraphDatabase.driver(uri,auth=(user,password)) as driver:
        driver.verify_connectivity()
        for author in corpus["authors"]:
            driver.execute_query("MERGE (a:RGAuthor {namespace:$ns, id:$id}) SET a.name=$name, a.publication_affiliation=$institution",ns=namespace,**{k:author[k] for k in ["id","name","institution"]})
        for work in corpus["works"]:
            driver.execute_query("MERGE (w:RGWork {namespace:$ns, id:$id}) SET w.title=$title, w.year=$year",ns=namespace,**{k:work[k] for k in ["id","title","year"]})
            for author in work["authors"]:
                driver.execute_query("MATCH (a:RGAuthor {namespace:$ns,id:$aid}), (w:RGWork {namespace:$ns,id:$wid}) MERGE (a)-[:AUTHORED]->(w)",ns=namespace,aid=author,wid=work["id"])
            for topic in work["topics"]:
                driver.execute_query("MATCH (w:RGWork {namespace:$ns,id:$wid}) MERGE (t:RGTopic {namespace:$ns,name:$topic}) MERGE (w)-[:HAS_TOPIC]->(t)",ns=namespace,wid=work["id"],topic=topic)
    return {"authors":len(corpus["authors"]),"works":len(corpus["works"]),"namespace":namespace,"mode":"idempotent merge; no delete operations"}
