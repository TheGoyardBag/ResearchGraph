"""Fictional scholarly records and weak, synthetic relevance judgments."""
import itertools
import numpy as np
TOPICS={
"computer vision":"image recognition visual detection segmentation cameras perception",
"robotics":"robot motion planning manipulation navigation control autonomous",
"natural language processing":"language text translation retrieval dialogue linguistics",
"machine learning systems":"neural training inference optimization accelerators deployment models",
"cybersecurity":"security privacy intrusion authentication adversarial threats",
"distributed systems":"distributed consensus replication networking databases reliability",
"bioinformatics":"genomics proteins sequences biological analysis molecular",
"climate modeling":"climate weather temperature environmental prediction simulation",
"economics":"economics markets incentives labor policy causal inference",
"human computer interaction":"interaction interfaces usability human design accessibility",
"quantum computing":"quantum qubits circuits entanglement computing algorithms",
"materials science":"materials structure chemistry polymers microscopy manufacturing"
}
def generate(seed=61):
    rng=np.random.default_rng(seed); topic_names=list(TOPICS); authors=[]; works=[]
    for i in range(120):
        authors.append({"id":f"demo:author:{i:03}","name":f"Fictional Researcher {i+1:03}","institution":f"Demo Institute {i%8+1}","source":"authored synthetic fixture"})
    for i,author in enumerate(authors):
        primary=i%12; secondary=(primary+1+(i//12)%4)%12
        for j in range(6):
            t=primary if j<4 else secondary; topics=[topic_names[t]]
            if j==3: topics.append(topic_names[secondary])
            year=int(rng.integers(2019,2026)); coauthor=(i+12)%120
            names=[author["id"]]+([authors[coauthor]["id"]] if j%3==0 else [])
            title=f"Study {i+1:03}-{j+1}: {topic_names[t]} methods"
            abstract="A fictional investigation of "+" and ".join(topics)+". "+" ".join(TOPICS[t] for t in topics)+". Methods and evaluation are illustrative, not actual publications."
            works.append({"id":f"demo:work:{i:03}-{j}","title":title,"abstract":abstract,"year":year,"authors":names,"topics":topics,"url":None,"source":"authored synthetic fixture"})
    pairs=list(itertools.combinations(topic_names,2)); rng.shuffle(pairs); queries=[]
    for i,(a,b) in enumerate(pairs):
        split="train" if i<42 else "validation" if i<54 else "test"
        for variant in range(2):
            text=f"Find research combining {a} and {b}" if variant==0 else f"Researchers with publications on {a} who also work on {b}"
            queries.append({"id":f"query-{i}-{variant}","intent":f"pair-{i}","split":split,"text":text,"target_topics":[a,b]})
    return {"authors":authors,"works":works,"topics":TOPICS,"queries":queries,"data_origin":"fully fictional"}

def relevance(corpus,query):
    """Toy labels from topic coverage. Not human expert assessments of researchers."""
    result=[]
    for author in corpus["authors"]:
        papers=[w for w in corpus["works"] if author["id"] in w["authors"]]
        counts=[sum(t in w["topics"] for w in papers) for t in query["target_topics"]]
        if min(counts)>=2: score=3
        elif min(counts)>0: score=2
        elif max(counts)>=2: score=1
        else: score=0
        result.append(score)
    return np.array(result,dtype=np.int64)
