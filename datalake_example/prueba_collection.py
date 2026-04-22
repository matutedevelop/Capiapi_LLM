from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import os

load_dotenv()

client = BlobServiceClient(
    account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
    credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
)

containers = [c["name"] for c in client.list_containers()]
print(containers)

# Take a look at the containers we have in our data lake