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


def generate() -> None:
    """ Generate cdef header. """
    global cdef_source

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