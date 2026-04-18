"""
This python file is ment to provide a python wrapper on the `canvas-downloader` binary and parse its results
in a pythonic and convenient way

"""

import pandas as pd  # ty: ignore
import subprocess
from pathlib import Path


class CanvasDownloader:

    def __init__(self, canvas_api_token: str, canvas_url: str) -> None:
        self.canvas_api_token = canvas_api_token
        self.canvas_url = canvas_url

    def config_file_creator(self) -> None:
        """The binary requires a `canvas-downloader.toml` to load
        user's secrets, this function is responsable for creating that file
        in the directory /ETL/EXTRACT/extract-tools/"""

        # TODO: error handling

        file_directory = (
            Path(__file__).parent / "extract-tools" / "canvas-downloader.toml"
        )

        file_content = f"""
        canvas_url= "{self.canvas_url}"
        canvas_token= "{self.canvas_api_token}"
        """

        # create the file
        with open(file_directory, "w") as f:
            f.write(file_content)

    def binary_caller(
        self,
        subcommand: str = None,
        flags: list[str] = [],
    ) -> subprocess.CompletedProcess:
        """This function is responsable for making use of the canvas-downloader binary
        it calls config_file_creator and handles error code, THIS FUNCTION MIGHT FAIL"""

        config_file_creator(self.canvas_api_token, self.canvas_url)

        binary_directory = Path(__file__).parent / "extract-tools"

        # call without subcommand argument
        if subcommand is None:
            result = subprocess.run(
                [binary_directory / "canvas-downloader", *flags],
                capture_output=True,
                cwd=binary_directory,
            )
        else:
            result = subprocess.run(
                [binary_directory / "canvas-downloader", subcommand, *flags],
                capture_output=True,
                cwd=binary_directory,
            )

        return result

    def get_user_courses(self) -> pd.DataFrame:
        """This function calls the binary without arguments, which should
        return the courses in which the user is enrolled in in a pd.DataFrame"""

        result = self.binary_caller()

        # parse the result
        # TODO: error handling

        output = str(result.stdout).lower()
        output = output.split(r"\n")

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
            class_code_column.append(row_values[class_code_idx])
            class_name_column.append(row_values[class_name_idx])

        df = pd.DataFrame(
            {"class_code": class_code_column, "class_name": class_name_column}
        )

        return df

    def get_course_file_name(self, course_codes: list[str]):
        """This function takes a list of valid course_codes runs the binary over this courses to get
        the file names, is important to assure that in all courses passed as argument, the student whose
        is the owner of the api token of this instance, is enrolled in this courses, otherwise the binary
        might fail   THIS_FUNCTION_MIGHT_FAIL
        """
        file_name_df_list = []

        for course_code in course_codes:
            flags = ["-c", course_code, "--dry-run", "--no-raw"]
            result = self.binary_caller(flags=flags)

            # parse the result

            output = str(result.stdout).lower()
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

            for line in output[content_slice]:
                row = line.split("->")
                download_url_column.append(row[0])
                file_name_column.append(row[1][:-9])

            df = pd.DataFrame(
                {
                    "download_url": download_url_column,
                    "file_name": file_name_column,
                    "course": [course_code] * len(output[content_slice]),
                }
            )

            file_name_df_list.append(df)

        file_name_df = pd.concat(file_name_df_list)
        return file_name_df


# === === === === === === === === === === === === === === === === ===
    # download flow
# === === === === === === === === === === === === === === === === ===

    def download_course(self,course_codes:list[str]):
        pass
        temp_stage_direction = 


# === === === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === === === ===
# binary wrappers
# === === === === === === === === === === === === === === === === ===


def config_file_creator(canvas_token_api: str, canvas_url: str) -> None:
    """The binary requires a `canvas-downloader.toml` to load
    user's secrets, this function is responsable for creating that file
    in the directory /ETL/EXTRACT/extract-tools/"""

    # TODO: error handling

    file_directory = Path(__file__).parent / "extract-tools" / "canvas-downloader.toml"

    file_content = f"""
    canvas_url= "{canvas_url}"
    canvas_token= "{canvas_token_api}"
    """

    # create the file
    with open(file_directory, "w") as f:
        f.write(file_content)

    # # delete the file
    # file_directory.unlink()


def binary_caller(
    canvas_token_api: str,
    canvas_url: str,
    subcommand: str = None,
    flags: list[str] = [],
) -> subprocess.CompletedProcess:
    """This function is responsable for making use of the canvas-downloader binary
    it calls config_file_creator and handles error code, THIS FUNCTION MIGHT FAIL"""

    config_file_creator(canvas_token_api, canvas_url)

    binary_directory = Path(__file__).parent / "extract-tools"

    # call without subcommand argument
    if subcommand is None:
        result = subprocess.run(
            [binary_directory / "canvas-downloader", *flags],
            capture_output=True,
            cwd=binary_directory,
        )
    else:
        result = subprocess.run(
            [binary_directory / "canvas-downloader", subcommand, *flags],
            capture_output=True,
            cwd=binary_directory,
        )

    return result


# === === === === === === === === === === === === === === === === ===
# parsers
# === === === === === === === === === === === === === === === === ===


# === === === === === === === === === === === === === === === === ===
# db uploaders
# === === === === === === === === === === === === === === === === ===



