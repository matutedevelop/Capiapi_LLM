from ETL.EXTRACT.azure_getter import download_blob_to_stream
from azure.storage.blob import BlobServiceClient
from neon_auth.client import NeonClient
import argparse
import time
import dotenv
import os
import httpx
import io
from azure.storage.blob import BlobServiceClient


dotenv.load_dotenv()

ac = BlobServiceClient(
    account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
    credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
)


def download_blob_to_stream(ac, container_name, blob_name):
    """
    Descarga un blob y devuelve un flujo de bytes en memoria.
    """
    try:
        # Inicializar el cliente
        blob_client = ac.get_blob_client(
            container=container_name, blob=blob_name
        )

        # Crear un buffer en memoria
        byte_stream = io.BytesIO()

        print(f"Iniciando descarga de: {blob_name}...")

        # Descargar los datos al stream
        download_stream = blob_client.download_blob()
        download_stream.readinto(byte_stream)

        # Reposicionar el puntero al inicio para que pueda ser leído después
        byte_stream.seek(0)

        print("Descarga completada.")
        return byte_stream

    except Exception as e:
        print(f"Error al descargar el archivo: {e}")
        return None
