"""
generate_model.py
-----------------
Run this script ONCE to generate the required pickle files:
  - model/books.pkl
  - model/pt.pkl
  - model/similarity_scores.pkl

Usage:
    python generate_model.py
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# 1. Curated book dataset (title, author, image_url, genre)
# ---------------------------------------------------------------------------
BOOKS = [
    # Fiction / Literary
    ("The Great Gatsby",           "F. Scott Fitzgerald",  "https://covers.openlibrary.org/b/id/8432827-L.jpg",  "fiction"),
    ("To Kill a Mockingbird",      "Harper Lee",           "https://covers.openlibrary.org/b/id/8810494-L.jpg",  "fiction"),
    ("1984",                       "George Orwell",        "https://covers.openlibrary.org/b/id/7222246-L.jpg",  "dystopia"),
    ("Brave New World",            "Aldous Huxley",        "https://covers.openlibrary.org/b/id/8406786-L.jpg",  "dystopia"),
    ("Animal Farm",                "George Orwell",        "https://covers.openlibrary.org/b/id/8291536-L.jpg",  "dystopia"),
    ("Fahrenheit 451",             "Ray Bradbury",         "https://covers.openlibrary.org/b/id/8228691-L.jpg",  "dystopia"),
    ("The Catcher in the Rye",     "J.D. Salinger",        "https://covers.openlibrary.org/b/id/8231432-L.jpg",  "fiction"),
    ("Of Mice and Men",            "John Steinbeck",       "https://covers.openlibrary.org/b/id/8231446-L.jpg",  "fiction"),
    ("The Old Man and the Sea",    "Ernest Hemingway",     "https://covers.openlibrary.org/b/id/8228678-L.jpg",  "fiction"),
    ("Lord of the Flies",          "William Golding",      "https://covers.openlibrary.org/b/id/8231460-L.jpg",  "fiction"),
    # Fantasy
    ("The Hobbit",                 "J.R.R. Tolkien",       "https://covers.openlibrary.org/b/id/8406786-L.jpg",  "fantasy"),
    ("The Fellowship of the Ring", "J.R.R. Tolkien",       "https://covers.openlibrary.org/b/id/8743261-L.jpg",  "fantasy"),
    ("The Two Towers",             "J.R.R. Tolkien",       "https://covers.openlibrary.org/b/id/8743262-L.jpg",  "fantasy"),
    ("The Return of the King",     "J.R.R. Tolkien",       "https://covers.openlibrary.org/b/id/8743263-L.jpg",  "fantasy"),
    ("Harry Potter and the Philosopher's Stone", "J.K. Rowling", "https://covers.openlibrary.org/b/id/10110415-L.jpg", "fantasy"),
    ("Harry Potter and the Chamber of Secrets",  "J.K. Rowling", "https://covers.openlibrary.org/b/id/8228691-L.jpg",  "fantasy"),
    ("Harry Potter and the Prisoner of Azkaban", "J.K. Rowling", "https://covers.openlibrary.org/b/id/8228675-L.jpg",  "fantasy"),
    ("A Game of Thrones",          "George R.R. Martin",   "https://covers.openlibrary.org/b/id/8406786-L.jpg",  "fantasy"),
    ("A Clash of Kings",           "George R.R. Martin",   "https://covers.openlibrary.org/b/id/8406789-L.jpg",  "fantasy"),
    ("The Name of the Wind",       "Patrick Rothfuss",     "https://covers.openlibrary.org/b/id/8743270-L.jpg",  "fantasy"),
    # Science Fiction
    ("Dune",                       "Frank Herbert",        "https://covers.openlibrary.org/b/id/8743271-L.jpg",  "sci-fi"),
    ("Foundation",                 "Isaac Asimov",         "https://covers.openlibrary.org/b/id/8743272-L.jpg",  "sci-fi"),
    ("The Hitchhiker's Guide to the Galaxy", "Douglas Adams", "https://covers.openlibrary.org/b/id/8743273-L.jpg", "sci-fi"),
    ("Ender's Game",               "Orson Scott Card",     "https://covers.openlibrary.org/b/id/8743274-L.jpg",  "sci-fi"),
    ("The Martian",                "Andy Weir",            "https://covers.openlibrary.org/b/id/8743275-L.jpg",  "sci-fi"),
    ("Neuromancer",                "William Gibson",       "https://covers.openlibrary.org/b/id/8743276-L.jpg",  "sci-fi"),
    ("Snow Crash",                 "Neal Stephenson",      "https://covers.openlibrary.org/b/id/8743277-L.jpg",  "sci-fi"),
    ("The Left Hand of Darkness",  "Ursula K. Le Guin",    "https://covers.openlibrary.org/b/id/8743278-L.jpg",  "sci-fi"),
    # Mystery / Thriller
    ("Gone Girl",                  "Gillian Flynn",        "https://covers.openlibrary.org/b/id/8743279-L.jpg",  "thriller"),
    ("The Girl with the Dragon Tattoo", "Stieg Larsson",   "https://covers.openlibrary.org/b/id/8743280-L.jpg",  "thriller"),
    ("The Da Vinci Code",          "Dan Brown",            "https://covers.openlibrary.org/b/id/8743281-L.jpg",  "thriller"),
    ("Angels & Demons",            "Dan Brown",            "https://covers.openlibrary.org/b/id/8743282-L.jpg",  "thriller"),
    ("Inferno",                    "Dan Brown",            "https://covers.openlibrary.org/b/id/8743283-L.jpg",  "thriller"),
    ("And Then There Were None",   "Agatha Christie",      "https://covers.openlibrary.org/b/id/8743284-L.jpg",  "mystery"),
    ("Murder on the Orient Express","Agatha Christie",     "https://covers.openlibrary.org/b/id/8743285-L.jpg",  "mystery"),
    # Self-Help / Non-Fiction
    ("Atomic Habits",              "James Clear",          "https://covers.openlibrary.org/b/id/10527843-L.jpg", "self-help"),
    ("The Power of Now",           "Eckhart Tolle",        "https://covers.openlibrary.org/b/id/8743287-L.jpg",  "self-help"),
    ("Thinking, Fast and Slow",    "Daniel Kahneman",      "https://covers.openlibrary.org/b/id/8743288-L.jpg",  "non-fiction"),
    ("Sapiens",                    "Yuval Noah Harari",    "https://covers.openlibrary.org/b/id/8743289-L.jpg",  "non-fiction"),
    ("Homo Deus",                  "Yuval Noah Harari",    "https://covers.openlibrary.org/b/id/8743290-L.jpg",  "non-fiction"),
    ("The 7 Habits of Highly Effective People", "Stephen Covey", "https://covers.openlibrary.org/b/id/8743291-L.jpg", "self-help"),
    ("How to Win Friends and Influence People", "Dale Carnegie", "https://covers.openlibrary.org/b/id/8743292-L.jpg", "self-help"),
    ("Rich Dad Poor Dad",          "Robert Kiyosaki",      "https://covers.openlibrary.org/b/id/8743293-L.jpg",  "self-help"),
    # Romance
    ("Pride and Prejudice",        "Jane Austen",          "https://covers.openlibrary.org/b/id/8743294-L.jpg",  "romance"),
    ("Sense and Sensibility",      "Jane Austen",          "https://covers.openlibrary.org/b/id/8743295-L.jpg",  "romance"),
    ("Emma",                       "Jane Austen",          "https://covers.openlibrary.org/b/id/8743296-L.jpg",  "romance"),
    ("Wuthering Heights",          "Emily Brontë",         "https://covers.openlibrary.org/b/id/8743297-L.jpg",  "romance"),
    ("Jane Eyre",                  "Charlotte Brontë",     "https://covers.openlibrary.org/b/id/8743298-L.jpg",  "romance"),
    ("The Notebook",               "Nicholas Sparks",      "https://covers.openlibrary.org/b/id/8743299-L.jpg",  "romance"),
    ("Twilight",                   "Stephenie Meyer",      "https://covers.openlibrary.org/b/id/8743300-L.jpg",  "romance"),
]

GENRE_ORDER = ["fiction", "dystopia", "fantasy", "sci-fi", "thriller", "mystery", "self-help", "non-fiction", "romance"]
GENRE_INDEX = {g: i for i, g in enumerate(GENRE_ORDER)}

np.random.seed(42)
N = len(BOOKS)


# ---------------------------------------------------------------------------
# 2. Build a DataFrame for books
# ---------------------------------------------------------------------------
books_df = pd.DataFrame(BOOKS, columns=["Book-Title", "Book-Author", "Image-URL-L", "genre"])
books_df["ISBN"] = [f"ISBN{i:04d}" for i in range(N)]


# ---------------------------------------------------------------------------
# 3. Build a pivot table (books × simulated users) and similarity matrix
# ---------------------------------------------------------------------------
NUM_USERS = 300

# Users who read similar genres give similar ratings
ratings = np.zeros((N, NUM_USERS))
for u in range(NUM_USERS):
    fav_genre_idx = np.random.randint(0, len(GENRE_ORDER))
    for b_idx, (_, _, _, genre, *_) in enumerate(BOOKS):
        genre_idx = GENRE_INDEX[genre]
        closeness = max(0, 1 - abs(genre_idx - fav_genre_idx) / len(GENRE_ORDER))
        base = 3 + 2 * closeness
        noise = np.random.normal(0, 0.5)
        rating = np.clip(base + noise, 1, 5)
        # Only some users rate each book
        if np.random.random() < (0.3 + 0.4 * closeness):
            ratings[b_idx, u] = round(rating)

pt = pd.DataFrame(
    ratings,
    index=books_df["Book-Title"].values,
    columns=[f"User_{u}" for u in range(NUM_USERS)],
)

similarity_scores = cosine_similarity(pt)

# ---------------------------------------------------------------------------
# 4. Save pickle files
# ---------------------------------------------------------------------------
os.makedirs("model", exist_ok=True)

with open("model/books.pkl", "wb") as f:
    pickle.dump(books_df, f)

with open("model/pt.pkl", "wb") as f:
    pickle.dump(pt, f)

with open("model/similarity_scores.pkl", "wb") as f:
    pickle.dump(similarity_scores, f)

print("✅  Pickle files generated successfully in the model/ directory:")
print("    - model/books.pkl")
print("    - model/pt.pkl")
print("    - model/similarity_scores.pkl")
print(f"    Total books: {N}")
