from ETL.EXTRACT.canvas_downloader import CanvasClient
from ETL.LOAD.qdrant_loader import on_new_document
from ETL.LOAD.sync import sync_user
from ETL.TRANSFORM.pdf_to_md import process_pdf_blobs_parallel
from ETL.LOAD.upload import upload_user_files
from azure.storage.blob import BlobServiceClient
import os
import dotenv
import asyncio
import time
from neon_auth.client import NeonClient
import argparse


def user_pipeline(user_id: int):

    # Implement intersect pattern to optimize time, i.e. process only new files

    # TODO: mejorar esta mierda que escribi yo

    print("initializing state of user_pipeline", flush=True)
    print(f"USER_ID {user_id}", flush=True)
    total_start = time.perf_counter()

    # ==State
    dotenv.load_dotenv()

    nc = NeonClient()

    user_data_response = nc.select("users", params={"id": f"eq.{user_id}"})
    if not user_data_response:
        print("Couldnt get user data to start the user_pipeline", flush=True)
        return
    print(f"{user_data_response=}", flush=True)
    user_canvas_api = user_data_response[0]["canvas_api_token"]
    user_canvas_url = "https://canvas.iteso.mx"  # TODO: make this general

    cc = CanvasClient(canvas_api_token=user_canvas_api, canvas_url=user_canvas_url)

    ac = BlobServiceClient(
        account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
        credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
    )

    # ====Hicimos lo mejor que pudimos profe

    print("BEG SYNC USER TO NEON", flush=True)
    start = time.perf_counter()
    try:
        sync_user(user_id=user_id, nc=nc, cc=cc)

    except Exception as e:
        print("The pipeline ended while running sync_user", flush=True)
        raise e

    end = time.perf_counter()
    print(f"NEON TOOK {end - start}s")
    print("END SYNC USER TO NEON", flush=True)

    user_courses = nc.select("user_courses", params={"user_id": f"eq.{user_id}"})
    course_ids = [uc["course_id"] for uc in user_courses]
    courses = nc.select(
        "courses", params={"id": f"in.({','.join(map(str, course_ids))})"}
    )
    course_codes = {c["code"] for c in courses}
    container_client = ac.get_container_client(os.getenv("AZURE_CONTAINER_RAW"))

    print("===========")
    print("BEGINING OF RAW DATALAKE", flush=True)
    print("===========")
    start = time.perf_counter()
    try:
        asyncio.run(
            upload_user_files(user_id=user_id, nc=nc, ac=ac, canvas_api=user_canvas_api)
        )
    except Exception as e:
        print("The pipeline ended while runing upload_file", flush=True)
        raise e

    end = time.perf_counter()

    print("===========")
    print("END OF  RAW DATALAKE")
    print(f"RAW DATALAKE TOOK {end - start}s")
    print("===========")

    print("===========")
    print("BEGINING OF Docling")
    print("===========")
    start = time.perf_counter()
    try:
        # TODO do this parallel
        blob_names = [
            blob.name
            for blob in container_client.list_blobs()
            if blob.name.split("/")[0] in course_codes
        ]

        process_pdf_blobs_parallel(blob_names, canvas_token=user_canvas_api)

    except Exception as e:
        print("The pipeline ended while running docling pipeline", flush=True)
        raise e

    end = time.perf_counter()
    print("===========")
    print("END OF  Docling")
    print(f"Docling TOOK {end - start}s")
    print("===========")

    print("===========")
    print("BEGINING OF QDRANT")
    print("===========")
    start = time.perf_counter()
    try:
        allowed_types = ['".pdf"', '".docx"', '".pptx"', '".md"']
        for course in courses:
            course_code = course["code"]
            course_id = course["id"]
            documents = nc.select(
                "documents",
                params={
                    "course_id": f"eq.{course_id}",
                    "file_type": f"in.({','.join(allowed_types)})",
                    "loaded": "eq.false",
                },
            )
            print(":::::::::" + documents,flush=True)

            n_documents = len(documents)

            loaded_filenames = []

            for i, doc in enumerate(documents):
                print(f"course:{doc['course_id']}, filename:{doc['filename']}")
                print(f"[QDRANT] ==== processing {i + 1}/{n_documents} ====")
                print("=====")
                loaded_filename = on_new_document(
                    course_code=course_code, filename=doc["filename"]
                )
                if loaded_filename is not None:
                    loaded_filenames.append(loaded_filename)

            if loaded_filenames:
                nc.update(
                    table="documents",
                    params={"filename": f"in.({','.join(loaded_filenames)})"},
                    data={"loaded": True},
                )

    except Exception as e:
        print("The pipeline ended while running qdrant pipeline", flush=True)
        raise e

    end = time.perf_counter()
    print("===========")
    print("END OF QDRANT")
    print(f"QDRANT TOOK {end - start}s")
    print("===========")
    total_end = time.perf_counter()
    print("<><><><><><><><><><><><><><")
    print(f"END OF MAIN PIPELINE OF USER {user_id}")
    print(f"=====  TOOK {total_end - total_start // 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user-id")
