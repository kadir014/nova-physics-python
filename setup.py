"""

    This file is a part of the Python binding of the
    Nova Physics Engine project and distributed under the MIT license.

    Copyright © Kadir Aksoy
    https://github.com/kadir014/nova-physics-python


    Nova Physics Engine Python Binding Builder
    ------------------------------------------
    This Python script is used to build Python binding
    of the Nova Physics Engine.

"""

import os
import shutil
import io
import tarfile
import urllib.request
from pathlib import Path
from setuptools import setup, Extension


# Latest Nova Physics release version, don't forget to update this
LATEST_NOVA = "0.4.0"


BASE_PATH = Path(os.getcwd())
BUILD_PATH = BASE_PATH / "build"
NOVA_PATH = BUILD_PATH / "nova-physics"
INCLUDE_PATH = NOVA_PATH / "include"


def download_latest():
    """ Download the latest Nova Physics release. """
    response = urllib.request.urlopen(
        f"https://github.com/kadir014/nova-physics/archive/refs/heads/main.tar.gz"
    )

    data = response.read()

    # Extract release archive
    with tarfile.open(mode="r:gz", fileobj=io.BytesIO(data)) as tar:
        tar.extractall(NOVA_PATH)


def get_version() -> str:
    """ Get Nova Physics version number. """

    #with open(INCLUDE_PATH / "novaphysics" / "novaphysics.h", "r") as header_file:
    with open(BASE_PATH.parent / "nova-physics" / "include" / "novaphysics" / "novaphysics.h", "r") as header_file:
        content = header_file.readlines()
        MAJOR, MINOR, PATCH = 0, 0, 0

        for line in content:
            if line.startswith("#define NV_VERSION_MAJOR"):
                MAJOR = int(line[24:].strip())

            elif line.startswith("#define NV_VERSION_MINOR"):
                MINOR = int(line[24:].strip())

            elif line.startswith("#define NV_VERSION_PATCH"):
                PATCH = int(line[24:].strip())
        
    return f"{MAJOR}.{MINOR}.{PATCH}"


def get_sources() -> list[str]:
    """ Get source file paths. """
    source_files = []

    for *_, files in os.walk(BASE_PATH / "src"):
        for name in files:
            if name.endswith(".c"):
                source_files.append(str(BASE_PATH / "src" / name))

    for *_, files in os.walk(BASE_PATH.parent / "nova-physics" / "src"):
        for name in files:
            if name.endswith(".c"):
                source_files.append(str(BASE_PATH.parent / "nova-physics" / "src" / name))

    return source_files

# Remove build directory
if os.path.exists(BUILD_PATH):
    shutil.rmtree(BUILD_PATH)


# Download latest Nova Physics release
download_latest()


extension = Extension(
    name = "nova",
    sources = get_sources(),
    include_dirs = [str(INCLUDE_PATH), str(BASE_PATH.parent / "nova-physics" / "include"), str(BASE_PATH / "src")],
)

setup(
    name = "nova",
    version = get_version(),
    description = "Nova Physics Engine",
    ext_modules = [extension]
)


# Python 3.10 -> lib.win-amd64-3.10        / nova.cp310-win_amd64.pyd
# Python 3.11 -> lib.win-amd64-cpython-311 / nova.cp311-win_amd64.pyd

# Copy extension build to working directory as "nova.pyd"
#shutil.copyfile(BASE_PATH / "build" / "lib.win-amd64-cpython-310" / "nova.cp310-win_amd64.pyd", BASE_PATH / "nova.pyd")
#shutil.copyfile(BASE_PATH / "build" / "lib.win-amd64-cpython-311" / "nova.cp311-win_amd64.pyd", BASE_PATH / "nova.pyd")