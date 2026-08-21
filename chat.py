import requests
from retrieve import retrieve

# Local LLM API endpoint for chat completions.
LLM_URL = "http://127.0.0.1:8081/v1/chat/completions"

# Instruction used to keep the assistant grounded in the uploaded documents.
SYSTEM_PROMPT = """
You are Z1, an offline AI study assistant.

Rules:
- Answer ONLY from the provided context.
- If the answer is missing, say:
  "The answer is not available in the uploaded documents."
- Explain clearly and briefly.
"""

# Retrieve the most relevant context for a question and send it to the model.
def ask(question: str):
    # Fetch the best matching document chunks from the hybrid retrieval pipeline.
    results = retrieve(question)

    if not results:
        return {
            "answer": "The answer is not available in the uploaded documents.",
            "sources": []
        }

    # Combine the retrieved chunks into a single context block for the LLM.
    context = "\n\n".join(
        f"[Source: {source} | Page: {page}]\n{text}"
        for source, page, text in results
    )

    # Build the OpenAI-style payload for the local chat-completion service.
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{question}"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 512
    }

    # Send the query to the local LLM service and raise an error if it fails.
    response = requests.post(LLM_URL, json=payload)
    response.raise_for_status()

    # Extract the generated answer from the model response.
    answer = response.json()["choices"][0]["message"]["content"]

    # Keep only the source names and page numbers for UI display.
    sources = [
        {"source": source, "page": page}
        for source, page, _ in results
    ]

    return {
        "answer": answer,
        "sources": sources
    }