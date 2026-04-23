from neon_auth.client import NeonClient
from ETL.EXTRACT.canvas_downloader import CanvasClient
import argparse
import pandas as pd

import os
import dotenv


def sync_courses(cc: CanvasClient, nc: NeonClient, user_id: int) -> None:
    canvas_course_names = cc.get_user_courses()

    course_table_name = "courses"
    user_courses_table_name = "user_courses"

    data = nc.select(user_courses_table_name + f"?user_id=eq.{user_id}")

    if isinstance(data, dict):
        data = [data]

    user_courses_db = pd.DataFrame(data)

    user_courses_canvas = cc.get_user_courses()

    print(user_courses_db.columns)



def main():
    pass


if __name__ == "__main__":
    pass

    dotenv.load_dotenv()

    CANVAS_API = os.getenv("CANVAS_API_TOKEN")
    CANVAS_URL = os.getenv("CANVAS_URL")

    cc = CanvasClient(CANVAS_API, CANVAS_URL)
    nc = NeonClient()

    sync_courses(cc,nc,1)

    

