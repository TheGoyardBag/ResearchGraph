import numpy as np
import torch
from torch import nn
class RelevanceRanker(nn.Module):
    def __init__(self,features=7):
        super().__init__(); self.net=nn.Sequential(nn.Linear(features,24),nn.Tanh(),nn.Linear(24,12),nn.Tanh(),nn.Linear(12,1))
    def forward(self,x): return self.net(x).squeeze(-1)

def ndcg(labels,ranking,k=10):
    grades=np.asarray(labels); ranking=np.asarray(ranking,dtype=int)[:k]; discounts=1/np.log2(np.arange(2,len(ranking)+2))
    dcg=((2.**grades[ranking]-1)*discounts).sum()
    ideal=np.sort(grades)[::-1][:k]; idcg=((2.**ideal-1)/np.log2(np.arange(2,len(ideal)+2))).sum()
    return float(dcg/max(idcg,1e-12))
