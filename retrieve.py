import sqlite3
import sqlite_vec
import requests
from rank_bm25 import BM25Okapi

# Database location for the local SQLite RAG index.
DB_PATH = "data/rag.db"
# Local embedding service used to convert a query into a vector representation.
EMBED_URL = "http://127.0.0.1:8080/embedding"

# ---------------- DATABASE ---------------- #

# Connect to SQLite and load the sqlite-vec extension so vector search can run.
def get_db():
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db

# Open the database once at import time and enable the vector extension.
db = get_db()
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Load all indexed chunks so BM25 can score them later.
rows = db.execute(
    "SELECT id, source, page, text FROM chunks"
).fetchall()

# Keep the chunk IDs and tokenized content needed for lexical retrieval.
ids = [r[0] for r in rows]
corpus = [r[3].split() for r in rows]

# Build the BM25 index used for keyword-based matching.
bm25 = BM25Okapi(corpus)

# ---------------- EMBEDDING ---------------- #

# Send text to the external embedding model and return the first embedding vector.
def get_embedding(text):
    r = requests.post(EMBED_URL, json={"content": text})
    r.raise_for_status()
    return r.json()[0]["embedding"][0]

# ---------------- BM25 ---------------- #

# Return the top-k chunk IDs matching the query using BM25 lexical scoring.
def bm25_search(query, k=3):
    scores = bm25.get_scores(query.split())

    # Rank chunks by BM25 score and keep the highest-scoring ones.
    ranked = sorted(
        zip(ids, scores),
        key=lambda x: x[1],
        reverse=True
    )[:k]

    return [i for i, _ in ranked]

# ---------------- VECTOR ---------------- #

# Return the top-k chunk IDs matching the query via semantic vector similarity.
def vector_search(query, k=3):
    # Convert the query to an embedding vector before searching the vector index.
    embedding = get_embedding(query)

    results = db.execute(
        """
        SELECT chunk_id, distance
        FROM vec_chunks
        WHERE embedding MATCH ?
          AND k = ?
        ORDER BY distance
        """,
        (sqlite_vec.serialize_float32(embedding), k)
    ).fetchall()

    return [row[0] for row in results]

# ---------------- HYBRID ---------------- #

# Combine BM25 and semantic retrieval, then fetch the final chunk records.
def retrieve(query, k=5):
    # Create a deduplicated list that keeps the BM25 matches first.
    found = []

    for i in bm25_search(query):
        if i not in found:
            found.append(i)

    # Add vector matches only if they were not already included.
    for i in vector_search(query):
        if i not in found:
            found.append(i)

    # Limit the final candidate list to the requested number of results.
    found = found[:k]

    # Build the SQL IN clause dynamically for the selected chunk ids.
    placeholders = ",".join("?" * len(found))

    return db.execute(
        f"""
        SELECT source, page, text
        FROM chunks
        WHERE id IN ({placeholders})
        """,
        found
    ).fetchall()