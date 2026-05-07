from ETL.EXTRACT.canvas_downloader import CanvasClient
from ETL.LOAD.qdrant_loader import on_new_document
from ETL.TRANSFORM.pdf_to_md import process_pdf_blobs_parallel
from azure.storage.blob import BlobServiceClient
import os
import dotenv

from neon_auth.client import NeonClient


def user_pipeline(user_id: int):

    # Implement intersect pattern to optimize time, i.e. process only new files

    # TODO: mejorar esta mierda que escribi yo

    print("initializing state of user_pipeline", flush=True)
    print(f"USER_ID {user_id}", flush=True)

    # ==State
    dotenv.load_dotenv()

    nc = NeonClient()

    user_data_response = nc.select("users", params={"id": f"eq.{user_id}"})
    if not user_data_response:
        print("Couldnt get user data to start the user_pipeline", flush=True)
        return
    user_canvas_api = user_data_response[0]["canvas_api_token"]
    user_canvas_url = "https://canvas.iteso.mx"  # TODO: make this general

    cc = CanvasClient(canvas_api_token=user_canvas_api, canvas_url=user_canvas_url)

    ac = BlobServiceClient(
        account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
        credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
    )

    # ====Hicimos lo mejor que pudimos profe

    print("BEG SYNC USER TO NEON", flush=True)

    try:
        # sync_user(user_id=user_id, nc=nc, cc=cc)
        pass
    except Exception as e:
        print("The pipeline ended while running sync_user", flush=True)
        raise e

    print("END SYNC USER TO NEON", flush=True)

    user_courses = nc.select("user_courses", params={"user_id": f"eq.{user_id}"})
    course_ids = [uc["course_id"] for uc in user_courses]
    courses = nc.select(
        "courses", params={"id": f"in.({','.join(map(str, course_ids))})"}
    )
    course_codes = {c["code"] for c in courses}
    container_client = ac.get_container_client(os.getenv("AZURE_CONTAINER_RAW"))

    print("===========")
    print("BEGINING OF RAW DATALAKE")
    print("===========")
    try:
        print("-----------========")
        # asyncio.run(upload_user_files(user_id=user_id, nc=nc, ac=ac, canvas_api=user_canvas_api))
    except Exception as e:
        print("The pipeline ended while runing upload_file", flush=True)
        raise e

    print("===========")
    print("END OF  RAW DATALAKE")
    print("===========")

    print("===========")
    print("BEGINING OF Docling")
    print("===========")
    try:
        # TODO do this parallel
        blob_names = [
            blob.name
            for blob in container_client.list_blobs()
            if blob.name.split("/")[0] in course_codes
        ]

        process_pdf_blobs_parallel(blob_names,canvas_token=user_canvas_api)

        # for blob_name in blob_names:
        #     process_pdf_blob(blob_name=blob_name, canvas_token=user_canvas_api)

    except Exception as e:
        print("The pipeline ended while running docling pipeline", flush=True)
        raise e

    print("===========")
    print("END OF  Docling")
    print("===========")

    print("===========")
    print("BEGINING OF QDRANT")
    print("===========")
    try:
        for course in courses:
            course_code = course["code"]
            course_id = course["id"]
            documents = nc.select("documents", params={"course_id": f"eq.{course_id}"})
            for doc in documents:
                on_new_document(course_code=course_code, file_name=doc["filename"])
    except Exception as e:
        print("The pipeline ended while running qdrant pipeline", flush=True)
        raise e

    print("===========")
    print("BEGINING OF QDRANT")
    print("===========")



    print("<><><><><><><><><><><><><><")
    print(f"END OF MAIN PIPELINE OF USER {user_id}") 
