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
    Busca los chunks más relevantes para una pregunta en la colección del curso.
    
    Parámetros:
        course_code: código del curso ej. 'P2025_MAF1121H2'
        question: pregunta del usuario
        top_k: número de chunks a retornar
    """
    collection_name = get_collection_name(course_code)

    # Embed la pregunta — usamos RETRIEVAL_QUERY para búsquedas
    query_embedding = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=question,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    ).embeddings[0].values

    # Buscar en Qdrant
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
    Hace una pregunta sobre un curso y retorna la respuesta del LLM.
    """
    # Recuperar contexto relevante
    chunks = query_course(course_code, question)

    if not chunks:
        yield "No encontré información relevante para tu pregunta."
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