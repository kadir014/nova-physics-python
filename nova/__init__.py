from typing import Type, TypeVar, Optional
from collections.abc import Iterator

from dataclasses import dataclass
from enum import Enum
from math import sqrt, cos, sin

import _nova

lib = _nova.lib
ffi = _nova.ffi

__version_major__ = 0
__version_minor__ = 1
__version_patch__ = 1
__version__ = f"{__version_major__}.{__version_minor__}.{__version_patch__}"


def get_error_buffer() -> str:
    error_buf = ffi.string(lib.nv_get_error())
    return error_buf.decode("utf-8")


class NovaError(Exception):
    """ A low-level error occured in the C library. """

class DuplicateError(Exception):
    """ Either a body or constraint is added to space more than once. """


class Vector2:
    __slots__ = ("x", "y")
    
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"<nova.Vector2({round(self.x, 3)}, {round(self.y, 3)})>"

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
    
    def __add__(self, vector: "Vector2") -> "Vector2":
        return Vector2(self.x + vector.x, self.y + vector.y)
    
    def __sub__(self, vector: "Vector2") -> "Vector2":
        return Vector2(self.x - vector.x, self.y - vector.y)
    
    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __eq__(self, vector: "Vector2") -> bool:
        return self.x == vector.x and self.y == vector.y
    
    def __neg__(self) -> "Vector2":
        return Vector2(-self.x, -self.y)
    
    def rotate(self, angle: float) -> "Vector2":
        c = cos(angle)
        s = sin(angle)
        return Vector2(c * self.x - s * self.y, s * self.x + c * self.y)
    
    def perp(self) -> "Vector2":
        return Vector2(-self.y, self.x)
    
    def perpr(self) -> "Vector2":
        return Vector2(self.y, -self.x)
    
    def len2(self) -> float:
        return self.x * self.x + self.y * self.y
    
    def len(self) -> float:
        return sqrt(self.len2())
    
    def dot(self, vector: "Vector2") -> float:
        return self.x * vector.x + self.y * vector.y
    
    def cross(self, vector: "Vector2") -> float:
        return self.x * vector.y - self.y * vector.x
    
    def dist2(self, vector: "Vector2") -> float:
        return (vector.x - self.x) * (vector.x - self.x) + (vector.y - self.y) * (vector.y - self.y)
    
    def dist(self, vector: "Vector2") -> float:
        return sqrt(self.dist2(vector))
    
    def normalize(self) -> "Vector2":
        return self / self.len()
    
    def lerp(self, vector: "Vector2", t: float) -> "Vector2":
        return Vector2((1.0 - t) * self.x + t * vector.x, (1.0 - t) * self.y + t * vector.y)


@dataclass
class AABB:
    """
    Axis-aligned bounding box.
    """

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def collide_aabb(self, aabb: "AABB") -> bool:
        """ Check collision against another AABB. """
    
        return not (self.max_x <= aabb.min_x or aabb.max_x <= self.min_x or
                    self.max_y <= aabb.min_y or aabb.max_y <= self.min_y)

    def collide_point(self, point: Vector2) -> bool:
        """ Check if point is inside AABB. """

        return (self.min_x <= point.x and point.x <= self.max_x and
                self.min_y <= point.y and point.y <= self.max_y)


@dataclass
class Profiler:
    """
    Physics frame profiler. Timings are in seconds.

    Attributes
    ----------
    step
        Time spent in one simulation step.
    broadphase
        Time spent for broadphase.
    broadphase_finalize
        Time spent finalizing broadphase.
    bvh_build
        Time spent constructing the BVH-tree.
    bvh_traverse
        Time spent traversing the BVH-tree.
    bvh_free
        Time spent destroying the BVH-tree.
    narrowphase
        Time spent for narrowphase.
    integrate_accelerations
        Time spend integrating accelerations.
    presolve
        Time spent preparing constraints for solving.
    warmstart
        Time spent warmstarting constraints.
    solve_velocities
        Time spent solving velocity constraints.
    integrate_velocities
        Time spent integrating velocities.
    """
    step: float = 0.0
    broadphase: float = 0.0
    broadphase_finalize: float = 0.0
    bvh_build: float = 0.0
    bvh_traverse: float = 0.0
    bvh_free: float = 0.0
    narrowphase: float = 0.0
    integrate_accelerations: float = 0.0
    presolve: float = 0.0
    warmstart: float = 0.0
    solve_velocities: float = 0.0
    integrate_velocities: float = 0.0


@dataclass
class RayCastResult:
    position: Vector2
    normal: Vector2
    body: "RigidBody"
    shape: "Shape"


class BroadPhaseAlgorithm(Enum):
    BRUTE_FORCE = 0
    BVH = 1


class Space:
    def __init__(self) -> None:
        self._space = lib.nvSpace_new()
        self._body_ref = [] # To keep bodies from GC'd

        self.profiler = Profiler()

        if self._space == ffi.NULL:
            raise NovaError(get_error_buffer())

    def __del__(self) -> None:
        lib.nvSpace_free(self._space)

    def _get_body_by_pointer(self, cbody) -> Optional["RigidBody"]:
        for body in self._body_ref:
            if body._rigidbody == cbody:
                return body
        return None

    def add_rigidbody(self, body: "RigidBody") -> None:
        body._refd = True
        ret = lib.nvSpace_add_rigidbody(self._space, body._rigidbody)
        if ret == 2:
            raise DuplicateError("Can't add same body to same space more than once.")
        elif ret == 1:
            raise NovaError(get_error_buffer())
        self._body_ref.append(body)

    def remove_rigidbody(self, body: "RigidBody") -> None:
        body._refd = False
        if lib.nvSpace_remove_rigidbody(self._space, body._rigidbody):
            raise NovaError(get_error_buffer())
        self._body_ref.remove(body)

    def add_constraint(self, constraint: Type["ConstraintT"]) -> None:
        lib.nvSpace_add_constraint(self._space, constraint._cons)

    def remove_constraint(self, constraint: Type["ConstraintT"]) -> None:
        lib.nvSpace_remove_constraint(self._space, constraint._cons)

    def iter_bodies(self) -> Iterator["RigidBody"]:

        # ? Use _body_ref instead of allocation and calling nvSpace_iter_bodies

        #body = ffi.new("nvRigidBody **")
        #index = ffi.new("size_t *")
        #while lib.nvSpace_iter_bodies(self._space, body, index):
        #    yield self._get_body_by_pointer(body[0])

        for body in self._body_ref:
            yield body

    def step(self, dt: float) -> None:
        lib.nvSpace_step(self._space, dt)

        self.profiler.step = self._space.profiler.step
        self.profiler.broadphase = self._space.profiler.broadphase
        self.profiler.broadphase_finalize = self._space.profiler.broadphase_finalize
        self.profiler.bvh_build = self._space.profiler.bvh_build
        self.profiler.bvh_traverse = self._space.profiler.bvh_traverse
        self.profiler.bvh_free = self._space.profiler.bvh_free
        self.profiler.narrowphase = self._space.profiler.narrowphase
        self.profiler.integrate_accelerations = self._space.profiler.integrate_accelerations
        self.profiler.presolve = self._space.profiler.presolve
        self.profiler.warmstart = self._space.profiler.warmstart
        self.profiler.solve_velocities = self._space.profiler.solve_velocities
        self.profiler.integrate_velocities = self._space.profiler.integrate_velocities

    def cast_ray(self, ray_from: Vector2, ray_to: Vector2) -> list[RayCastResult]:
        from_ = ray_from.to_tuple()
        to_ = ray_to.to_tuple()
        capacity = 512

        results_ = ffi.new(f"nvRayCastResult[{capacity}]")
        num_hits_ = ffi.new("size_t *")

        lib.nvSpace_cast_ray(self._space, from_, to_, results_, num_hits_, capacity)

        num_hits = int(num_hits_[0])
        results = []

        for i in range(num_hits):
            result = results_[i]
            body = self._get_body_by_pointer(result.body)
            shape = body._get_shape_by_pointer(result.shape)

            results.append(RayCastResult(
                Vector2(result.position.x, result.position.y),
                Vector2(result.normal.x, result.normal.y),
                body,
                shape
            ))

        return results

    @property
    def broadphase(self) -> BroadPhaseAlgorithm:
        bph = lib.nvSpace_get_broadphase(self._space)
        return BroadPhaseAlgorithm(bph)
    
    @broadphase.setter
    def broadphase(self, broadphase_algorithm: BroadPhaseAlgorithm) -> None:
        lib.nvSpace_set_broadphase(self._space, broadphase_algorithm.value)


class ShapeType(Enum):
    CIRCLE = 0
    POLYGON = 1

class Shape:
    def __init__(self, cshape) -> None:
        self._shape = cshape
        self._refd = False

        if self._shape == ffi.NULL:
            raise NovaError(get_error_buffer())

    def __del__(self) -> None:
        if self._refd: return
        lib.nvShape_free(self._shape)

    @classmethod
    def circle(cls, radius: float, center: Vector2 = Vector2(0.0, 0.0)):
        shape = lib.nvCircleShape_new(center.to_tuple(), radius)
        return cls(shape)
    
    @classmethod
    def polygon(cls, vertices: list[Vector2], offset: Vector2 = Vector2(0.0, 0.0)):
        n = len(vertices)
        vertices_buf = ffi.new(f"nvVector2[{n}]")
        for i in range(n):
            vertices_buf[i] = (vertices[i].x, vertices[i].y)

        shape = lib.nvPolygonShape_new(vertices_buf, n, offset.to_tuple())
        return cls(shape)

    @classmethod
    def rect(cls, width: float, height: float, offset: Vector2 = Vector2(0.0, 0.0)):
        shape = lib.nvRectShape_new(width, height, offset.to_tuple())
        return cls(shape)
    
    @classmethod
    def box(cls, width: float, height: float, offset: Vector2 = Vector2(0.0, 0.0)):
        shape = lib.nvRectShape_new(width, height, offset.to_tuple())
        return cls(shape)
    
    @classmethod
    def ngon(cls, n: int, radius: float, offset: Vector2 = Vector2(0.0, 0.0)):
        shape = lib.nvNGonShape_new(n, radius, offset.to_tuple())
        return cls(shape)
    
    @property
    def type(self) -> ShapeType:
        return ShapeType(self._shape.type)


@dataclass
class Material:
    density: float = 1.0
    restitution: float = 0.2
    friction: float = 0.5

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.density, self.restitution, self.friction)


class RigidBodyType(Enum):
    STATIC = 0
    DYNAMIC = 1

class RigidBody:
    def __init__(
            self,
            type: RigidBodyType = RigidBodyType.STATIC,
            position: Vector2 = Vector2(0.0, 0.0),
            linear_velocity: Vector2 = Vector2(0.0, 0.0),
            angular_velocity: float = 0.0,
            material: Material = Material()
        ) -> None:
        init = lib.nvRigidBodyInitializer_default
        init.type = type.value
        init.position = position.to_tuple()
        init.linear_velocity = linear_velocity.to_tuple()
        init.angular_velocity = angular_velocity
        init.material = material.to_tuple()
        self._rigidbody = lib.nvRigidBody_new(init)
        self._refd = False

        # To keep GC
        self._shape_ref = []

        if self._rigidbody == ffi.NULL:
            raise NovaError(get_error_buffer())

    def __del__(self) -> None:
        if self._refd: return
        lib.nvRigidBody_free(self._rigidbody)

        # Clear all references to shapes so they can get cleaned up by GC
        for shape in self._shape_ref: shape._refd = False
        self._shape_ref.clear()

    def _get_shape_by_pointer(self, cshape) -> Optional[Shape]:
        for shape in self._shape_ref:
            if shape._shape == cshape:
                return shape
        return None

    def add_shape(self, shape: Shape) -> None:
        shape._refd = True
        if (lib.nvRigidBody_add_shape(self._rigidbody, shape._shape)):
            raise NovaError(get_error_buffer())
        self._shape_ref.append(shape)

    def remove_shape(self, shape: Shape) -> None:
        shape._refd = False
        if (lib.nvRigidBody_remove_shape(self._rigidbody, shape._shape)):
            raise NovaError(get_error_buffer())
        self._shape_ref.remove(shape)

    def iter_shapes(self) -> Iterator[Shape]:
        for shape in self._shape_ref:
            yield shape

    @property
    def aabb(self) -> AABB:
        aabb = lib.nvRigidBody_get_aabb(self._rigidbody)
        return AABB(aabb.min_x, aabb.min_y, aabb.max_x, aabb.max_y)

    @property
    def position(self) -> Vector2:
        pos = lib.nvRigidBody_get_position(self._rigidbody)
        return Vector2(pos.x, pos.y)
    
    @position.setter
    def position(self, position: Vector2) -> None:
        lib.nvRigidBody_set_position(self._rigidbody, position.to_tuple())

    @property
    def angle(self) -> float:
        return lib.nvRigidBody_get_angle(self._rigidbody)
    
    @angle.setter
    def angle(self, angle: Vector2) -> None:
        lib.nvRigidBody_set_angle(self._rigidbody, angle)

    @property
    def linear_velocity(self) -> Vector2:
        vel = lib.nvRigidBody_get_linear_velocity(self._rigidbody)
        return Vector2(vel.x, vel.y)
    
    @linear_velocity.setter
    def linear_velocity(self, linear_velocity: Vector2) -> None:
        lib.nvRigidBody_set_linear_velocity(self._rigidbody, linear_velocity.to_tuple())

    @property
    def angular_velocity(self) -> float:
        return lib.nvRigidBody_get_angular_velocity(self._rigidbody)
    
    @angular_velocity.setter
    def angular_velocity(self, angular_velocity: float) -> None:
        lib.nvRigidBody_set_angular_velocity(self._rigidbody, angular_velocity)

    @property
    def linear_damping_scale(self) -> float:
        return lib.nvRigidBody_get_linear_damping_scale(self._rigidbody)
    
    @linear_damping_scale.setter
    def linear_damping_scale(self, linear_damping_scale: float) -> None:
        lib.nvRigidBody_set_linear_damping_scale(self._rigidbody, linear_damping_scale)

    @property
    def angular_damping_scale(self) -> float:
        return lib.nvRigidBody_get_angular_damping_scale(self._rigidbody)
    
    @angular_damping_scale.setter
    def angular_damping_scale(self, angular_damping_scale: float) -> None:
        lib.nvRigidBody_set_angular_damping_scale(self._rigidbody, angular_damping_scale)

    @property
    def inertia(self) -> float:
        return lib.nvRigidBody_get_inertia(self._rigidbody)
    
    @inertia.setter
    def inertia(self, inertia: float) -> None:
        lib.nvRigidBody_set_inertia(self._rigidbody, inertia)


class Constraint:
    def __init__(self, a: Optional[RigidBody], b: Optional[RigidBody]) -> None:
        self.a = a
        self.b = b
        self._cons = None

    def __del__(self) -> None:
        self.a, self.b = None, None

ConstraintT = TypeVar("ConstraintT", bound=Constraint)

class DistanceConstraint(Constraint):
    def __init__(
            self,
            a: Optional[RigidBody],
            b: Optional[RigidBody],
            length: float,
            anchor_a: Vector2 = Vector2(0.0, 0.0),
            anchor_b: Vector2 = Vector2(0.0, 0.0),
            spring: bool = False,
            hertz: float = 3.0,
            damping: float = 0.3
        ) -> None:
        super().__init__(a, b)

        init = lib.nvDistanceConstraintInitializer_default
        init.a = a._rigidbody if a is not None else ffi.NULL
        init.b = b._rigidbody if b is not None else ffi.NULL
        init.length = length
        init.anchor_a = anchor_a.to_tuple()
        init.anchor_b = anchor_b.to_tuple()
        init.spring = spring
        init.hertz = hertz
        init.damping = damping
        self._cons = lib.nvDistanceConstraint_new(init)


class HingeConstraint(Constraint):
    def __init__(
            self,
            a: RigidBody,
            b: RigidBody,
            anchor: Vector2,
            enable_limits: bool = False
        ) -> None:
        super().__init__(a, b)

        init = lib.nvHingeConstraintInitializer_default
        init.a = a._rigidbody
        init.b = b._rigidbody
        self._cons = lib.nvHingeConstraint_new(init)
        