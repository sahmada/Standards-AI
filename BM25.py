import json
import re
import numpy as np
from rank_bm25 import BM25Okapi


# ============================
# 1) توکن‌سازی متن (ساده و مؤثر)
# ============================

def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)   # حذف علائم
    text = re.sub(r"\s+", " ", text)       # حذف فاصله‌های اضافی
    return text.split()


# ============================
# 2) بارگذاری بندهای استاندارد
# ============================

def load_clauses(json_path="clauses.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        clauses = json.load(f)
    return clauses


# ============================
# 3) ساخت ایندکس BM25
# ============================

def build_bm25_index(clauses):
    documents = [tokenize(c["text"]) for c in clauses]
    bm25 = BM25Okapi(documents)
    return bm25, documents


# ============================
# 4) جستجو در BM25
# ============================

def search_bm25(query, bm25, clauses, top_n=5):
    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)
    best_indexes = np.argsort(scores)[::-1][:top_n]

    results = []
    for idx in best_indexes:
        results.append({
            "clause_id": clauses[idx]["clause_id"],
            "title": clauses[idx]["title"],
            "text": clauses[idx]["text"],
            "score": float(scores[idx])
        })
    return results


# ============================
# 5) اجرای تست نمونه
# ============================

if __name__ == "__main__":
    print("Loading clauses...")
    clauses = load_clauses("clauses.json")

    print("Building BM25 index...")
    bm25, docs = build_bm25_index(clauses)

    print("Searching BM25 for sample query...")
    query = "زمان ماند در جداکننده گاز مایع"
    results = search_bm25(query, bm25, clauses, top_n=5)

    for r in results:
        print("=" * 60)
        print("Clause:", r["clause_id"])
        print("Title :", r["title"])
        print("Score :", r["score"])
        print("Text  :", r["text"][:250], "...")