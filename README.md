# 📘 Z1 — Offline AI Study Assistant

> **A privacy-focused, offline AI study assistant that answers questions directly from your own study materials using Hybrid RAG.**

Z1 is an experimental **offline AI study assistant** designed to make AI-powered learning accessible without depending on cloud-based AI services or a constant internet connection.

Users can upload PDF study materials, which Z1 processes locally and stores in a SQLite-based RAG database. When a question is asked, Z1 combines **BM25 keyword retrieval** with **vector-based semantic retrieval** to find relevant passages. These passages are then provided to a locally running language model to generate a grounded answer.

The long-term vision of Z1 is to evolve from a document-based RAG assistant into a **privacy-preserving personal AI tutor and "second brain."**

---

## ✨ Features

* 📚 Ask questions from uploaded PDF documents
* 🔒 Local-first and privacy-focused architecture
* 🌐 Designed for offline AI-assisted learning
* 🔎 Hybrid retrieval system

  * BM25 keyword search
  * Vector semantic search
* 🧠 Local embedding generation
* 🤖 Local LLM inference
* 🗃️ SQLite document database
* ⚡ SQLite-Vec vector search
* 📄 Page-level source tracking
* 💬 Streamlit chat interface
* 🔄 Automatic PDF ingestion after upload
* ⚠️ Indexing error handling
* 🧹 New Chat functionality
* 🛡️ Graceful handling when no indexed documents are available

The hybrid retrieval approach combines the strengths of lexical and semantic search: BM25 helps with exact keywords and technical terms, while vector search helps identify conceptually similar content.

---

# 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │     Streamlit UI    │
                         │       app.py        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      chat.py        │
                         │  Query Orchestrator │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     retrieve.py     │
                         │   Hybrid Retrieval  │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
             ┌──────────────┐              ┌────────────────┐
             │     BM25     │              │ Vector Search  │
             │    Search    │              │  SQLite-Vec    │
             └──────┬───────┘              └───────┬────────┘
                    │                              │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │    SQLite RAG DB    │
                         │  Text + Embeddings  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Local Embedding   │
                         │       Server        │
                         └─────────────────────┘

                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Local LLM API    │
                         │  Chat Completions   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Grounded Answer   │
                         │   + Source Pages    │
                         └─────────────────────┘
```

---

# 🔄 How Z1 Works

## 1. Upload a PDF

The user uploads a PDF through the Streamlit sidebar.

The file is saved into:

```text
books/
```

Z1 then automatically starts the ingestion process.

The application now also catches ingestion failures and displays an error instead of silently crashing.

---

## 2. Extract Text

`ingest.py` uses **PyMuPDF** to open each PDF and extract text page by page.

Each page's text is divided into chunks of approximately:

```text
200 words
```

---

## 3. Generate Embeddings

Every text chunk is sent to the local embedding service:

```text
http://127.0.0.1:8080/embedding
```

The returned embedding is stored in the SQLite-Vec vector database.

The current vector table uses:

```text
384-dimensional embeddings
```

---

## 4. Store the Knowledge Base

Z1 maintains a SQLite database at:

```text
data/rag.db
```

The database contains:

* Chunk ID
* Source filename
* Page number
* Extracted text
* Vector embeddings

Before rebuilding the index, the existing chunks and vectors are cleared.

## The updated ingestion script also checks whether there are actually PDFs in the `books/` directory. If none are found, it leaves the existing database unchanged rather than deleting the current index.

# 🔎 Hybrid Retrieval

When the user asks a question, Z1 performs two searches.

### BM25 Search

BM25 performs lexical/keyword-based retrieval.

It is particularly useful for:

* Exact terminology
* Names
* Technical words
* Formulas
* Specific phrases

### Vector Search

The question is converted into an embedding and compared against the stored vector embeddings using SQLite-Vec.

This helps retrieve content that is **semantically similar**, even when the wording differs.

### Combined Retrieval

Z1 combines the results from both methods, removes duplicate chunk IDs, and keeps the best candidates.

## The updated retrieval implementation dynamically loads the current database index when a query is made rather than assuming the database was available when the module was initially imported.

# 🤖 Local LLM

The retrieved document chunks are sent to a locally running OpenAI-compatible chat-completion API:

```text
http://127.0.0.1:8081/v1/chat/completions
```

Z1 uses a system prompt that instructs the model to:

1. Answer only from the retrieved context.
2. Clearly state when the answer is unavailable.
3. Keep explanations clear and brief.

If no relevant documents are available, Z1 returns:

> **The answer is not available in the uploaded documents.**

---

# 📄 Source Tracking

Z1 doesn't just return an answer.

It also keeps track of:

```text
Source PDF
Page number
```

The Streamlit interface displays these sources underneath the assistant's response.

## This makes it easier to trace the generated answer back to the uploaded study material.

# 📁 Project Structure

```text
Z1/
│
├── app.py
├── chat.py
├── ingest.py
├── retrieve.py
├── documentation.txt
│
├── books/
│   └── *.pdf
│
└── data/
    └── rag.db
```

---

# 🧩 Core Files

## `app.py`

The Streamlit frontend.

Responsibilities:

* PDF uploading
* Saving PDFs
* Starting ingestion
* Chat interface
* Session conversation history
* Displaying sources
* New Chat functionality
* Handling ingestion failures

---

## `ingest.py`

The document ingestion pipeline.

Responsibilities:

1. Find PDFs in `books/`
2. Check whether PDFs exist
3. Extract page text
4. Split text into chunks
5. Generate embeddings
6. Store text and metadata in SQLite
7. Store embeddings in SQLite-Vec
8. Rebuild the RAG index

---

## `retrieve.py`

The hybrid retrieval engine.

Responsibilities:

* Load the current RAG database
* Build the BM25 index
* Generate query embeddings
* Perform BM25 retrieval
* Perform vector retrieval
* Combine results
* Remove duplicates
* Return source/page/text information
* Safely close the database connection

The updated implementation uses `try/finally` to ensure the database is closed after retrieval.

---

## `chat.py`

The question-answering layer.

It:

1. Receives the user's question
2. Calls the retrieval pipeline
3. Builds the context
4. Creates the local LLM request
5. Sends the request
6. Extracts the generated answer
7. Returns the answer and sources

---

# 🧰 Tech Stack

| Component         | Technology                     |
| ----------------- | ------------------------------ |
| Frontend          | Streamlit                      |
| Language          | Python                         |
| PDF Processing    | PyMuPDF                        |
| Database          | SQLite                         |
| Vector Search     | SQLite-Vec                     |
| Keyword Retrieval | BM25                           |
| Embeddings        | Local Embedding API            |
| LLM               | Local OpenAI-compatible API    |
| Architecture      | Retrieval-Augmented Generation |

---

# 🚀 Installation

## Prerequisites

You need:

* Python 3.x
* A local embedding server
* A local LLM server
* SQLite-Vec support

The current application expects the embedding service at:

```text
http://127.0.0.1:8080/embedding
```

and the LLM service at:

```text
http://127.0.0.1:8081/v1/chat/completions
```

---

## Install Python Dependencies

```bash
pip install streamlit requests pymupdf sqlite-vec rank-bm25
```

---

# ▶️ Running Z1

Start your local embedding server first.

Then start your local LLM server.

Finally run:

```bash
streamlit run app.py
```

Open the Streamlit URL displayed in the terminal.

---

# 📚 Using Z1

### Step 1

Start the local embedding service.

### Step 2

Start the local LLM service.

### Step 3

Launch Z1:

```bash
streamlit run app.py
```

### Step 4

Upload a PDF using:

**Sidebar → Upload PDF**

### Step 5

Wait for:

```text
Creating RAG...
```

After successful indexing:

```text
<filename>.pdf indexed!
```

### Step 6

Ask a question.

For example:

```text
What is the main concept discussed in chapter 2?
```

### Step 7

Open **Sources** to see which PDF pages were used.

---

# 🛡️ Error Handling & Reliability

The updated version introduces several improvements to make the application more robust.

### Empty `books/` Directory

If no PDF files exist, `ingest.py` now stops without destroying an existing RAG database.

```text
No PDF files found. Existing RAG database was left unchanged.
```

### Missing Database

`retrieve.py` checks whether the database exists before attempting retrieval.

If it isn't ready, retrieval returns an empty result instead of immediately failing.

### Empty Index

If the database exists but contains no indexed documents, BM25 is not initialized and retrieval safely returns no results.

### Database Cleanup

The retrieval process closes its SQLite connection in a `finally` block, helping prevent lingering database connections.

### Ingestion Failure

If indexing fails during a PDF upload, Streamlit now displays:

```text
Indexing failed with exit code <code>.
```

instead of allowing the subprocess error to crash the interface.

---

# 🔐 Privacy & Offline Design

Z1 is built around the idea of keeping AI-assisted learning local.

Study documents are processed and indexed on the user's machine, while the embedding and language-model services are expected to run locally.

This reduces dependence on external cloud AI services and allows the project to target environments where reliable internet connectivity may not always be available.

> **Your study material. Your machine. Your AI.**

---

# ⚠️ Current Limitations

## No OCR

Scanned or image-only PDFs are not currently supported because the ingestion pipeline extracts textual PDF content.

## No Visual Understanding

Diagrams, charts, handwritten notes, and other visual information are not currently interpreted.

## No Persistent Conversational Memory

Chat history is maintained within the current Streamlit session but is not stored as long-term memory.

## Shared Knowledge Base

The current ingestion pipeline rebuilds a single SQLite knowledge base from the PDFs currently present in `books/`.

## Limited Document Management

There is currently no interface for individually activating, deactivating, or deleting specific documents from the knowledge base.

---

# 🛣️ Roadmap

## 📓 Notebook-Based Knowledge Management

Allow students to organize PDFs into separate notebooks or subjects.

```text
Z1
├── Mathematics
├── Physics
├── Computer Science
└── Personal Notes
```

Each subject could eventually have its own knowledge base.

---

## 📝 Intelligent Mock Examination System

Generate examinations directly from uploaded study materials.

Future versions could:

* Generate questions
* Accept written answers
* Evaluate answers
* Provide scores
* Give feedback
* Identify weak areas

---

## ⏱️ Learning & Anti-Procrastination Support

Move beyond simply answering questions.

Z1 could eventually guide students through structured learning sessions and encourage focused study.

---

## 🧠 Adaptive Learning Assistance

If a student repeatedly struggles with a concept, Z1 could provide:

* Hints
* Simpler explanations
* Examples
* Alternative explanations
* Targeted practice

---

## 👁️ Multimodal Document Understanding

Future versions could understand:

* Diagrams
* Charts
* Tables
* Images
* Handwritten notes
* Other visual study materials

---

# 🎯 Long-Term Vision

Z1 is intended to evolve beyond a PDF chatbot.

```text
PDF Chatbot
     ↓
Offline RAG Assistant
     ↓
Subject / Notebook Knowledge Base
     ↓
Personalized Learning Assistant
     ↓
Adaptive AI Tutor
     ↓
Personal AI "Second Brain"
```

The ultimate goal is a **privacy-preserving personal AI tutor** that can understand a user's knowledge, organize information, assist with learning, and eventually become a personal second brain.

---

# 🤝 Contributing

Contributions, experiments, ideas, and improvements are welcome.

Potential areas for contribution:

* Better retrieval and ranking
* OCR
* Multimodal RAG
* Document management
* Persistent memory
* Subject-based knowledge bases
* Local model optimization
* Mock examination generation
* Learning analytics
* UI/UX improvements
* Retrieval evaluation and benchmarking

---

# 📊 Project Status

**Status: MVP / Experimental**

Z1 currently demonstrates a working offline Hybrid RAG pipeline consisting of:

```text
PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Local Embeddings
 ↓
SQLite + SQLite-Vec
 ↓
BM25 + Vector Retrieval
 ↓
Local LLM
 ↓
Grounded Answer
 ↓
Source Pages
```

The current version focuses on making the core RAG pipeline reliable while providing a foundation for future personalized learning features.

---

# ⭐ Why Z1?

Many modern AI study tools depend heavily on:

* Reliable internet
* Cloud AI services
* External APIs
* Uploading personal documents

Z1 explores a different question:

> **What if useful AI learning assistance could run locally on an ordinary personal computer?**

The project is an attempt to build toward that idea — starting with offline document retrieval and gradually moving toward a private, adaptive personal AI tutor.

---

# 📌 License

No license has currently been specified for the project.

If you plan to publish Z1 as open source, add an appropriate license such as MIT, Apache-2.0, or another license that matches your goals.

---

<div align="center">

**📘 Z1 — Offline AI Study Assistant**

*Learn from your knowledge. Run your AI locally. Build your second brain.*

</div>
