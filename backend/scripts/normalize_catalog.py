import pandas as pd, glob, os, hashlib, re, json, sys
from pathlib import Path

# --- Resolve paths relative to THIS FILE (not the working dir) ---
THIS_FILE = Path(__file__).resolve()
BACKEND_DIR = THIS_FILE.parents[1]           # .../backend
PROJECT_DIR = BACKEND_DIR.parent             # .../clozyt-track
DATA_DIR = PROJECT_DIR / "data"
SRC_DIR = DATA_DIR / "brands"
OUT = DATA_DIR / "catalog.csv"
# -----------------------------------------------------------------


def as_list(x):
    if pd.isna(x): return []
    s = str(x)
    parts = re.split(r'[|,;/\t]', s)
    return [p.strip() for p in parts if p.strip()]

def mk_id(brand, pid, url):
    base = f"{brand}:{pid or ''}:{url or ''}"
    h = hashlib.md5(base.encode()).hexdigest()[:10]
    return f"{brand.lower()}:{h}"

def read_csv_robust(path):
    # Try common encodings / separators
    tries = [
        dict(encoding="utf-8", sep=","),
        dict(encoding="utf-8-sig", sep=","),
        dict(encoding="latin-1", sep=","),
        dict(encoding="utf-8", sep=";"),
    ]
    for kw in tries:
        try:
            return pd.read_csv(path, **kw)
        except Exception:
            continue
    # Last resort: python engine, no dtype inference
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}", file=sys.stderr)
        return pd.DataFrame()

rows = []
paths = sorted(glob.glob(str(SRC_DIR / "*.csv")))
print(f"[DEBUG] Looking for CSVs in: {SRC_DIR}")
if not paths:
    print(f"[ERROR] No CSVs found in {SRC_DIR}.", file=sys.stderr)
    sys.exit(1)

for path in paths:
    brand = Path(path).stem.replace("_products","")
    df = read_csv_robust(path)
    if df.empty:
        print(f"[WARN] Empty or unreadable: {os.path.basename(path)}")
        continue

    print(f"[INFO] Processing {os.path.basename(path)} with {len(df)} rows")
    # Normalize likely column names to a standard set (case-insensitive)
    cols = {c.lower(): c for c in df.columns}
    def cget(*names):
        for n in names:
            if n in cols: return cols[n]
        return None

    for _, r in df.iterrows():
        title = r.get(cget("title","name"))
        pid   = r.get(cget("product_id","sku","id"))
        url   = r.get(cget("product_url","url","link"))
        image = r.get(cget("image_url","img","image","thumbnail"))
        price = r.get(cget("current_price","price","sale_price","final_price"))
        oprice= r.get(cget("original_price","list_price","msrp"))
        cat_v = r.get(cget("category","subcategory","type","collection"))
        sizes = r.get(cget("available_sizes","sizes","size"))
        colors= r.get(cget("available_colors","color","colors"))
        labels= r.get(cget("labels","tags","label","tag","promotion","notes"))
        avail = r.get(cget("availability","stock_status","in_stock","status"))

        rows.append({
            "item_id": mk_id(brand, pid, url),
            "brand": brand,
            "title": None if pd.isna(title) else str(title),
            "category": None if pd.isna(cat_v) else str(cat_v).lower(),
            "color_list": json.dumps(as_list(colors)),
            "size_list": json.dumps(as_list(sizes)),
            "current_price": pd.to_numeric(price, errors="coerce"),
            "original_price": pd.to_numeric(oprice, errors="coerce"),
            "tags": json.dumps(as_list(labels)),
            "availability_status": None if pd.isna(avail) else str(avail),
            "product_url": None if pd.isna(url) else str(url),
            "image_url": None if pd.isna(image) else str(image),
            "raw_source": os.path.basename(path)
        })

cat = pd.DataFrame(rows)

# Ensure required columns exist even if rows is empty/partial
for needed in ["item_id","brand","title","category","color_list","size_list",
               "current_price","original_price","tags","availability_status",
               "product_url","image_url","raw_source"]:
    if needed not in cat.columns:
        cat[needed] = None

# Drop dupes and rows missing item_id or title
cat = cat.drop_duplicates("item_id")
cat = cat[cat["item_id"].notna() & cat["title"].notna()]

def norm_cat(c):
    if not c or pd.isna(c): return None
    s = str(c).lower()
    if any(k in s for k in ["jean","pant","bottom","trouser","short","skirt"]): return "bottoms"
    if any(k in s for k in ["jacket","coat","outer","hoodie","sweater"]): return "outerwear"
    if any(k in s for k in ["dress","gown"]): return "dress"
    if any(k in s for k in ["shoe","sneaker","boot","sandal","heel","trainer"]): return "shoes"
    if any(k in s for k in ["top","tee","t-shirt","shirt","blouse","bra","tank","crew","hooded"]): return "tops"
    if any(k in s for k in ["bag","belt","hat","cap","scarf","sock","accessor"]): return "accessories"
    return "other"

cat["category"] = cat["category"].apply(norm_cat)

# Final sanity
cat = cat.reset_index(drop=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
cat.to_csv(OUT, index=False)
print(f"[DONE] Wrote {OUT} with {len(cat)} items.")
