from __future__ import annotations
import numpy as np
import networkx as nx
class ScholarlyGraph:
    def __init__(self,corpus,encoder):
        self.corpus=corpus; self.encoder=encoder; self.authors=corpus["authors"]; self.works=corpus["works"]
        self.author_lookup={a["id"]:i for i,a in enumerate(self.authors)}; self.graph=nx.Graph(); self.author_works=[[] for _ in self.authors]
        for a in self.authors:
            self.graph.add_node(a["id"],kind="author",label=a["name"])
            ins="institution:"+a["institution"]; self.graph.add_node(ins,kind="institution",label=a["institution"]); self.graph.add_edge(a["id"],ins,relation="affiliated_in_fixture")
        for j,w in enumerate(self.works):
            self.graph.add_node(w["id"],kind="work",label=w["title"])
            for a in w["authors"]:
                if a in self.author_lookup:
                    self.graph.add_edge(a,w["id"],relation="authored"); self.author_works[self.author_lookup[a]].append(j)
            for topic in w["topics"]:
                tid="topic:"+topic; self.graph.add_node(tid,kind="topic",label=topic); self.graph.add_edge(w["id"],tid,relation="has_topic")
        work_text=[w["title"]+" "+w["abstract"] for w in self.works]
        self.work_vectors=encoder.encode(work_text)
        self.author_vectors=encoder.encode([" ".join(work_text[j] for j in indexes) for indexes in self.author_works])
        self.coauthors=[]
        for i,a in enumerate(self.authors):
            peers={self.author_lookup[x] for j in self.author_works[i] for x in self.works[j]["authors"] if x in self.author_lookup and x!=a["id"]}
            self.coauthors.append(sorted(peers))
    def features(self,query):
        q=self.encoder.encode([query])[0]; author_sim=self.author_vectors@q; work_sim=self.work_vectors@q
        result=[]
        for i,indexes in enumerate(self.author_works):
            scores=np.asarray([work_sim[j] for j in indexes]); order=np.argsort(-scores); best=indexes[int(order[0])]
            recent=[work_sim[j] for j in indexes if self.works[j]["year"]>=2023]
            peers=self.coauthors[i]; peer=float(np.mean(np.sort(author_sim[peers])[-3:])) if peers else 0
            # Purely observational features; neither query labels nor latent target topics are inputs.
            result.append([author_sim[i],float(scores.max()),float(np.mean(np.sort(scores)[-3:])),float(max(recent,default=0)),peer,float(sum(scores>.15)/max(len(scores),1)),(self.works[best]["year"]-2019)/6])
        return np.asarray(result,np.float32),work_sim,q
    def evidence(self,index,work_sim,min_year=2019,k=3):
        candidates=[j for j in self.author_works[index] if self.works[j]["year"]>=min_year]
        candidates=sorted(candidates,key=lambda j:float(work_sim[j]),reverse=True)[:k]
        return [{**self.works[j],"retrieval_score":float(work_sim[j])} for j in candidates]
    def neighborhood(self,author_id,limit=24):
        if author_id not in self.author_lookup: raise KeyError(author_id)
        nodes={author_id}; nodes.update(list(self.graph.neighbors(author_id))[:limit])
        for node in list(nodes):
            if self.graph.nodes[node]["kind"]=="work":
                for neighbor in self.graph.neighbors(node):
                    if len(nodes)<limit: nodes.add(neighbor)
        sub=self.graph.subgraph(nodes)
        return {"nodes":[{"id":k,**v} for k,v in sub.nodes(data=True)],"edges":[{"source":a,"target":b,**v} for a,b,v in sub.edges(data=True)]}
