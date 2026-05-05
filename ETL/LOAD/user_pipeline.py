from ETL.EXTRACT.canvas_downloader import CanvasClient
from ETL.LOAD.upload import upload_file
from ETL.LOAD.qdrant_loader import on_new_document
from ETL.TRANSFORM.pdf_to_md import process_pdf_blob
from ETL.LOAD.sync import sync_user
import asyncio

from neon_auth.client import NeonClient


def user_pipeline(user_id: int):

    # TODO: mejorar esta mierda que escribi yo
    
    #==State
    nc = NeonClient()
    
    user_data_response = nc.select("users",params={"user_id":f"eq.{user_id}"})[0]
    if not user_data_response:
        print("Couldnt get user data to start the user_pipeline")
        return
    user_canvas_api = user_data_response[0]["canvas_api_token"]
    user_canvas_url = "https://canvas.iteso.mx" # TODO: make this general

    cc = CanvasClient(canvas_api_token=user_canvas_api,canvas_url=user_canvas_url)

    #====Hicimos lo mejor que pudimos profe

    try:
        sync_user(user_id=user_id,nc=nc,cc=cc)
    except Exception:
        print("The pipeline ended while running sync_user")
    try:
        upload_file() # aqui 
    except Exception:
        print("The pipeline ended while runing upload_file")
