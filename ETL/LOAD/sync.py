from neon_auth.client import NeonClient
from ETL.EXTRACT.canvas_downloader import CanvasClient
import argparse
import pandas as pd
import time

import os
import dotenv


def sync_courses(cc: CanvasClient, nc: NeonClient, user_id: int) -> None:
    canvas_course_names = cc.get_user_courses()

    course_table_name = "courses"
    user_courses_table_name = "user_courses"

    data_db = nc.select(user_courses_table_name, params={"user_id": f"eq.{user_id}"})

    user_courses_db = (
        pd.DataFrame(data_db)
        if len(data_db) > 0
        else pd.DataFrame({"user_id": [], "course_id": [], "id": []})
    )


    map_code_id_db = {}
    for course_id in user_courses_db["course_id"]:
        course = nc.select(course_table_name, params={"id": f"eq.{course_id}"})
        if course:
            map_code_id_db[course[0]["code"]] = course[0]["id"]
    canvas_df = cc.get_user_courses()
    canvas_codes = set(canvas_df["class_code"])

    db_codes = set(map_code_id_db.keys())
    to_insert = canvas_codes - db_codes
    to_delete = db_codes - canvas_codes

    for insert_code in to_insert:
        courses_to_insert_name = canvas_df.loc[
            canvas_df["class_code"] == insert_code, "class_name"
        ].values[0]
        data_to_insert_courses = {"code": insert_code, "name": courses_to_insert_name}
        course = nc.insert(course_table_name, data=data_to_insert_courses)

        course_id = map_code_id_db.get(
            insert_code,
            nc.select(course_table_name, params={"code": f"eq.{insert_code}"})[0]["id"],
        )

        data_to_insert_user_courses = {"course_id": course_id, "user_id": user_id}
        nc.insert(user_courses_table_name, data=data_to_insert_user_courses)


    for delete_code in to_delete:
        course_id = map_code_id_db[delete_code]

        nc.delete(user_courses_table_name, params={"course_id": f"eq.{course_id}"})
        nc.delete(course_table_name, params={"code": f"eq.{delete_code}"})


def sync_documents(cc: CanvasClient, nc: NeonClient, user_id: int) -> None:

    user_courses_table_name = "user_courses"
    courses_table_name = "courses"
    documents_table_name = "documents"

    # build maping class_code -> course_id
    user_courses_data_db = nc.select(
        user_courses_table_name, params={"user_id": f"eq.{user_id}"}
    )
    user_courses_df = (
        pd.DataFrame(user_courses_data_db)
        if len(user_courses_data_db) > 0
        else pd.DataFrame({"user_id": [], "course_id": [], "id": []})
    )
    map_code_id_db = {}
    for course_id in user_courses_df["course_id"]:
        course = nc.select(courses_table_name, params={"id": f"eq.{course_id}"})
        if course:
            map_code_id_db[course[0]["code"]] = course[0]["id"]


    canvas_df, problematic_courses = cc.get_course_file_name(map_code_id_db.keys())

    # Some courses cant be scraped with canvas-downloader binary, so we take them apart
    for code in problematic_courses:
        course_id = map_code_id_db.get(code)
        if not course_id:
            continue
        nc.delete(user_courses_table_name, params={"course_id": f"eq.{course_id}"})
        nc.delete(courses_table_name, params={"id": f"eq.{course_id}"})

    # build difs intersect sets
    canvas_urls = set(canvas_df["download_url"])
    db_documents = nc.select(
        documents_table_name,
        params={
            "course_id": f"in.({','.join(str(v) for v in map_code_id_db.values())})"
        },
    )
    db_urls = set(doc["file_url"] for doc in db_documents)
    map_url_id_db = {doc["file_url"]: doc["id"] for doc in db_documents}

    to_insert = canvas_urls - db_urls
    to_delete = db_urls - canvas_urls

    # Insert
    to_insert_data = []
    for url in to_insert:
        row = canvas_df.loc[canvas_df["download_url"] == url].iloc[0]
        course_id = map_code_id_db.get(row["course"])
        if not course_id:
            print(f"[WARN] No course_id for course {row['course']}, skipping")
            continue

        data = {
            "course_id": course_id,
            "filename": row["file_name"],
            "file_type": row["file_extention"],
            "file_url": row["download_url"],
        }
        to_insert_data.append(data)

    nc.insert(documents_table_name, data=to_insert_data)

    # Delete
    for url in to_delete:
        doc_id = map_url_id_db[url]
        nc.delete(documents_table_name, params={"id": f"eq.{doc_id}"})



def main():

    begining_time = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int)
    args = parser.parse_args()

    user_id = args.user_id

    dotenv.load_dotenv()

    CANVAS_API = os.getenv("CANVAS_API_TOKEN")
    CANVAS_URL = os.getenv("CANVAS_URL")

    cc = CanvasClient(CANVAS_API, CANVAS_URL)
    nc = NeonClient()

    sync_courses(cc, nc, user_id)
    sync_documents(cc, nc, user_id)

    end_time = time.time()

    print(f"SYNC RDB TO USER {user_id} DID TAKE {end_time - begining_time}")





if __name__ == "__main__":

    main()

    

