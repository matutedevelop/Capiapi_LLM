from azure.storage.blob import BlobServiceClient
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PipelineOptions, AcceleratorOptions
from docling.datamodel.base_models import AcceleratorDevice
from ETL.LOAD.upload import upload_file
import tempfile
import dotenv
import os
import io
from concurrent.futures import ThreadPoolExecutor, as_completed



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

        pipeline_options = PipelineOptions(
            accelerator_options=AcceleratorOptions(
                num_threads=4,
                device=AcceleratorDevice.CUDA
            )
        )

        converter = DocumentConverter(pipeline_options=pipeline_options)
        result = converter.convert(tmp_path)
        markdown = result.document.export_to_markdown()
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
def process_pdf_blob(blob_name: str, canvas_token: str) -> bool:
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
    processed_container_name = os.getenv("AZURE_CONTAINER_PROCESSED")

    ac = BlobServiceClient(
        account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
        credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
    )

    # ++++++++++++++

    print(f"\n{'=' * 50}")
    print(f"[docling] processing: {blob_name}")

    # 1. Download
    byte_stream = download_blob_to_stream(ac, blob_name)
    if byte_stream is None:
        print(f"[docling][ERROR] couldnt download {blob_name}")
        return False

    # 2.  convert
    filename = blob_name.split("/")[-1]
    course_code = blob_name.split("/")[0]
    markdown, confidence = convert_stream_to_markdown(byte_stream, filename)

    if markdown is None:
        print(f"[docling][ERROR] couldnt convert {blob_name}")
        return False

    # 3. upload
    md_filename = filename.rsplit(".", 1)[0] + ".md"


    upload_file(
        ac=ac,
        container_name=processed_container_name,
        file_name=md_filename,
        course_code=course_code,
        file_type=".md",
        content=markdown.encode("utf-8"),
        canvas_api=canvas_token,
    )

    print(f"[OK] {blob_name}")
    print(f"     Markdown   : {course_code}/.md/{md_filename}")
    print(f"     Confidence : {confidence:.2%}")
    return True


def process_pdf_blobs_parallel(
    blob_names: list[str],
    canvas_token: str,
    max_workers: int = 1,
) -> dict:
    """
    parallel process of docling blobs and upload
    """
    results = {}
    print(f"[docling] Processing {len(blob_names)} blobs with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_pdf_blob, blob_name, canvas_token): blob_name
            for blob_name in blob_names
        }
        for future in as_completed(futures):
            blob_name = futures[future]
            try:
                results[blob_name] = future.result()
            except Exception as e:
                print(f"[docling] FAILED {blob_name}: {type(e).__name__}: {e}", flush=True)
                results[blob_name] = False

    succeeded = sum(1 for v in results.values() if v)
    failed = len(results) - succeeded
    print(f"[docling] Done: {succeeded} OK, {failed} FAILED")
    return results

if __name__ == "__main__":
    pass
# main()
