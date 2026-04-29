from azure.storage.blob import BlobServiceClient
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from ETL.LOAD.upload import upload_file
import argparse
import tempfile
import time
import dotenv
import os
import io

dotenv.load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
raw_container_name       = os.getenv("AZURE_CONTAINER_RAW")
processed_container_name = os.getenv("AZURE_CONTAINER_PROCESSED")

ac = BlobServiceClient(
    account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
    credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
)


# ─── DOWNLOAD ─────────────────────────────────────────────────────────────────
def download_blob_to_stream(ac, blob_name, container_name=raw_container_name):
    try:
        blob_client = ac.get_blob_client(container=container_name, blob=blob_name)
        byte_stream = io.BytesIO()
        print(f"Iniciando descarga de: {blob_name}...")
        blob_client.download_blob().readinto(byte_stream)
        byte_stream.seek(0)
        print("Descarga completada.")
        return byte_stream
    except Exception as e:
        print(f"Error al descargar el archivo: {e}")
        return None


# ─── CONFIDENCE SCORE ─────────────────────────────────────────────────────────
def get_confidence_score(result) -> float:
    scores = []
    for element, _ in result.document.iterate_items():
        prov = getattr(element, "prov", None)
        if prov:
            for p in prov:
                conf = getattr(p, "confidence", None)
                if conf is not None:
                    scores.append(conf)
    if not scores:
        return 1.0
    return round(sum(scores) / len(scores), 4)


# ─── CHUNKING ─────────────────────────────────────────────────────────────────
def apply_chunking(result) -> tuple[int, str]:
    """
    Aplica chunking al documento.
    Retorna (total de chunks, chunks en formato Markdown)
    """
    chunker = HybridChunker()
    chunks  = list(chunker.chunk(result.document))

    md_lines = ["# Chunks\n"]

    for i, chunk in enumerate(chunks):
        headings = chunk.meta.headings if chunk.meta else []
        try:
            page = chunk.meta.doc_items[0].prov[0].page_no \
                   if chunk.meta and chunk.meta.doc_items \
                   and chunk.meta.doc_items[0].prov else None
        except Exception:
            page = None

        heading_str = " > ".join(headings) if headings else "Sin encabezado"
        page_str    = f"Página {page}" if page else "Página desconocida"
        md_lines.append(f"## Chunk {i + 1} — {heading_str} ({page_str})\n")
        md_lines.append(f"{chunk.text}\n")
        md_lines.append("---\n")

    return len(chunks), "\n".join(md_lines)


# ─── TRANSFORM ────────────────────────────────────────────────────────────────
def convert_stream_to_markdown(byte_stream: io.BytesIO, filename: str):
    """
    Convierte un stream de bytes PDF a Markdown usando docling.
    Retorna (markdown, confidence, total_chunks, chunks_md) o Nones si falla.
    """
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    try:
        with open(tmp_path, "wb") as f:
            f.write(byte_stream.read())

        converter  = DocumentConverter()
        result     = converter.convert(tmp_path)
        markdown   = result.document.export_to_markdown()
        confidence = get_confidence_score(result)
        total_chunks, chunks_md = apply_chunking(result)

        print(f"  Confidence score : {confidence:.2%}")
        print(f"  Chunks generados : {total_chunks}")
        print(f"  Conversion completada: {filename}")

        return markdown, confidence, total_chunks, chunks_md

    except Exception as e:
        print(f"Error al convertir {filename}: {e}")
        return None, None, None, None

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─── PIPELINE ─────────────────────────────────────────────────────────────────
def process_pdf_blob(blob_name: str) -> bool:
    """
    Pipeline completo:
        1. Descarga PDF del contenedor RAW
        2. Convierte a Markdown con docling
        3. Imprime confidence score y numero de chunks
        4. Sube 2 archivos al contenedor PROCESSED:
            - {nombre}.md        → Markdown completo
            - {nombre}_chunks.md → Chunks en formato Markdown
    """
    print(f"\n{'='*50}")
    print(f"Procesando: {blob_name}")

    # 1. Descargar
    byte_stream = download_blob_to_stream(ac, blob_name)
    if byte_stream is None:
        print(f"[ERROR] No se pudo descargar {blob_name}")
        return False

    # 2. Convertir
    filename    = blob_name.split("/")[-1]
    course_code = blob_name.split("/")[0]
    markdown, confidence, total_chunks, chunks_md = convert_stream_to_markdown(byte_stream, filename)

    if markdown is None:
        print(f"[ERROR] No se pudo convertir {blob_name}")
        return False

    base_name      = filename.rsplit(".", 1)[0]
    md_filename    = base_name + ".md"
    chunks_md_file = base_name + "_chunks.md"

    # 3. Subir Markdown completo
    upload_file(
        ac=ac, container_name=processed_container_name,
        file_name=md_filename, course_code=course_code,
        file_type=".md", content=markdown.encode("utf-8"),
    )

    # 4. Subir chunks en Markdown
    upload_file(
        ac=ac, container_name=processed_container_name,
        file_name=chunks_md_file, course_code=course_code,
        file_type=".md", content=chunks_md.encode("utf-8"),
    )

    print(f"[OK] {blob_name}")
    print(f"     Markdown        : {course_code}/.md/{md_filename}")
    print(f"     Chunks Markdown : {course_code}/.md/{chunks_md_file}")
    print(f"     Confidence      : {confidence:.2%}")
    return True


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Convierte PDFs del datalake RAW a Markdown en PROCESSED."
    )
    parser.add_argument(
        "--blob", type=str, required=True,
        help="Nombre del blob (ej: P2025_MAF1121H2/.pdf/repaso1v1.pdf)",
    )
    args = parser.parse_args()

    start   = time.time()
    success = process_pdf_blob(args.blob)
    elapsed = time.time() - start

    print(f"\n{'='*50}")
    print(f"Estado  : {'OK' if success else 'FAILED'}")
    print(f"Tiempo  : {elapsed:.2f}s")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()