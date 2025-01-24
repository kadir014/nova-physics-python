import os
import platform

from cffi import FFI


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


def generate_cdef() -> None:
    """ Generate cdef header. """
    
    cdef_source = """
typedef float nv_float;
typedef int8_t nv_int8;
typedef int16_t nv_int16;
typedef int32_t nv_int32;
typedef int64_t nv_int64;
typedef uint8_t nv_uint8;
typedef uint16_t nv_uint16;
typedef uint32_t nv_uint32;
typedef uint64_t nv_uint64;
typedef int nv_bool;

#define NV_POLYGON_MAX_VERTICES 16
#define NV_SPLINE_CONSTRAINT_MAX_CONTROL_POINTS 64
#define NV_SPLINE_CONSTRAINT_SAMPLES 500

typedef struct {
    nv_float x;
    nv_float y;
} nvVector2;

typedef struct {
    nvVector2 position;
    nv_float angle;
} nvTransform;

typedef struct {
    double step;
    double broadphase;
    double broadphase_finalize;
    double bvh_free;
    double bvh_build;
    double bvh_traverse;
    double narrowphase;
    double integrate_accelerations;
    double presolve;
    double warmstart;
    double solve_velocities;
    double solve_positions;
    double integrate_velocities;
} nvProfiler;

char *nv_get_error();
"""

    includes = (
        "core/array.h",
        "core/hashmap.h",
        "core/pool.h",
        "aabb.h",
        "material.h",
        "shape.h",
        "body.h",
        "contact.h",
        "collision.h",
        "constraints/constraint.h",
        "constraints/contact_constraint.h",
        "constraints/distance_constraint.h",
        "constraints/hinge_constraint.h",
        "constraints/spline_constraint.h",
        "broadphase.h",
        "space_settings.h",
        "space.h",
    )

    for include in includes:
        bracket = 0
        staticinline = False
        with open(f"build/nova-physics/include/novaphysics/{include}", "r") as f:
            for line in f.readlines()[:-1]:

                if line.startswith("static inline"):
                    if "{" in line: bracket += 1
                    staticinline = True
                    continue

                if staticinline and "{" in line:
                    bracket += 1

                if staticinline and "}" in line:
                    bracket -= 1

                    if bracket == 0:
                        staticinline = False
                        continue

                if staticinline:
                    continue

                if not (
                    line.startswith("#ifndef NOVAPHYSICS") or
                    line.startswith("#define NOVAPHYSICS") or
                    line.startswith("#include") or
                    line.startswith("#define")
                ):
                    cdef_source += line

    with open("novaphysics_cdef.h", "w") as f:
        f.write(cdef_source)


generate_cdef()

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