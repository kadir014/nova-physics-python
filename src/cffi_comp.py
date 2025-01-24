import os
import platform

from cffi import FFI

from src.cffi_gen import generate


RELEASE_BUILD = True

MSVC_COMPILER_ARGS = (
    "/arch:AVX2",
    "/D_CRT_SECURE_NO_WARNINGS",
    "/DNV_ENABLE_PROFILER"
)

GCC_COMPILER_ARGS = (
    "-march=native",
    "-D_POSIX_C_SOURCE=200809L",
    "-DNV_ENABLE_PROFILER"
)


generate()

ffibuilder = FFI()

with open("novaphysics_cdef.h", "r") as f:
    ffibuilder.cdef(f.read())

src_path = "build/nova-physics/src"
sources = []
for root, _, files in os.walk(src_path):
    for file in files:
        sources.append(os.path.join(root, file))

c_args = []

if platform.system() == "Windows":
    c_args += MSVC_COMPILER_ARGS
else:
    c_args += GCC_COMPILER_ARGS

ffibuilder.set_source(
    "_nova",
    """
    #include \"novaphysics/internal.h\"
    #include \"novaphysics/novaphysics.h\"
    """,
    sources=sources,
    include_dirs=["build/nova-physics/include/"],
    extra_compile_args=c_args
)


if __name__ == "__main__":
    ffibuilder.compile(verbose=False, debug=not RELEASE_BUILD)