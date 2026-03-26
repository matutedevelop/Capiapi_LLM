"""
This python file is ment to provide a python wrapper on the `canvas-downloader` binary and parse its results
in a pythonic and convenient way

"""

import pandas as pd
import subprocess
import os


# Later refactor to OOP pattern
class CanvasDownloader:
    pass


def config_file_maker(canvas_url: str, canvas_token_api: str) -> None:
    """The binary requires a `canvas-downloader.toml` to load
    user's secrets, this function is responsable for creating that file"""

    # TODO: error handling

    file_content = f"""
    canvas_url= "{canvas_url}"
    canvas_token= "{canvas_token_api}"
    """
    with open("canvas-downloader.toml", "x") as f:
        f.write(file_content)


if __name__ == "__main__":
    config_file_maker("hello", "world")
