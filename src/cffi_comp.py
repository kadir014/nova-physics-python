import os
import platform

from cffi import FFI

from src.cffi_gen import generate


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
    c_args.append("/arch:AVX2")
    c_args.append("/D_CRT_SECURE_NO_WARNINGS")
    c_args.append("/DNV_ENABLE_PROFILER")
else:
    c_args.append("-march=native")
    c_args.append("-D_POSIX_C_SOURCE=200809L")
    c_args.append("-DNV_ENABLE_PROFILER")

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
    ffibuilder.compile(verbose=False, debug=False)