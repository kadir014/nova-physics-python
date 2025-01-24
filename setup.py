import sys
import os
import platform
import shutil
import io
import tarfile
import urllib.request
from time import time
from pathlib import Path
from setuptools import setup


if platform.system() == "Darwin":
    # OSX stuff
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context


BASE_PATH = Path(os.getcwd())
BUILD_PATH = BASE_PATH / "build"
NOVA_PATH = BUILD_PATH / "nova-physics"


def download_nightly() -> None:
    """ Download the latest Nova Physics commit. """

    print("Downloading latest commit...")

    if os.path.exists(BUILD_PATH / "nova-physics"):
        shutil.rmtree(BUILD_PATH / "nova-physics")

    if os.path.exists(BUILD_PATH / "nova-physics-main"):
        shutil.rmtree(BUILD_PATH / "nova-physics-main")

    response = urllib.request.urlopen(
        f"https://github.com/kadir014/nova-physics/archive/refs/heads/main.tar.gz"
    )

    data = response.read()

    with tarfile.open(mode="r:gz", fileobj=io.BytesIO(data)) as tar:
        tar.extractall(BUILD_PATH)

    os.rename(BUILD_PATH / "nova-physics-main", BUILD_PATH / "nova-physics")

    print("Downloaded and extracted commit.")
    

download_nightly()

setup(
    packages=["nova"],
    cffi_modules=["nova/_cffi_gen.py:ffibuilder"],
)