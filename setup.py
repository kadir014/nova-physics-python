import sys
import os
import platform
import shutil
import io
import json
import tarfile
import urllib.request
from time import time
from pathlib import Path
from setuptools import setup, Extension


if platform.system() == "Darwin":
    # Fuck OSX
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context


BUILD_WEB = False
if "--web" in sys.argv:
    BUILD_WEB = True
    sys.argv.remove("--web")


BASE_PATH = Path(os.getcwd())
BUILD_PATH = BASE_PATH / "build"
NOVA_PATH = BUILD_PATH / "nova-physics"


def download_nightly():
    """ Download the latest Nova Physics commit. """

    print("Downloading latest commit...")

    response = urllib.request.urlopen(
        f"https://github.com/kadir014/nova-physics/archive/refs/heads/main.tar.gz"
    )

    data = response.read()

    with tarfile.open(mode="r:gz", fileobj=io.BytesIO(data)) as tar:
        tar.extractall(BUILD_PATH)

    os.rename(BUILD_PATH / "nova-physics-main", BUILD_PATH / "nova-physics")

    print("Downloaded and extracted commit.")



if __name__ == "__main__":
    start = time()

    # Remove build directory
    if os.path.exists(BUILD_PATH):
        shutil.rmtree(BUILD_PATH)

    download_nightly()

    setup(
        name = "nova",
        version = "0.0.0",
        description = "Nova Physics Engine",
        setup_requires=["cffi>=1.0.0"],
        cffi_modules=["src/cffi_comp.py:ffibuilder"],
        install_requires=["cffi>=1.0.0"]
    )


    # Python 3.10 -> lib.win-amd64-3.10        / nova.cp310-win_amd64.pyd
    # Python 3.11 -> lib.win-amd64-cpython-311 / nova.cp311-win_amd64.pyd
    # generated = BASE_PATH / "build" / "lib.win-amd64-cpython-310" / "nova.cp310-win_amd64.pyd"

    # if os.path.exists(generated):
    #     print("Moving the compiled module as nova.pyd to working directory.")

    #     # Copy extension build to working directory as "nova.pyd"
    #     if os.path.exists(BASE_PATH / "nova.pyd"):
    #         os.remove(BASE_PATH / "nova.pyd")

    #     shutil.copyfile(generated, BASE_PATH / "nova.pyd")

    #     print("Moved succesfully.")
    #     print()

    # print(f"Succesfully built Nova in {round(time() - start, 2)}s.")