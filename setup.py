import os
import platform
import shutil
import io
import tarfile
import urllib.request
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

    print(
        "    \n"
        "    setup.py:\n"
        "    =========================================\n"
        "    Downloading latest commit of Nova Physics\n"
        "    \n"
        "    https://github.com/kadir014/nova-physics\n"
        "    =========================================\n"
        "    \n"
    )

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

    print(
        "    \n"
        "    setup.py:\n"
        "    =========================================\n"
        "    Downloaded and extracted successfully.\n"
        "    =========================================\n"
        "    \n"
    )

import json


def download_stable() -> None:
    """ Download the latest stable release of Nova Physics. """

    print(
        "    \n"
        "    setup.py:\n"
        "    =========================================\n"
        "    Downloading latest stable release of Nova Physics\n"
        "    \n"
        "    https://github.com/kadir014/nova-physics\n"
        "    =========================================\n"
        "    \n"
    )

    if os.path.exists(BUILD_PATH / "nova-physics"):
        shutil.rmtree(BUILD_PATH / "nova-physics")

    if os.path.exists(BUILD_PATH / "nova-physics-main"):
        shutil.rmtree(BUILD_PATH / "nova-physics-main")

    # Get the latest stable release information via GH API
    response = urllib.request.urlopen(
        "https://api.github.com/repos/kadir014/nova-physics/releases/latest"
    )

    release = json.loads(response.read())
    url = release["tarball_url"]

    response = urllib.request.urlopen(url)
    data = response.read()

    with tarfile.open(mode="r:gz", fileobj=io.BytesIO(data)) as tar:
        tar.extractall(BUILD_PATH)

    # GitHub names the extracted directory after the tag/commit
    extracted_path = next(
        path for path in BUILD_PATH.iterdir()
        if path.is_dir() and
        (path.name.startswith("nova-physics-") or path.name.startswith("kadir014-nova-physics-"))
    )

    os.rename(extracted_path, BUILD_PATH / "nova-physics")

    print(
        "    \n"
        "    setup.py:\n"
        "    =========================================\n"
        "    Downloaded and extracted successfully.\n"
        "    =========================================\n"
        "    \n"
    )
    

# TODO: Downloads multiple times for one install...

BUILD_PATH.mkdir(parents=True, exist_ok=True)
build_type = os.environ.get("NOVA_BUILD", "stable").lower()

if build_type == "nightly":
    download_nightly()
elif build_type == "stable":
    download_stable()
else:
    raise ValueError(
        f"Invalid NOVA_BUILD value: {build_type!r}. "
        "Expected 'stable' or 'nightly'."
    )

setup(
    packages=["nova"],
    cffi_modules=["nova/_cffi_gen.py:ffibuilder"],
)