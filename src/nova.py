from typing import Type, TypeVar, Optional

from dataclasses import dataclass
from enum import Enum
from math import sqrt

import _nova

lib = _nova.lib
ffi = _nova.ffi


def get_error_buffer() -> str:
    error_buf = ffi.string(lib.nv_get_error())
    return error_buf.decode("utf-8")


@dataclass
class Vector2:
    x: float
    y: float

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
    
    def __add__(self, vector: "Vector2") -> "Vector2":
        return Vector2(self.x + vector.x, self.y + vector.y)
    
    def __sub__(self, vector: "Vector2") -> "Vector2":
        return Vector2(self.x - vector.x, self.y - vector.y)
    
    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)
    
    def len2(self) -> float:
        return self.x * self.x + self.y * self.y
    
    def len(self) -> float:
        return sqrt(self.len2())
    

@dataclass
class Profiler:
    step: float = 0.0
    bvh_build: float = 0.0


class BroadPhaseAlgorithm(Enum):
    BRUTE_FORCE = 0
    BVH = 1


class Space:
    def __init__(self) -> None:
        self._space = lib.nvSpace_new()
        self._body_ref = [] # To keep bodies from GC'd

        self.profiler = Profiler()

        if self._space == ffi.NULL:
            raise Exception(get_error_buffer())

    def __del__(self) -> None:
        lib.nvSpace_free(self._space)

    def add_rigidbody(self, body: "RigidBody") -> None:
        body._refd = True
        if (lib.nvSpace_add_rigidbody(self._space, body._rigidbody)):
            raise Exception(get_error_buffer())
        self._body_ref.append(body)

    def remove_rigidbody(self, body: "RigidBody") -> None:
        body._refd = False
        if (lib.nvSpace_remove_rigidbody(self._space, body._rigidbody)):
            raise Exception(get_error_buffer())
        self._body_ref.remove(body)

    def add_constraint(self, constraint: Type["ConstraintT"]) -> None:
        lib.nvSpace_add_constraint(self._space, constraint._cons)

    def remove_constraint(self, constraint: Type["ConstraintT"]) -> None:
        lib.nvSpace_remove_constraint(self._space, constraint._cons)

    def step(self, dt: float) -> None:
        lib.nvSpace_step(self._space, dt)

        self.profiler.step = self._space.profiler.step
        self.profiler.bvh_build = self._space.profiler.bvh_build

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
            raise Exception(get_error_buffer())

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
            raise Exception(get_error_buffer())

    def __del__(self) -> None:
        if self._refd: return
        lib.nvRigidBody_free(self._rigidbody)

        # Clear all references to shapes so they can get cleaned up by GC
        for shape in self._shape_ref: shape._refd = False
        self._shape_ref.clear()

    def add_shape(self, shape: Shape) -> None:
        shape._refd = True
        if (lib.nvRigidBody_add_shape(self._rigidbody, shape._shape)):
            Exception(get_error_buffer())
        self._shape_ref.append(shape)

    def remove_shape(self, shape: Shape) -> None:
        shape._refd = False
        if (lib.nvRigidBody_remove_shape(self._rigidbody, shape._shape)):
            raise Exception(get_error_buffer())
        self._shape_ref.remove(shape)

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
        