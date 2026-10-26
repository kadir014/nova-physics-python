"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

import platform
import re
from pathlib import Path

from cffi import FFI


RELEASE_BUILD = True

BASE_PATH = Path(__file__).resolve().parents[1]
NOVA_PATH = BASE_PATH / "build" / "nova-physics"
INCLUDE_PATH = NOVA_PATH / "include"
HEADER_PATH = INCLUDE_PATH / "novaphysics"

MSVC_COMPILER_ARGS = (
    "/arch:AVX2",
    "/D_CRT_SECURE_NO_WARNINGS",
    "/DNV_ENABLE_PROFILER",
)
GCC_COMPILER_ARGS = (
    # TODO: Detect if building with python-wasm-sdk, emcc doesn't accept -march
    "-D_POSIX_C_SOURCE=200809L",
    "-DNV_ENABLE_PROFILER",
)

IGNORED_HEADERS = {"internal.h", "internal_alloc.h"}


def read_header(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    # Preserve string literals while removing comments (including commented code).
    return re.sub(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*',
        lambda match: " " if match[0].startswith(("/*", "//")) else match[0],
        source,
        flags=re.S,
    )


def ordered_headers() -> list[Path]:
    """ Visit includes first so typedefs precede the declarations using them. """

    visited = set()
    ordered = []

    def visit(path):
        if path in visited:
            return
        visited.add(path)
        for include in re.findall(r'^\s*#include\s+"([^"]+)"', read_header(path), re.M):
            dependency = (INCLUDE_PATH / include).resolve()
            if not dependency.is_file():
                dependency = (path.parent / include).resolve()
            if dependency.is_file() and dependency.is_relative_to(HEADER_PATH.resolve()):
                visit(dependency)
        if path.name not in IGNORED_HEADERS:
            ordered.append(path)

    for path in sorted(HEADER_PATH.rglob("*.h")):
        visit(path.resolve())
    if not ordered:
        raise FileNotFoundError(f"No Nova headers found in {HEADER_PATH}")
    return ordered


def header_cdef(path: Path) -> str:
    """ Generate cdef for one header. """

    source = read_header(path)
    if path.name == "types.h":
        # Ignore the alternate precision branch and nv_sin/nv_cos/etc aliases.
        # These math macros are not used by the Python binding. CFFI's float...
        # typedef lets the compiler determine nv_float's actual precision.
        source = re.sub(r"#ifdef NV_USE_DOUBLE_PRECISION\b.*?#else\b", "", source, flags=re.S)
        source = re.sub(r"typedef\s+(float|double)\s+(nv_float)\s*;", r"typedef \1... \2;", source)

    if path.name == "profiler.h":
        # nvPrecisionTimer and its functions are ignored. Windows & posix types
        # complicate CFFI, and the Python binding only uses nvProfiler.
        source = source.split("typedef struct _nvPrecisionTimer", 1)[0]

    # Only simple integer macros are exposed. Function-like macros, strings,
    # float expressions, platform flags and include guards are intentionally
    # ignored.
    # BUT DONT FORGET their definitions remain available to the compiled C source!!
    source = re.sub(r"\\\r?\n", "", source)
    constants = re.findall(
        r"^\s*#define\s+([A-Za-z_]\w*)\s+(0[xX][0-9a-fA-F]+|\d+)[uUlL]*\s*$",
        source, re.M,
    )
    source = re.sub(r"^\s*#[^\n]*", "", source, flags=re.M)
    # Initializers do not belong to cdef.
    source = re.sub(r"(\bstatic\s+const\b[^=;]+)\s*=.*?;", r"\1;", source, flags=re.S)

    # Nova's inline definitions always start with 'static inline'
    # unless I forget this and do a change in the future lol
    declarations = []
    signature = []
    in_inline = False
    depth = 0
    for line in source.splitlines():

        if not in_inline and re.match(r"\s*static\s+inline\b", line):
            in_inline = True
            signature = []
            line = re.sub(r"\bstatic\s+inline\s+", "", line, count=1)

        if not in_inline:
            declarations.append(line)
            continue

        masked = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', line)
        if depth == 0:
            if "{" not in masked:
                signature.append(line)
                if ";" in masked:  # inline prototype, without a body
                    declarations.extend(signature)
                    in_inline = False
                continue
            signature.append(line[:masked.index("{")].rstrip() + ";")
            declarations.extend(signature)

        depth += masked.count("{") - masked.count("}")
        if depth == 0:
            in_inline = False

    if in_inline:
        raise ValueError(f"Unfinished static inline function in {path}")

    return "\n".join(f"#define {name} {value}" for name, value in constants) + "\n" + "\n".join(declarations)


def generate_cdef(headers: list[Path] | None = None) -> str:
    """ Generate cdef header. """
    headers = ordered_headers() if headers is None else headers
    return "\n\n".join(header_cdef(path) for path in headers)


headers = ordered_headers()
cdef_source = generate_cdef(headers)
# Includes put the original inline implementations in the generated C module.
# No need to copy the bodies header guards already prevent duplicate definitions
ffi_sources = "\n".join(
    f'#include "{path.relative_to(INCLUDE_PATH).as_posix()}"' for path in headers
)


print(
    "    \n"
    "    nova/_cffi_gen.py:\n"
    "    =========================================\n"
    "    Parsing & building the cdef header.\n"
    "    =========================================\n"
    "    \n"
)
ffibuilder = FFI()
ffibuilder.cdef(cdef_source)
ffibuilder.set_source(
    "_nova",
    ffi_sources,
    sources=[str(path) for path in sorted((NOVA_PATH / "src").rglob("*.c"))],
    include_dirs=[str(INCLUDE_PATH)],
    extra_compile_args=list(MSVC_COMPILER_ARGS if platform.system() == "Windows" else GCC_COMPILER_ARGS),
    libraries=[] if platform.system() == "Windows" else ["m"],
)

if __name__ == "__main__":
    print(
        "    \n"
        "    nova/_cffi_gen.py:\n"
        "    =========================================\n"
        "    Building the CFFI module.\n"
        "    =========================================\n"
        "    \n"
    )

    (BASE_PATH / "novaphysics_cdef.h").write_text(cdef_source, encoding="utf-8")
    ffibuilder.compile(verbose=False, debug=not RELEASE_BUILD)
