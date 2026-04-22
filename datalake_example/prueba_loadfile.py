from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import os

load_dotenv()

client = BlobServiceClient(
    account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
    credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
)

container = os.getenv("AZURE_CONTAINER_RAW")

# Upload a file
def upload():
    blob = client.get_blob_client(container, "test/hello.txt")
    blob.upload_blob("hola desde Azure!", overwrite=True)
    print("Archivo subido")

# List files
def list_files():
    container_client = client.get_container_client(container)
    blobs = list(container_client.list_blobs())
    if not blobs:
        print("Container vacío")
    for b in blobs:
        print(f"  {b.name}  ({b.size} bytes)")

# download and read
def download():
    blob = client.get_blob_client(container, "test/hello.txt")
    contenido = blob.download_blob().readall().decode("utf-8")
    print(f"Contenido: {contenido}")

# delete a file
def delete():
    blob = client.get_blob_client(container, "test/hello.txt")
    blob.delete_blob()
    print("Archivo eliminado")


if __name__ == '__main__':
    upload()
    list_files()
    download()
    delete()
    list_files() 