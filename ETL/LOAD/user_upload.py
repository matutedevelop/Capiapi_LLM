import pandas as pd
from canvas_downloader import CanvasDownloader
import argparse
from neon_auth.client import NeonClient

description = """
este archivo es el pipeline que recibe un usuario y su canvas_api_token
"""

parser = argparse.ArgumentParser(description=description)

parser.add_argument("canvas_api",type=str)
parser.add_argument("user_mail",type=str)

args = parser.parse_args()


# TODO: make it work for any U
canvas_url = "https://canvas.iteso.mx"

canvas_manager = CanvasDownloader(canvas_api_token=args.canvas_api,canvas_url=canvas_url)




# === === === === === === === === === === === ===
# Update Courses Table
# === === === === === === === === === === === ===

user_courses = canvas_manager.get_user_courses()
database_courses = NeonClient.select()

