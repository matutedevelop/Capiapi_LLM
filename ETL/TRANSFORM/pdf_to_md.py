from azure.storage.blob import BlobServiceClient
from docling.document_converter import DocumentConverter
from ETL.LOAD.upload import upload_file
import tempfile
import dotenv
import os
import io



# ─── DOWNLOAD ─────────────────────────────────────────────────────────────────
def download_blob_to_stream(ac, blob_name, container_name=None):

    container_name = container_name or os.getenv("AZURE_CONTAINER_RAW")

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


# ─── TRANSFORM ────────────────────────────────────────────────────────────────
def convert_stream_to_markdown(byte_stream: io.BytesIO, filename: str):
    """
    Convierte un stream de bytes PDF a Markdown usando docling.
    Retorna (markdown, confidence) o (None, None) si falla.
    """
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    try:
        with open(tmp_path, "wb") as f:
            f.write(byte_stream.read())

        converter  = DocumentConverter()
        result     = converter.convert(tmp_path)
        markdown   = result.document.export_to_markdown()
        confidence = get_confidence_score(result)

        print(f"  Confidence score : {confidence:.2%}")
        print(f"  Conversion completada: {filename}")

        return markdown, confidence

    except Exception as e:
        print(f"Error al convertir {filename}: {e}")
        return None, None

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─── PIPELINE ─────────────────────────────────────────────────────────────────
def process_pdf_blob(blob_name: str) -> bool:
    """
    Pipeline completo:
        1. Descarga PDF del contenedor RAW
        2. Convierte a Markdown con docling
        3. Imprime confidence score
        4. Sube el .md al contenedor PROCESSED
    """

    # ==========


    dotenv.load_dotenv()

    # ─── CONFIG ───────────────────────────────────────────────────────────────────
    raw_container_name       = os.getenv("AZURE_CONTAINER_RAW")
    processed_container_name = os.getenv("AZURE_CONTAINER_PROCESSED")

    ac = BlobServiceClient(
        account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
        credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
    )


    # ++++++++++++++

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
    markdown, confidence = convert_stream_to_markdown(byte_stream, filename)

    if markdown is None:
        print(f"[ERROR] No se pudo convertir {blob_name}")
        return False

    # 3. Subir Markdown
    md_filename = filename.rsplit(".", 1)[0] + ".md"
    upload_file(
        ac=ac, container_name=processed_container_name,
        file_name=md_filename, course_code=course_code,
        file_type=".md", content=markdown.encode("utf-8"),
    )

    print(f"[OK] {blob_name}")
    print(f"     Markdown   : {course_code}/.md/{md_filename}")
    print(f"     Confidence : {confidence:.2%}")
    return True


# ─── MAIN ─────────────────────────────────────────────────────────────────────
# def main():
#     parser = argparse.ArgumentParser(
#         description="Convierte PDFs del datalake RAW a Markdown en PROCESSED."
#     )
#     parser.add_argument(
#         "--blob", type=str, required=True,
#         help="Nombre del blob (ej: P2025_MAF1121H2/.pdf/repaso1v1.pdf)",
#     )
#     args = parser.parse_args()
#
#     start   = time.time()
#     success = process_pdf_blob(args.blob)
#     elapsed = time.time() - start
#
#     print(f"\n{'='*50}")
#     print(f"Estado  : {'OK' if success else 'FAILED'}")
#     print(f"Tiempo  : {elapsed:.2f}s")
#     print(f"{'='*50}")


if __name__ == "__main__":
    pass
   # main()
