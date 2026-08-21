import os
import json
import sqlite3
import requests
import pymupdf as fitz
import sqlite_vec

# ---------------- CONFIG ---------------- #

# Directory containing uploaded PDF files and database/output paths.
BOOKS_DIR = "books"
DB_PATH = "data/rag.db"
EMBED_URL = "http://127.0.0.1:8080/embedding"

# Split each page into segments of roughly this many words.
CHUNK_SIZE = 200  # words

# ------------- DATABASE ----------------- #

# Make sure the folder for the SQLite database exists before writing.
os.makedirs("data", exist_ok=True)

# Open the local SQLite database and load sqlite-vec for vector storage.
db = sqlite3.connect(DB_PATH)
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Store raw text chunks and their page/source metadata.
db.execute("""
CREATE TABLE IF NOT EXISTS chunks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    page INTEGER,
    text TEXT
)
""")

# Store vector embeddings for each chunk using sqlite-vec.
db.execute("""
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks
USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[384]
)
""")

# Clear previous indexed content before re-ingesting.
db.execute("DELETE FROM chunks")
db.execute("DELETE FROM vec_chunks")
db.commit()

# ------------- FUNCTIONS ---------------- #

# Split text into chunks of a fixed word count.
def chunk_text(text, size=CHUNK_SIZE):
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i + size])


# Call the local embedding service to convert text into a vector.
def get_embedding(text):
    r = requests.post(EMBED_URL, json={"content": text})
    r.raise_for_status()

    data = r.json()

    # llama-server returns: [{"embedding": [[...]]}]
    return data[0]["embedding"][0]

# ------------- INGEST ------------------- #

# Loop over every PDF in the books folder and index its pages/chunks.
for filename in os.listdir(BOOKS_DIR):

    if not filename.endswith(".pdf"):
        continue

    pdf = fitz.open(os.path.join(BOOKS_DIR, filename))

    print(f"Ingesting: {filename}")

    for page_no, page in enumerate(pdf, start=1):

        text = page.get_text().strip()

        if not text:
            continue

        for chunk in chunk_text(text):

            embedding = get_embedding(chunk)

            cur = db.execute(
                "INSERT INTO chunks(source,page,text) VALUES(?,?,?)",
                (filename, page_no, chunk)
            )

            chunk_id = cur.lastrowid

            db.execute(
                "INSERT INTO vec_chunks(chunk_id, embedding) VALUES(?, ?)",
                (chunk_id, sqlite_vec.serialize_float32(embedding))
            )

db.commit()
db.close()

print("RAG database created successfully.")