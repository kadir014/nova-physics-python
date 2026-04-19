"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import TYPE_CHECKING
from collections.abc import Iterator

from nova.common import lib, ffi, get_error_buffer
from nova.typing import Coordinate, enforce
from nova.error import NovaError
from nova.models import RigidBodyType, Material, AABB
from nova.vector import Vector2

if TYPE_CHECKING:
    from nova.shape import Shape


class RigidBody:
    def __init__(
            self,
            type: RigidBodyType = RigidBodyType.STATIC,
            position: Coordinate = Vector2(0.0, 0.0),
            angle: float = 0.0,
            linear_velocity: Coordinate = Vector2(0.0, 0.0),
            angular_velocity: float = 0.0,
            material: Material = Material()
        ) -> None:
        type = enforce("type", type, RigidBodyType)
        position = enforce("position", position, Coordinate)
        angle = enforce("angle", angle, float)
        linear_velocity = enforce("linear_velocity", linear_velocity, Coordinate)
        angular_velocity = enforce("angular_velocity", angular_velocity, float)
        material = enforce("material", material, Material)

        position = Vector2(position)
        linear_velocity = Vector2(linear_velocity)

        init = lib.nvRigidBodyInitializer_default
        init.type = type.value
        init.position = position.to_tuple()
        init.angle = angle
        init.linear_velocity = linear_velocity.to_tuple()
        init.angular_velocity = angular_velocity
        init.material = material.to_tuple()
        self._rigidbody = lib.nvRigidBody_new(init)
        self._refd = False

        # To keep GC
        self._shape_ref: list["Shape"] = []

        if self._rigidbody == ffi.NULL:
            raise NovaError(get_error_buffer())

    def __del__(self) -> None:
        if not hasattr(self, "_rigidbody"): return
        if self._refd: return

        lib.nvRigidBody_free(self._rigidbody)

        # Do not clear shape references
        # because nvRigidBody_free already frees all shapes
        # heap corruption -> for shape in self._shape_ref: shape._refd = False
        self._shape_ref.clear()

    def _get_shape_by_pointer(self, cshape) -> "Shape | None":
        for shape in self._shape_ref:
            if shape._shape == cshape:
                return shape
        return None

    def add_shape(self, shape: "Shape") -> None:
        shape._refd = True
        if (lib.nvRigidBody_add_shape(self._rigidbody, shape._shape)):
            raise NovaError(get_error_buffer())
        self._shape_ref.append(shape)

    def remove_shape(self, shape: "Shape") -> None:
        shape._refd = False
        if (lib.nvRigidBody_remove_shape(self._rigidbody, shape._shape)):
            raise NovaError(get_error_buffer())
        self._shape_ref.remove(shape)

    def iter_shapes(self) -> Iterator["Shape"]:
        for shape in self._shape_ref:
            yield shape

    def apply_force(self, force: Coordinate) -> None:
        force = Vector2(force)
        lib.nvRigidBody_apply_force(self._rigidbody, force.to_tuple())

    def apply_torque(self, torque: float) -> None:
        lib.nvRigidBody_apply_torque(self._rigidbody, torque)

    @property
    def type(self) -> RigidBodyType:
        type = lib.nvRigidBody_get_type(self._rigidbody)
        if type == 0:
            return RigidBodyType.STATIC
        else:
            return RigidBodyType.DYNAMIC
    
    @type.setter
    def type(self, type: RigidBodyType) -> None:
        if lib.nvRigidBody_set_type(self._rigidbody, type.value):
            raise NovaError(get_error_buffer())

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

    @property
    def gravity_scale(self) -> float:
        return lib.nvRigidBody_get_gravity_scale(self._rigidbody)

    @gravity_scale.setter
    def gravity_scale(self, gravity_scale: float) -> None:
        lib.nvRigidBody_set_gravity_scale(self._rigidbody, gravity_scale)