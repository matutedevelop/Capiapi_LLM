import os
import sys
from dotenv import load_dotenv
from google.genai import types
import ollama

sys.path.append(os.path.join(os.path.dirname(__file__), '../../qdrant'))
from config import client, get_collection_name, get_embedding, genai_client

load_dotenv()

ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))


def query_course(course_code: str, question: str, top_k: int = 5) -> list[dict]:
    """
    Searches the course collection for the most relevant chunks related to a question.
    
    Parameters:
        course_code: course code, e.g., 'P2025_MAF1121H2'
        question: user's question
        top_k: number of chunks to return
    """
    collection_name = get_collection_name(course_code)

    # Embed the question 
    query_embedding = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=question,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    ).embeddings[0].values

    # search Qdrant
    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=top_k,
        with_payload=True
    )

    return [
        {
            "score": r.score,
            "text": r.payload["text"],
            "filename": r.payload["filename"],
            "chunk_index": r.payload["chunk_index"],
        }
        for r in results.points
    ]


def ask(course_code: str, question: str) -> str:
    """
    You ask a question about a course, and the LLM returns the answer.
    """
    # Retrieve relevant context
    chunks = query_course(course_code, question)

    if not chunks:
        yield "I couldn't find any relevant information for your question."
        return

    context = "\n\n".join([f"[{c['filename']}]\n{c['text']}" for c in chunks])

    prompt = f"""Eres un asistente académico. Usa el siguiente contexto para responder la pregunta del estudiante.
Si la respuesta no está en el contexto, dilo claramente.

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:"""

    stream = ollama_client.chat(
        model="gemma4:26b",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        yield chunk["message"]["content"]


# if __name__ == "__main__":
#     respuesta = ask(
#         course_code="P2025_MAF1121H2",
#         question="Que onda tengo la siguiente duda, que son los z-scores?"
#     )
#     print(respuesta)

# Stream
if __name__ == "__main__":
    for chunk in ask(
        course_code="P2025_MAF1121H2",
        question="Que onda tengo la siguiente duda, que son los z-scores?"
    ):
        print(chunk, end="", flush=True)