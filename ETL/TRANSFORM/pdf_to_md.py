from azure.storage.blob import BlobServiceClient
from neon_auth.client import NeonClient
from docling.document_converter import DocumentConverter
import argparse
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
    """
    Descarga un blob y devuelve un flujo de bytes en memoria.
    """
    try:
        blob_client = ac.get_blob_client(
            container=container_name, blob=blob_name
        )
        byte_stream = io.BytesIO()
        print(f"Iniciando descarga de: {blob_name}...")
        download_stream = blob_client.download_blob()
        download_stream.readinto(byte_stream)
        byte_stream.seek(0)
        print("Descarga completada.")
        return byte_stream
 
    except Exception as e:
        print(f"Error al descargar el archivo: {e}")
        return None
 
 
# ─── TRANSFORM ────────────────────────────────────────────────────────────────
def convert_stream_to_markdown(byte_stream: io.BytesIO, filename: str) -> str:
    """
    Toma un stream de bytes de un PDF y lo convierte a Markdown usando docling.
    Guarda temporalmente el archivo en disco porque docling necesita una ruta.
    """
    # docling necesita un archivo en disco, no acepta streams directamente
    import tempfile
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
 
    try:
        with open(tmp_path, "wb") as f:
            f.write(byte_stream.read())
 
        converter = DocumentConverter()
        result = converter.convert(tmp_path)
        markdown = result.document.export_to_markdown()
        print(f"Conversión completada: {filename}")
        return markdown
 
    except Exception as e:
        print(f"Error al convertir {filename}: {e}")
        return None
 
    finally:
        # Limpia el archivo temporal
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
 
 
# ─── UPLOAD ───────────────────────────────────────────────────────────────────
def upload_markdown_to_processed(ac, blob_name: str, markdown_content: str) -> None:
    """
    Sube el contenido Markdown al contenedor procesado en Azure.
    El blob_name debe terminar en .md
    """
    try:
        blob_client = ac.get_blob_client(
            container=processed_container_name, blob=blob_name
        )
        blob_client.upload_blob(
            markdown_content.encode("utf-8"),
            overwrite=True
        )
        print(f"Subido a procesado: {processed_container_name}/{blob_name}")
 
    except Exception as e:
        print(f"Error al subir {blob_name}: {e}")
 
 
# ─── PIPELINE ─────────────────────────────────────────────────────────────────
def process_pdf_blob(blob_name: str) -> bool:
    """
    Pipeline completo para un blob:
        1. Descarga el PDF del contenedor RAW
        2. Convierte a Markdown con docling
        3. Sube el .md al contenedor PROCESSED
 
    Retorna True si todo salió bien, False si algo falló.
    """
    print(f"\n{'='*50}")
    print(f"Procesando: {blob_name}")
 
    # 1. Descargar
    byte_stream = download_blob_to_stream(ac, blob_name)
    if byte_stream is None:
        print(f"[ERROR] No se pudo descargar {blob_name}")
        return False
 
    # 2. Convertir
    filename = blob_name.split("/")[-1]  # ej: "archivo.pdf"
    markdown = convert_stream_to_markdown(byte_stream, filename)
    if markdown is None:
        print(f"[ERROR] No se pudo convertir {blob_name}")
        return False
 
    # 3. Subir como .md
    md_blob_name = blob_name.rsplit(".", 1)[0] + ".md"  # cambia .pdf → .md
    upload_markdown_to_processed(ac, md_blob_name, markdown)
 
    print(f"[OK] {blob_name} → {md_blob_name}")
    return True
 
 
# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Convierte PDFs del datalake RAW a Markdown en PROCESSED."
    )
    parser.add_argument(
        "--blob",
        type=str,
        required=True,
        help="Nombre del blob a procesar (ej: 'P2025_MAF1121H2/archivo.pdf')",
    )
    args = parser.parse_args()
 
    start = time.time()
    success = process_pdf_blob(args.blob)
    elapsed = time.time() - start
 
    print(f"\n{'='*50}")
    print(f"Estado  : {'OK' if success else 'FAILED'}")
    print(f"Tiempo  : {elapsed:.2f}s")
    print(f"{'='*50}")
 
 
if __name__ == "__main__":
    main()