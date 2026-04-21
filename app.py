"""
app.py  —  BookMind Flask Backend
Uses real Book-Crossing Dataset pickle files:
  model/books copy.pkl            -> 271,360 books (ISBN, Title, Author, Image-URL-L)
  model/pt copy.pkl               -> 706x810 pivot table  (books x users)
  model/similarity_scores copy.pkl -> 706x706 cosine-similarity matrix
  model/popular.pkl               -> Top-50 popular books
"""

import os
import pickle
import numpy as np
from flask import Flask, render_template, request, jsonify

# ── App setup ────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookmind-real-data-2024")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")


def _load(filename: str):
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing: {path}")
    with open(path, "rb") as f:
        return pickle.load(f)


# ── Load all artefacts ───────────────────────────────────────
try:
    books_df          = _load("books copy.pkl")             # full 271K books DataFrame
    pt                = _load("pt copy.pkl")                # pivot table — index = book titles
    similarity_scores = _load("similarity_scores copy.pkl") # (706, 706) numpy array
    popular_df        = _load("popular.pkl")                # top-50 popular books

    # Build a fast lookup: title -> row in books_df
    books_title_lower = books_df["Book-Title"].str.lower().tolist()

    MODEL_READY = True
    print(f"[OK] Model loaded -- {len(pt.index)} recommendable books, "
          f"{len(books_df)} total books, {len(popular_df)} popular books.")

except FileNotFoundError as e:
    MODEL_READY = False
    books_df = pt = similarity_scores = popular_df = books_title_lower = None
    print(f"[ERROR] {e}")


# ── Recommendation logic ─────────────────────────────────────
def recommend(book_name: str, top_n: int = 5) -> list[dict]:
    """
    Return top_n books similar to book_name.
    Matches against pt.index (706 books that have enough ratings).
    Falls back to partial/case-insensitive match.
    """
    if not MODEL_READY:
        raise RuntimeError("Model not loaded.")

    index_list      = list(pt.index)
    query_lower     = book_name.strip().lower()

    # 1. Exact match (case-insensitive)
    book_index = None
    for i, title in enumerate(index_list):
        if title.lower() == query_lower:
            book_index = i
            break

    # 2. Partial / substring match
    if book_index is None:
        candidates = [(i, t) for i, t in enumerate(index_list)
                      if query_lower in t.lower()]
        if not candidates:
            return []
        book_index = candidates[0][0]

    # 3. Sort by similarity descending
    distances  = similarity_scores[book_index]
    sorted_idx = np.argsort(distances)[::-1]

    results = []
    for idx in sorted_idx:
        if idx == book_index:
            continue

        title = index_list[idx]

        # Look up author + image from full books_df
        row = books_df[books_df["Book-Title"] == title]
        if row.empty:
            # Try case-insensitive fallback
            mask = books_df["Book-Title"].str.lower() == title.lower()
            row  = books_df[mask]

        if not row.empty:
            r      = row.iloc[0]
            author = r.get("Book-Author", "Unknown")
            # Prefer large image, fall back to medium
            image  = r.get("Image-URL-L") or r.get("Image-URL-M") or r.get("Image-URL-S", "")
        else:
            author = "Unknown"
            image  = ""

        results.append({
            "title":  title,
            "author": str(author),
            "image":  str(image),
            "score":  round(float(distances[idx]), 4),
        })

        if len(results) >= top_n:
            break

    return results


def build_popular_list() -> list[dict]:
    """Convert popular_df to list of dicts for the template."""
    if popular_df is None:
        return []
    out = []
    for _, row in popular_df.iterrows():
        out.append({
            "title":       row.get("Book-Title", ""),
            "author":      row.get("Book-Author", ""),
            "image":       row.get("Image-URL-M", "") or row.get("Image-URL-L", ""),
            "num_ratings": int(row.get("num_ratings", 0)),
            "avg_rating":  round(float(row.get("avg_rating", 0)), 2),
        })
    return out


# ── Routes ───────────────────────────────────────────────────
@app.route("/")
def index():
    popular = build_popular_list()
    titles  = list(pt.index) if MODEL_READY else []
    return render_template(
        "index.html",
        popular=popular,
        titles=titles,
        model_ready=MODEL_READY,
    )


@app.route("/recommend", methods=["POST"])
def recommend_route():
    data      = request.get_json(silent=True) or {}
    book_name = data.get("book_name", "").strip()

    if not book_name:
        return jsonify({"error": "Please provide a book name."}), 400

    if not MODEL_READY:
        return jsonify({"error": "Model not loaded."}), 503

    try:
        results = recommend(book_name, top_n=5)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    if not results:
        return jsonify({
            "error": f'No recommendations found for "{book_name}". Try another title.'
        }), 404

    return jsonify({"results": results, "query": book_name})


@app.route("/autocomplete")
def autocomplete():
    q      = request.args.get("q", "").strip().lower()
    titles = list(pt.index) if MODEL_READY else []
    if not q or len(q) < 2:
        return jsonify([])
    matches = [t for t in titles if q in t.lower()][:10]
    return jsonify(matches)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
