"""
This python file is ment to provide a python wrapper on the `canvas-downloader` binary and parse its results
in a pythonic and convenient way

"""

import pandas as pd  # ty: ignore
import subprocess
from pathlib import Path


# Later refactor to OOP pattern
# class CanvasDownloader:
#     pass

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


def get_user_courses() -> pd.DataFrame:
    """This function calls the binary without arguments, which should
    return the courses in which the user is enrolled in in a pd.DataFrame"""

    binary_directory = Path(__file__).parent / "extract-tools"

    # call the binary
    result = subprocess.run(
        [binary_directory / "canvas-downloader"],
        capture_output=True,
        cwd=binary_directory,
    )

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


def get_course_file_names(course_name:str) -> pd.DataFrame:
    pass


# === === === === === === === === === === === === === === === === ===
# db uploaders
# === === === === === === === === === === === === === === === === ===


if __name__ == "__main__":
    config_file_creator(
        "",
        "",
    )
    r = binary_caller()
    print(r.returncode)
    print(r.stdout)
    print(r.args)
