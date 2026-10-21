"""Explicit offline TF-IDF/SVD vectors. These are NOT pretrained sentence embeddings."""
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer,TfidfTransformer
from sklearn.decomposition import TruncatedSVD
from .common import dump,load

def normalize(x): return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
class LocalEncoder:
    def fit(self,texts,dimensions=64):
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=4000,sublinear_tf=True)
        matrix=self.vectorizer.fit_transform(texts)
        reducer=TruncatedSVD(n_components=min(dimensions,matrix.shape[0]-1,matrix.shape[1]-1),random_state=61)
        reducer.fit(matrix); self.components=reducer.components_.astype(np.float32)
        return self
    def encode(self,texts):
        return normalize(np.asarray(self.vectorizer.transform(texts)@self.components.T,dtype=np.float32))
    def save(self,folder):
        dump(folder/"encoder.json",{"vocabulary":self.vectorizer.vocabulary_,"idf":self.vectorizer.idf_,"kind":"tfidf_svd","pretrained":False})
        np.save(folder/"components.npy",self.components,allow_pickle=False)
    @classmethod
    def restore(cls,folder):
        state=load(folder/"encoder.json"); obj=cls(); obj.vectorizer=TfidfVectorizer(ngram_range=(1,2),vocabulary=state["vocabulary"],sublinear_tf=True)
        obj.vectorizer.vocabulary_=state["vocabulary"]; obj.vectorizer.fixed_vocabulary_=True
        obj.vectorizer._tfidf=TfidfTransformer(); obj.vectorizer._tfidf.idf_=np.asarray(state["idf"])
        obj.components=np.load(folder/"components.npy",allow_pickle=False); return obj

class SentenceEncoder:
    def __init__(self,local_model_path):
        from sentence_transformers import SentenceTransformer
        self.model=SentenceTransformer(str(local_model_path),local_files_only=True,trust_remote_code=False)
    def encode(self,texts):
        return self.model.encode(texts,normalize_embeddings=True,convert_to_numpy=True).astype(np.float32)

class CandidateIndex:
    def __init__(self,vectors,backend="numpy"):
        self.vectors=normalize(np.asarray(vectors,dtype=np.float32)); self.backend=backend
        if backend=="faiss":
            import faiss
            self.index=faiss.IndexFlatIP(self.vectors.shape[1]); self.index.add(self.vectors)
        elif backend!="numpy": raise ValueError("Unknown vector backend")
    def search(self,vector,k=40):
        q=normalize(np.asarray(vector,dtype=np.float32).reshape(1,-1))
        if not np.isfinite(q).all() or q.shape[1]!=self.vectors.shape[1]: raise ValueError("Invalid query vector")
        if k<1: raise ValueError("k must be positive")
        if self.backend=="faiss": return self.index.search(q,min(k,len(self.vectors)))[1][0].tolist()
        return np.argsort(-(self.vectors@q[0]),kind="stable")[:k].tolist()
