from neon_auth.client import NeonClient
import argparse
import time
import dotenv
import os
from azure.storage.blob import BlobServiceClient
import httpx
import asyncio


def download_file(file_name: str, file_url: str, canvas_token: str) -> bytes:

    headers = {"Authorization": f"Bearer {canvas_token}"}

    r = httpx.get(file_url, headers=headers, follow_redirects=True)
    r.raise_for_status()
    return r.content


def upload_file(
    ac: BlobServiceClient,
    container_name: str,
    file_name: str,
    file_url: str,
    course_code: str,
    file_type: str,
    canvas_api: str,
) -> None:

    content_to_upload = download_file(
        file_name=file_name, file_url=file_url, canvas_token=canvas_api
    )
    blob = ac.get_blob_client(container_name, f"{course_code}/{file_type}/{file_name}")
    blob.upload_blob(content_to_upload, overwrite=True)


async def upload_user_files(
    nc: NeonClient, ac: BlobServiceClient, canvas_api: str, user_id: int
):
    # Get user courses
    user_courses = nc.select("user_courses", params={"user_id": f"eq.{user_id}"})
    if not user_courses:
        print(f"[upload_user_files] No courses found for user {user_id}")
        return

    course_ids = [uc["course_id"] for uc in user_courses]

    # get courses codes
    courses = nc.select(
        "courses", params={"id": f"in.({','.join(map(str, course_ids))})"}
    )
    course_map = {c["id"]: c["code"] for c in courses}

    # TODO: Extend to more than pdfs
    ALLOWED_TYPES = ["pdf", "docx", "pptx", "md"]  

    documents = nc.select(
        "documents",
        params={
            "course_id": f"in.({','.join(map(str, course_ids))})",
            "file_type": f"in.({','.join(ALLOWED_TYPES)})",
        },
    )

    if not documents:
        print(f"[upload_user_files] No documents found for user {user_id}")
        return

    # upload asyncronus
    semaphore = asyncio.Semaphore(5)

    async def upload_one(doc):
        async with semaphore:
            course_code = course_map.get(doc["course_id"])
            if not course_code:
                print(
                    f"[upload_user_files] No course_code for course_id {doc['course_id']}"
                )
                return

            await asyncio.to_thread(
                upload_file,
                ac=ac,
                container_name=os.getenv("AZURE_CONTAINER_RAW"),
                file_name=doc["filename"],
                file_url=doc["file_url"],
                course_code=course_code,
                file_type=doc["file_type"],
                canvas_api=canvas_api,
            )

    await asyncio.gather(
        *[upload_one(doc) for doc in documents], return_exceptions=True
    )


# def main():
#
#     begining_time = time.time()
#
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--course-id", type=int)
#     parser.add_argument("--file-name", type=str)
#     parser.add_argument("--file-url", type=str)
#     parser.add_argument("--file-type", type=str)
#     parser.add_argument("--raw-content", type=bool)
#     args = parser.parse_args()
#
#     course_id = args.course_id
#     file_name = args.file_name
#     file_url = args.file_url
#     file_type = args.file_type
#     raw_content = args.file_type
#
#     COURSES_TABLE_NAME = "courses"
#     CONTAINER_NAME = os.getenv("AZURE_CONTAINER_RAW") if raw_content else os.getenv("AZURE_CONTAINER_PROCESSED")
#
#     dotenv.load_dotenv()
#
#     CANVAS_API = os.getenv("CANVAS_API_TOKEN")
#
#     ### ===> <====
#
#     ALLOWED_TYPES = [".pdf", ".docx", ".pptx", ".md"]
#     if file_type not in ALLOWED_TYPES:
#         print(f"non .pdf /.pptx /.docx /.md file type is not allowed the file_type passed is {file_type}")
#         raise RuntimeError("Aborting because filetype is not allowed")
#
#
#     nc = NeonClient()
#
#     ac = BlobServiceClient(
#         account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
#         credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
#     )
#
#     course_req = nc.select(COURSES_TABLE_NAME, params={"id": f"eq.{course_id}"})
#     course_code = None
#     if course_req:
#         course_code = course_req[0].get("code")
#     else:
#         raise("Couldnt get course info from neon source")
#
#
#     content_to_upload = download_file(
#         file_name=file_name, file_url=file_url, canvas_token=CANVAS_API
#     )
#     upload_file(
#         ac=ac,
#         container_name=CONTAINER_NAME,
#         file_name=file_name,
#         course_code=course_code,
#         content=content_to_upload,
#         file_type=file_type,
#     )
#
#     ### ===> <====
#
#     end_time = time.time()
#     print(f"UPLOAD TO DATALAKE TOOK {end_time - begining_time}")
#

if __name__ == "__main__":
    pass
    #main()
