import os
import sys
from dotenv import load_dotenv
import ollama

from config import client, get_collection_name, get_embedding

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
    query_embedding = get_embedding(question)

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


def ask(course_code: str, course_name: str, question: str):
    chunks = query_course(course_code, question)

    if not chunks:
        yield "No encontré información relevante para tu pregunta en el material del curso."
        return

    context = "\n\n".join([f"[{c['filename']}]\n{c['text']}" for c in chunks])

    system_prompt = (
        f"Eres CapiAPI, un asistente académico del curso '{course_name}' (código: {course_code}) del ITESO. "
        f"Tu único trabajo es ayudar a estudiantes universitarios a entender el material de este curso. "
        f"\n\nREGLAS:"
        f"\n- Responde SIEMPRE en español, de forma clara y accesible para estudiantes de universidad o preparatoria."
        f"\n- Usa ÚNICAMENTE la información del contexto proporcionado. Si algo no está en el contexto, dilo claramente: 'Eso no está en el material del curso'."
        f"\n- NUNCA inventes información, fórmulas, definiciones o ejemplos que no estén en el contexto."
        f"\n- Si el contexto es insuficiente para responder, dilo honestamente y sugiere al estudiante revisar sus apuntes o preguntar al profesor."
        f"\n- Solo menciona el nombre del curso si el estudiante te lo pregunta explícitamente."
        f"\n- Explica los conceptos de forma sencilla, usa ejemplos cuando ayude a entender."
        f"\n- Si hay fórmulas matemáticas, explícalas paso a paso."
    )

    user_prompt = f"CONTEXTO:\n{context}\n\nPREGUNTA:\n{question}"

    stream = ollama_client.chat(
        model="gemma4:latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
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