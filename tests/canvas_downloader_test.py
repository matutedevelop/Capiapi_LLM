import os
import dotenv
from ETL.EXTRACT.canvas_downloader import CanvasClient

dotenv.load_dotenv()

canvas_api_token = os.getenv("CANVAS_API_TOKEN")
canvas_url = os.getenv("CANVAS_URL")


# Initialize manager
canvas_manager = CanvasClient(canvas_api_token, canvas_url)


# Test get user courses
#r = canvas_manager.get_user_courses()
#print(r)


# Test get coourse's file names
course_codes = ["P2026_MAF3071J", "P2026_MAF3653P"]
r = canvas_manager.get_course_file_name(course_codes)
print(r[0]["file_name"])


# Test get coourse's file names with incorrect code
# course_codes = ["P2026_MAF3071J", "clearly not a code"]
# r = canvas_manager.get_course_file_name(course_codes)
# print(r)

# Test download files in desired location
# course_codes = ["P2026_MAF3071J", "P2026_MAF3653P"]
# r = canvas_manager.download_course(course_codes)

# Test clean temp_stage 
#r = canvas_manager.clean_temp_stage()

#r = canvas_manager._binary_caller()

# Test download files without the destination folder
#course_codes = ["P2026_MAF3071J", "P2026_MAF3653P"]
#r = canvas_manager.download_course(course_codes)
