import pandas as pd, numpy as np, faiss, json
from pathlib import Path

# --- Resolve paths relative to THIS FILE (not the working dir) ---
THIS_FILE = Path(__file__).resolve()
BACKEND_DIR = THIS_FILE.parents[1]           # .../backend
PROJECT_DIR = BACKEND_DIR.parent             # .../clozyt-track
DATA_DIR = PROJECT_DIR / "data"
CATALOG = DATA_DIR / "catalog.csv"
OUT_VEC = DATA_DIR / "item_vectors.npy"
OUT_IDS = DATA_DIR / "item_ids.json"
INDEX   = DATA_DIR / "faiss.index"
# -----------------------------------------------------------------
print(f"[DEBUG] Reading catalog from: {CATALOG}")


def normalize(x):
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-8
    return x / norms

# ---- STUB encoders (replace with CLIP later) ----
def encode_image_batch(urls):
    rng = np.random.default_rng(42)
    return rng.normal(size=(len(urls), 512)).astype("float32")
def encode_text_batch(texts):
    rng = np.random.default_rng(43)
    return rng.normal(size=(len(texts), 512)).astype("float32")
# -------------------------------------------------

df = pd.read_csv(CATALOG)
texts = (df["brand"].fillna("") + " " + df["title"].fillna("") + " " +
         df["category"].fillna("") + " " + df["tags"].fillna("")).tolist()
img_vecs = encode_image_batch(df["image_url"].fillna("").tolist())
txt_vecs = encode_text_batch(texts)

vecs = normalize(0.7*img_vecs + 0.3*txt_vecs).astype("float32")

np.save(OUT_VEC, vecs)
Path(OUT_IDS).write_text(json.dumps(df["item_id"].tolist()))
index = faiss.IndexFlatIP(vecs.shape[1])
index.add(vecs)
faiss.write_index(index, str(INDEX))
print(f"Indexed {len(df)} items at dim {vecs.shape[1]}")
