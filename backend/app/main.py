from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import faiss, numpy as np, json, pandas as pd
import os

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
VEC_PATH   = os.path.join(DATA_DIR, "item_vectors.npy")
IDS_PATH   = os.path.join(DATA_DIR, "item_ids.json")
CATALOG    = os.path.join(DATA_DIR, "catalog.csv")

app = FastAPI(title="Clozyt Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

index = faiss.read_index(INDEX_PATH)
vecs  = np.load(VEC_PATH)
with open(IDS_PATH) as f: ids = json.load(f)
cat   = pd.read_csv(CATALOG).set_index("item_id")

def mmr(query_vec, cand_idx, topk=10, lam=0.2):
    selected = []
    cand = list(cand_idx)
    while cand and len(selected) < topk:
        if not selected:
            sims = vecs[cand] @ query_vec
            i = int(np.argmax(sims))
            selected.append(cand.pop(i))
            continue
        best, best_score, best_i = None, -1e9, None
        for i, c in enumerate(cand):
            rel = float(vecs[c] @ query_vec)
            div = max(float(vecs[c] @ vecs[s]) for s in selected)
            score = lam*rel - (1-lam)*div
            if score > best_score:
                best, best_score, best_i = c, score, i
        selected.append(best); cand.pop(best_i)
    return selected

@app.get("/health")
def health():
    return {"status": "ok", "items": len(ids)}

@app.get("/recommend/similar")
def recommend_similar(item_id: str, k: int = 10):
    idx = ids.index(item_id)
    q = vecs[idx].astype("float32")
    D, I = index.search(q.reshape(1, -1), 200)
    cand = [i for i in I[0].tolist() if i != idx]
    picks = mmr(q, cand, topk=k)
    out = []
    for i in picks:
        iid = ids[i]
        r = cat.loc[iid]
        out.append({
            "item_id": iid,
            "score": float(vecs[i] @ q),
            "brand": r.get("brand",""),
            "title": r.get("title",""),
            "category": r.get("category",""),
            "image_url": r.get("image_url",""),
            "current_price": r.get("current_price","")
        })
    return out

@app.get("/recommend/complete-look")
def complete_look(seed_item_id: str, target_category: str = "shoes", k: int = 10):
    idx = ids.index(seed_item_id)
    q = vecs[idx].astype("float32")
    allowed = [i for i, iid in enumerate(ids) if str(cat.loc[iid].get("category","")) == target_category]
    if not allowed: return []
    sims = vecs[allowed] @ q
    ordered = [allowed[j] for j in np.argsort(-sims) if allowed[j] != idx]
    picks = mmr(q, ordered, topk=k)
    out = []
    for i in picks:
        iid = ids[i]
        r = cat.loc[iid]
        out.append({
            "item_id": iid,
            "score": float(vecs[i] @ q),
            "brand": r.get("brand",""),
            "title": r.get("title",""),
            "category": r.get("category",""),
            "image_url": r.get("image_url",""),
            "current_price": r.get("current_price","")
        })
    return out

