# 📘 Z1 — Offline AI Study Assistant

> **A privacy-focused, offline AI study assistant that answers questions directly from your own study materials using Hybrid RAG.**

Z1 is an experimental offline AI study assistant designed to make AI-powered learning accessible without depending on cloud services or a constant internet connection.

It allows students to upload PDF study materials, indexes their contents locally, and answers questions using a combination of **BM25 keyword retrieval** and **vector-based semantic retrieval**. The retrieved context is then passed to a locally running language model to generate a concise, grounded answer.

The long-term goal of Z1 is to evolve from a document-based RAG system into a **privacy-preserving personal AI tutor and "second brain."**

---

## ✨ Features

* 📚 **Ask questions from uploaded PDFs**
* 🔒 **Local-first / privacy-focused architecture**
* 🌐 **Designed for offline AI-assisted learning**
* 🔎 **Hybrid retrieval**

  * BM25 keyword search
  * Vector semantic search
* 🧠 **Local embedding generation**
* 🤖 **Local LLM inference**
* 🗃️ **SQLite-based knowledge store**
* ⚡ **SQLite-Vec vector search**
* 📄 **Page-level source tracking**
* 💬 **Streamlit chat interface**
* 🔄 **Automatic re-indexing when a PDF is uploaded**
* 🧹 **Session-based "New Chat" functionality**

## The current system combines BM25 and vector retrieval because keyword search is useful for exact terms while vector search is useful for semantically similar concepts.

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │     Streamlit UI    │
                    │       app.py        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      chat.py        │
                    │   Query Orchestrator│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     retrieve.py     │
                    │   Hybrid Retrieval  │
                    └─────────┬───────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
        ┌────────────────┐        ┌────────────────┐
        │     BM25       │        │  Vector Search │
        │ Keyword Search │        │  SQLite-Vec    │
        └────────┬───────┘        └────────┬───────┘
                 │                         │
                 └────────────┬────────────┘
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

## 🔄 How It Works

### 1. Upload

A user uploads a PDF through the Streamlit interface.

The PDF is stored in the `books/` directory. The application then runs the ingestion pipeline automatically.

### 2. Text Extraction

`ingest.py` opens each PDF using PyMuPDF and extracts text page by page.

The extracted text is divided into chunks of approximately **200 words**.

### 3. Embedding

Each chunk is sent to a locally running embedding service:

```text
http://127.0.0.1:8080/embedding
```

The resulting 384-dimensional embedding is stored in SQLite-Vec.

### 4. Hybrid Retrieval

When a user asks a question, Z1 performs two retrieval operations:

**BM25**

Finds relevant chunks based on keyword matching.

**Vector Search**

Converts the question into an embedding and searches for semantically similar chunks using SQLite-Vec.

The results are combined and deduplicated to create the final context.

### 5. Local LLM

The retrieved chunks are passed to a locally running OpenAI-compatible chat-completion endpoint:

```text
http://127.0.0.1:8081/v1/chat/completions
```

The system prompt instructs the model to answer **only from the retrieved document context**. If the information is unavailable, it returns:

> "The answer is not available in the uploaded documents."

### 6. Source Display

Answers are accompanied by the source document and page number of the retrieved chunks, allowing the user to identify where the answer came from.

---

## 📁 Project Structure

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

### `app.py`

The Streamlit frontend.

It handles:

* PDF uploads
* Chat interface
* Session chat history
* Source display
* Triggering the ingestion process

### `ingest.py`

The document ingestion pipeline.

It:

1. Reads PDFs
2. Extracts page text
3. Splits text into chunks
4. Generates embeddings
5. Stores chunks in SQLite
6. Stores embeddings in SQLite-Vec

### `retrieve.py`

The hybrid retrieval engine.

It contains:

* BM25 retrieval
* Vector retrieval
* Result combination
* SQLite database access

### `chat.py`

The question-answering layer.

It:

1. Receives the user's question
2. Retrieves relevant document chunks
3. Builds the LLM context
4. Sends the request to the local LLM
5. Returns the answer and sources

---

## 🧰 Tech Stack

| Component         | Technology                           |
| ----------------- | ------------------------------------ |
| Frontend          | Streamlit                            |
| Language          | Python                               |
| PDF Processing    | PyMuPDF                              |
| Database          | SQLite                               |
| Vector Database   | SQLite-Vec                           |
| Keyword Retrieval | BM25                                 |
| Embeddings        | Local embedding API                  |
| LLM               | Local OpenAI-compatible API          |
| Architecture      | Retrieval-Augmented Generation (RAG) |

---

## 🚀 Getting Started

### Prerequisites

You need:

* Python 3.x
* A local embedding server running on:

```text
http://127.0.0.1:8080
```

* A local LLM/chat-completion server running on:

```text
http://127.0.0.1:8081/v1/chat/completions
```

The current code expects both services to be available locally.

### Install Python Dependencies

Install the dependencies used by the project:

```bash
pip install streamlit requests pymupdf sqlite-vec rank-bm25
```

### Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in your terminal.

---

## 📚 Using Z1

1. Start your local embedding server.
2. Start your local LLM server.
3. Run:

```bash
streamlit run app.py
```

4. Upload a PDF from the sidebar.
5. Wait for the document to be indexed.
6. Ask a question about the uploaded material.
7. Z1 retrieves relevant passages and generates an answer.
8. Expand **Sources** to see the document and page numbers used.

---

## 🔐 Privacy & Offline Design

One of the core ideas behind Z1 is reducing dependence on cloud AI services.

The project is designed around local processing so that study materials can remain on the user's own computer rather than being uploaded to an external AI service.

The project's stated vision is to make AI-assisted learning accessible in environments where reliable internet connectivity or cloud AI services may not be available or affordable.

> **Your study material. Your machine. Your AI.**

---

## ⚠️ Current Limitations

The current MVP has several limitations.

### No OCR

Scanned or image-based PDFs cannot currently be processed because the system relies on extracted text.

### No Visual Understanding

Diagrams, charts, handwritten notes, and other visual elements are not currently interpreted.

### No Persistent Conversational Memory

Chat history currently exists only within the application session and is not retained after the application closes.

### Shared Knowledge Database

Uploaded PDFs are currently stored in a shared SQLite knowledge base rather than separate subject-specific collections.

### Limited Document Management

Individual PDFs cannot currently be selectively activated, deactivated, or removed without rebuilding the database.

---

## 🛣️ Roadmap

The long-term roadmap includes:

### 📓 Notebook-Based Knowledge Management

Organize documents into separate notebooks or subjects so each course has its own knowledge base.

### 📝 Intelligent Mock Examinations

Generate examinations from uploaded study material and evaluate written answers instead of simply revealing the answer.

### ⏱️ Anti-Procrastination Learning Support

Move beyond passive question answering and actively guide students through focused learning sessions.

### 🧠 Adaptive Learning Assistance

Detect when a student is struggling with a concept and provide hints, simpler explanations, or alternative approaches.

### 👁️ Multimodal Document Understanding

Add support for:

* Diagrams
* Charts
* Tables
* Educational images
* Other visual study material

---

## 🎯 Long-Term Vision

Z1 is intended to evolve beyond a simple PDF chatbot.

The ultimate goal is a **privacy-preserving personal AI tutor** that can understand a user's knowledge, organize information, assist with learning, and eventually act as a personal "second brain."

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

---

## 🤝 Contributing

Contributions, ideas, experiments, and improvements are welcome.

Some areas that would be especially useful:

* Better retrieval/ranking
* OCR support
* Multimodal RAG
* Document management
* Persistent memory
* Subject-based knowledge bases
* Local model optimization
* Mock examination generation
* Learning analytics

---

## 📜 Project Status

**Current status:** MVP / Experimental

Z1 currently demonstrates the core concept of an **offline hybrid RAG study assistant**. The system is functional but intentionally serves as a foundation for the larger vision of a personal offline AI learning companion.

---

## ⭐ Why Z1?

Most AI study tools assume that the user has:

* Reliable internet
* Access to cloud AI services
* Willingness to upload personal documents
* Sufficient connectivity for continuous AI usage

Z1 explores a different approach:

> **What if useful AI learning assistance could run locally on an ordinary personal computer?**

That question is the foundation of Z1.

---

## 📌 License

Add your preferred open-source license here, for example **MIT**, before publishing the repository.

---

**Z1 — Offline AI Study Assistant**

*Learn from your knowledge. Run your AI locally. Build your second brain.*
