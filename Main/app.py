import streamlit as st
import os
import subprocess
import sys
from chat import ask

# ---------------- CONFIG ---------------- #

# App metadata and page layout for the Streamlit UI.
st.set_page_config(
    page_title="Z1 Study AI",
    page_icon="📘",
    layout="wide"
)

# Folder where uploaded PDFs are stored before indexing.
BOOKS_DIR = "books"
os.makedirs(BOOKS_DIR, exist_ok=True)

# ---------------- SESSION ---------------- #

# Keep the chat history in the browser session so the conversation persists.
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- SIDEBAR ---------------- #

with st.sidebar:
    st.title("📘 Z1 Study AI")
    st.caption("Offline Hybrid RAG")

    st.divider()
    st.subheader("Upload PDF")

    # Upload a PDF, save it locally, then rebuild the database index.
    uploaded = st.file_uploader(
        "Choose a PDF",
        type=["pdf"]
    )

    if uploaded is not None:
        save_path = os.path.join(BOOKS_DIR, uploaded.name)

        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())

        with st.spinner("Creating RAG..."):
            subprocess.run(
                [sys.executable, "ingest.py"],
                check=True
            )

        st.success(f"{uploaded.name} indexed!")

    st.divider()

    # Reset the current chat conversation without touching the uploaded files.
    if st.button("🗑 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------- HEADER ---------------- #

st.title("📘 Z1 Study AI")
st.caption("Ask questions from your uploaded documents")

# ---------------- CHAT HISTORY ---------------- #

# Render previous user/assistant messages and their source citations.
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("Sources"):
                for src in msg["sources"]:
                    st.write(f"**{src['source']}** — Page {src['page']}")

# ---------------- INPUT ---------------- #

# Receive the latest prompt from the user and answer it with the RAG pipeline.
prompt = st.chat_input("Ask anything...")

if prompt:

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):
            result = ask(prompt)

        st.markdown(result["answer"])

        if result["sources"]:
            with st.expander("Sources"):
                for src in result["sources"]:
                    st.write(f"**{src['source']}** — Page {src['page']}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })