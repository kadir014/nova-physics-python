"""
    This file is a part of the Python binding of the
    Nova Physics Engine project and distributed under the MIT license.

    Copyright © Kadir Aksoy
    https://github.com/kadir014/nova-physics-python


    Nova Physics Engine Python Binding Builder
    ------------------------------------------
    This Python script is used to build Python binding
    of the Nova Physics Engine.

    Download the latest release and build the module:
    $ python setup.py build

    Download the latest commit and build the module:
    $ python setup.py build --nightly
"""

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


DOWNLOAD_NIGHTLY = False
if "--nightly" in sys.argv:
    DOWNLOAD_NIGHTLY = True
    sys.argv.remove("--nightly")


BUILD_WEB = False
if "--web" in sys.argv:
    BUILD_WEB = True
    sys.argv.remove("--web")


BASE_PATH = Path(os.getcwd())
BUILD_PATH = BASE_PATH / "build"
NOVA_PATH = BUILD_PATH / "nova-physics"


def download_latest():
    """ Download the latest Nova Physics release. """

    print("Getting latest release...")

    response = urllib.request.urlopen(
        f"https://api.github.com/repos/kadir014/nova-physics/releases/latest"
    )

    release_data = json.loads(response.read())
    version = release_data["name"]
    release_url = release_data["tarball_url"]

    print(f"Gathered latest version: {version}.")
    print("Downloading latest release...")

    response = urllib.request.urlopen(release_url)

    data = response.read()

    with tarfile.open(mode="r:gz", fileobj=io.BytesIO(data)) as tar:
        base_dir = tar.getnames()[0]
        tar.extractall(BUILD_PATH)

    os.replace(BUILD_PATH / base_dir, NOVA_PATH)

    shutil.rmtree(BUILD_PATH / base_dir, True)

    print("Downloaded and extracted latest release.")


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


def download_extract_library():
    # TODO: Download latest & Remove other download functions

    print("Downloading 0.7.0 libraries...")

    URL = "https://github.com/kadir014/nova-physics/releases/download/0.7.0/nova-physics-0.7.0-devel.tar.gz"

    response = urllib.request.urlopen(URL)

    data = response.read()

    with tarfile.open(mode="r:gz", fileobj=io.BytesIO(data)) as tar:
        tar.extractall(BUILD_PATH)

    print("Downloaded and extracted 0.7.0 libraries.")


def get_version() -> str:
    """ Get Nova Physics version number. """

    with open(NOVA_PATH / "include" / "novaphysics" / "novaphysics.h", "r") as header_file:
        content = header_file.readlines()
        major, minor, patch = 0, 0, 0

        for line in content:
            if line.startswith("#define NV_VERSION_MAJOR"):
                major = int(line[24:].strip())

            elif line.startswith("#define NV_VERSION_MINOR"):
                minor = int(line[24:].strip())

            elif line.startswith("#define NV_VERSION_PATCH"):
                patch = int(line[24:].strip())
        
    return f"{major}.{minor}.{patch}"


def get_sources() -> list[str]:
    """ Get source file paths. """
    source_files = []

    for *_, files in os.walk(BASE_PATH / "src"):
        for name in files:
            if name.endswith(".c"):
                source_files.append(str(BASE_PATH / "src" / name))

    for *_, files in os.walk(NOVA_PATH / "src"):
        for name in files:
            if name.endswith(".c"):
                source_files.append(str(NOVA_PATH / "src" / name))

    return source_files


if __name__ == "__main__":
    start = time()

    # Remove build directory
    if os.path.exists(BUILD_PATH):
        shutil.rmtree(BUILD_PATH)


    # if DOWNLOAD_NIGHTLY:
    #     download_nightly()
    # else:
    #     download_latest()
        
    if BUILD_WEB:
        download_latest()

        print("Building for web.")

        extension = Extension(
            name = "nova",
            sources = get_sources(),
            include_dirs = [str(NOVA_PATH / "include"), str(BASE_PATH / "src")],
            extra_compile_args=[
                #"-DNV_USE_SIMD",
                #"-DNV_USE_FLOAT",
                "-O3",
                #"-g0",
                "-Wall"
            ]
        )

    else:
        download_extract_library()

        extension = Extension(
            name = "nova",
            sources = [str(BASE_PATH / "src" / "py_nova.c")],
            include_dirs = [str(BUILD_PATH / "include")],
            library_dirs = [str(BUILD_PATH / "lib" / "x86_64")],
            libraries=["nova"],
            #extra_link_args = ["nova.lib",]
        )

    setup(
        name = "nova",
        version = "0.0.0",
        description = "Nova Physics Engine",
        ext_modules = [extension]
    )


    # Python 3.10 -> lib.win-amd64-3.10        / nova.cp310-win_amd64.pyd
    # Python 3.11 -> lib.win-amd64-cpython-311 / nova.cp311-win_amd64.pyd
    generated = BASE_PATH / "build" / "lib.win-amd64-cpython-310" / "nova.cp310-win_amd64.pyd"

    if os.path.exists(generated):
        print("Moving the compiled module as nova.pyd to working directory.")

        # Copy extension build to working directory as "nova.pyd"
        if os.path.exists(BASE_PATH / "nova.pyd"):
            os.remove(BASE_PATH / "nova.pyd")

        shutil.copyfile(generated, BASE_PATH / "nova.pyd")

        print("Moved succesfully.")
        print()

    print(f"Succesfully built Nova in {round(time() - start, 2)}s.")