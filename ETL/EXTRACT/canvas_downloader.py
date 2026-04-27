import pandas as pd  # ty: ignore
import subprocess
from pathlib import Path
import os
import shutil
from unidecode import unidecode


class CanvasClient:
    def __init__(self, canvas_api_token: str, canvas_url: str) -> None:
        self.__canvas_api_token = canvas_api_token
        self.__canvas_url = canvas_url

    def _config_file_creator(self) -> None:
        """The binary requires a `canvas-downloader.toml` to load
        user's secrets, this function is responsable for creating that file
        in the directory /ETL/EXTRACT/extract-tools/"""

        # Directions
        base_path = Path(__file__).parent / "extract-tools"
        file_directory = base_path / "canvas-downloader.toml"
        binary_path = base_path / "canvas-downloader"

        # .toml file content
        file_content = (
            f'canvas_url = "{self.__canvas_url}"\n'
            f'canvas_token = "{self.__canvas_api_token}"'
        )

        # validate that the binary is where is suposed to and is executable
        if not binary_path.exists():
            raise RuntimeError(
                f"FATAL: El binario no existe en {binary_path}. Revisa tu Dockerfile."
            )

        if not os.access(binary_path, os.X_OK):
            raise PermissionError(
                f"FATAL: El binario en {binary_path} no tiene permisos de ejecución."
            )

        try:
            # create the file
            with open(file_directory, "w", encoding="utf-8") as f:
                f.write(file_content)

        except PermissionError as e:
            raise e
        except OSError as e:
            raise e
        except Exception as e:
            raise e

    def _binary_caller(
        self, flags: list[str] | None = [], input=None
    ) -> subprocess.CompletedProcess:
        """This function is responsable for making use of the canvas-downloader binary
        it calls config_file_creator and handles error code, THIS FUNCTION MIGHT FAIL"""



        temp_stage_direction = Path(__file__).parent.parent / "LOAD" / "temp_stage"

        if flags is None:
            flags = ["--no-raw","-d", temp_stage_direction ]

        try:
            self._config_file_creator()
        except Exception as e:
            raise RuntimeError(
                f"There was a problem while creating config.toml file \n {e}"
            )

        binary_directory = Path(__file__).parent / "extract-tools"

        # call without subcommand argument
        if input is None:
            result = subprocess.run(
                [binary_directory / "canvas-downloader", *flags],
                capture_output=True,
                cwd=binary_directory,
            )
        else:
            result = subprocess.run(
                [binary_directory / "canvas-downloader", *flags],
                capture_output=True,
                input=input,
                cwd=binary_directory,
            )
        if result.returncode == -6:
            self._clean_binary_directory()
            raise ProblematicCourseException


        elif result.returncode != 0:
            raise RuntimeError(
                f"Canvas downloader ended with {result.returncode}\n log: {result.stderr}"
            )

        self._clean_binary_directory()

        return result

    def get_user_courses(self) -> pd.DataFrame:
        """This function calls the binary without arguments, which should
        return the courses in which the user is enrolled in in a pd.DataFrame"""

        result = self._binary_caller()

        # parse the result
        # TODO: error handling

        output = str(result.stdout).upper()
        output = output.split(r"\N")

        rows_slice = slice(3, -1)
        class_code_idx = 1
        class_name_idx = 2
        class_code_column = []
        class_name_column = []

        for row in output[rows_slice]:
            # ignore the division lines "----------"
            if row.replace("-", " ").isspace():
                continue

            row_values = row.split("|")
            class_code_column.append(row_values[class_code_idx].strip())
            class_name_column.append(row_values[class_name_idx].strip())

        df = pd.DataFrame(
            {"class_code": class_code_column, "class_name": class_name_column}
        )

        return df

    def get_course_file_name(self, course_codes: list[str]) -> (pd.DataFrame,list[str]):
        """This function takes a list of valid course_codes runs the binary over this courses to get
        the file names, is important to assure that in all courses passed as argument, the student whose
        is the owner of the api token of this instance, is enrolled in this courses, otherwise the binary
        might fail   THIS_FUNCTION_MIGHT_FAIL
        """
        file_name_df_list = []

        problematic_course_codes = []

        for course_code in course_codes:
            flags = ["-c", course_code, "--dry-run", "--no-raw"]


            try:
                result = self._binary_caller(flags=flags)
            except ProblematicCourseException:
                problematic_course_codes.append(course_code)

            # parse the result

            output = str(result.stdout).lower()

            # validate that the course code was valid
            error_pattern = "could not find any course matching course name(s)"
            if error_pattern in output:
                raise RuntimeError(
                    f"el codigo {course_code} no es un codigo de clase valido"
                )

            output = output.split(r"\n")

            begining_content_index = None
            content_slice = None
            end_content_index = -3

            for i, line in enumerate(output):
                if "[dry run] would download" not in line:
                    continue

                begining_content_index = i + 2  # shifting to avoid empty lines
                content_slice = slice(begining_content_index, end_content_index)

                break

            # make table

            download_url_column = []
            file_name_column = []
            file_type_column = []

            for line in output[content_slice]:
                row = line.split("->")

                # want to cut the name of the file at <filename.pdf>

                begining_file_name_idx = row[1].rfind("/") + 1
                end_file_name_idx = row[1].rfind("(")
                begining_file_ext_idx = row[1][:end_file_name_idx].rfind(".")

                file_name_slice = slice(begining_file_name_idx,end_file_name_idx)
                file_ext_slice = slice(begining_file_ext_idx,end_file_name_idx)

                file_name = unidecode(row[1])[file_name_slice]
                file_type = unidecode(row[1])[file_ext_slice]
                download_url = row[0]

                file_name_column.append(file_name)
                file_type_column.append(file_type)
                download_url_column.append(download_url)

            df = pd.DataFrame(
                {
                    "download_url": download_url_column,
                    "file_name": file_name_column,
                    "file_extention": file_type_column,
                    "course": [course_code] * len(output[content_slice]),
                }
            )

            file_name_df_list.append(df)

        file_name_df = pd.concat(file_name_df_list)
        return (file_name_df,problematic_course_codes)

    # === === === === === === === === === === === === === === === === ===
    # download flow
    # === === === === === === === === === === === === === === === === ===

    def download_course(self, course_codes: list[str]) -> None:
        # ==
        # Se debe de garantizar que todos los elementos de course_codes sean codigos validos

        if not all(isinstance(c, str) for c in course_codes) or len(course_codes) == 0:
            raise Exception("course_codes debe de ser una lista no vacia de strings")

        temp_stage_direction = Path(__file__).parent.parent / "LOAD" / "temp_stage"

        for course_code in course_codes:
            # create course_exclusive_directory

            course_folder_direction = temp_stage_direction / course_code
            course_folder_direction.mkdir(parents=True, exist_ok=True)

            flags = ["-c", course_code, "--no-raw", "-d", temp_stage_direction]
            self._binary_caller(flags=flags, input=b"y\n")

    def clean_temp_stage(self) -> None:
        temp_stage_direction = Path(__file__).parent.parent / "LOAD" / "temp_stage"

        if not temp_stage_direction.exists():

            print("the temporary stage direction does not exists")
            temp_stage_direction.mkdir(parents=True)
            print(f"temp stage directory was created at {temp_stage_direction}")

            return

        for x in temp_stage_direction.iterdir():

            if x.is_dir():
                shutil.rmtree(x)
            else:
                x.unlink()

    def _clean_binary_directory(self) -> None:
        binary_directory = Path(__file__).parent / "extract-tools"
        if not binary_directory.exists():
            print("the binary directory does not exist")
            return
        for x in binary_directory.iterdir():
            if x.is_dir():
                shutil.rmtree(x)
                print(f"Removed directory: {x.name}")



class ProblematicCourseException(Exception):
    """This exception is Raised when the course is problematic to query e.g. has not enought content to query, this a thing of the canvas binary and is not completlly desired"""
    pass

# === === === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === === === ===
