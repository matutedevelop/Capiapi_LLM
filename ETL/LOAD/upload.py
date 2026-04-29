from neon_auth.client import NeonClient
import argparse
import time
import dotenv
import os
from azure.storage.blob import BlobServiceClient
import httpx


def download_file(file_name: str, file_url: str, canvas_token: str) -> bytes:

    headers = {"Authorization": f"Bearer {canvas_token}"}

    r = httpx.get(file_url, headers=headers, follow_redirects=True)
    r.raise_for_status()
    return r.content


def upload_file(
    ac: BlobServiceClient,
    container_name: str,
    file_name: str,
    file_url :str,
    course_code: str,
    file_type: str,
    canvas_api:str
) -> None:
    content_to_upload = download_file(
        file_name=file_name, file_url=file_url, canvas_token=canvas_api
    )
    blob = ac.get_blob_client(
        container_name, f"{course_code}/{file_type}/{file_name}"
    )
    blob.upload_blob(content_to_upload, overwrite=True)


def main():

    begining_time = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--course-id", type=int)
    parser.add_argument("--file-name", type=str)
    parser.add_argument("--file-url", type=str)
    parser.add_argument("--file-type", type=str)
    parser.add_argument("--raw-content", type=bool)
    args = parser.parse_args()

    course_id = args.course_id
    file_name = args.file_name
    file_url = args.file_url
    file_type = args.file_type
    raw_content = args.file_type

    COURSES_TABLE_NAME = "courses"
    CONTAINER_NAME = os.getenv("AZURE_CONTAINER_RAW") if raw_content else os.getenv("AZURE_CONTAINER_PROCESSED")

    dotenv.load_dotenv()

    CANVAS_API = os.getenv("CANVAS_API_TOKEN")

    ### ===> <====

    if file_type not in [".pdf",".md"]:
        print(f"non PDF file type is not allowed the file_type passed is {file_type}")
        raise RuntimeError("Aborting because filetype is not allowed")


    nc = NeonClient()

    ac = BlobServiceClient(
        account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
        credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
    )

    course_req = nc.select(COURSES_TABLE_NAME, params={"id": f"eq.{course_id}"})
    course_code = None
    if course_req:
        course_code = course_req[0].get("code")
    else:
        raise("Couldnt get course info from neon source")
    

    content_to_upload = download_file(
        file_name=file_name, file_url=file_url, canvas_token=CANVAS_API
    )
    upload_file(
        ac=ac,
        container_name=CONTAINER_NAME,
        file_name=file_name,
        course_code=course_code,
        content=content_to_upload,
        file_type=file_type,
    )

    ### ===> <====

    end_time = time.time()
    print(f"UPLOAD TO DATALAKE TOOK {end_time - begining_time}")


if __name__ == "__main__":
    main()

