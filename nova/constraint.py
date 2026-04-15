"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import TYPE_CHECKING

from nova.common import lib, ffi
from nova.vector import Vector2

if TYPE_CHECKING:
    from nova.space import Space
    from nova.body import RigidBody


class Constraint:
    def __init__(self, ccons) -> None:
        self._cons = ccons
        self._refd = False

        # This is only existent when constraint is managed by the space
        # it is to access Python representations by pointers
        self._space: "Space | None" = None

    @property
    def body_a(self) -> "RigidBody | None":
        if self._space is None:
            return None
        
        cbody = self._cons.a
        return self._space._get_body_by_pointer(cbody)
    
    @property
    def body_b(self) -> "RigidBody | None":
        if self._space is None:
            return None
        
        cbody = self._cons.b
        return self._space._get_body_by_pointer(cbody)

    def __del__(self) -> None:
        if self._refd: return
        lib.nvConstraint_free(self._cons)


class DistanceConstraint(Constraint):
    def __init__(
            self,
            body_a: "RigidBody | None",
            body_b: "RigidBody | None",
            length: float,
            anchor_a: Vector2 = Vector2(0.0, 0.0),
            anchor_b: Vector2 = Vector2(0.0, 0.0),
            spring: bool = False,
            hertz: float = 3.0,
            damping: float = 0.3
        ) -> None:
        init = lib.nvDistanceConstraintInitializer_default
        init.a = body_a._rigidbody if body_a is not None else ffi.NULL
        init.b = body_b._rigidbody if body_b is not None else ffi.NULL
        init.length = length
        init.anchor_a = anchor_a.to_tuple()
        init.anchor_b = anchor_b.to_tuple()
        init.spring = spring
        init.hertz = hertz
        init.damping = damping
        ccons = lib.nvDistanceConstraint_new(init)

        super().__init__(ccons)

    @property
    def length(self) -> float:
        return lib.nvDistanceConstraint_get_length(self._cons)
    
    @length.setter
    def length(self, length: float) -> None:
        lib.nvDistanceConstraint_set_length(self._cons, length)

    @property
    def anchor_a(self) -> Vector2:
        anchor = lib.nvDistanceConstraint_get_anchor_a(self._cons)
        return Vector2(anchor.x, anchor.y)
    
    @anchor_a.setter
    def anchor_a(self, anchor_a: Vector2) -> None:
        lib.nvDistanceConstraint_set_anchor_a(self._cons, anchor_a.to_tuple())

    @property
    def anchor_b(self) -> Vector2:
        anchor = lib.nvDistanceConstraint_get_anchor_b(self._cons)
        return Vector2(anchor.x, anchor.y)
    
    @anchor_b.setter
    def anchor_b(self, anchor_b: Vector2) -> None:
        lib.nvDistanceConstraint_set_anchor_b(self._cons, anchor_b.to_tuple())

    @property
    def max_force(self) -> float:
        return lib.nvDistanceConstraint_get_max_force(self._cons)
    
    @max_force.setter
    def max_force(self, max_force: float) -> None:
        lib.nvDistanceConstraint_set_max_force(self._cons, max_force)

    @property
    def is_spring(self) -> bool:
        return lib.nvDistanceConstraint_get_spring(self._cons)
    
    @is_spring.setter
    def is_spring(self, is_spring: bool) -> None:
        lib.nvDistanceConstraint_set_spring(self._cons, is_spring)

    @property
    def hertz(self) -> float:
        return lib.nvDistanceConstraint_get_hertz(self._cons)
    
    @hertz.setter
    def hertz(self, hertz: float) -> None:
        lib.nvDistanceConstraint_set_hertz(self._cons, hertz)

    @property
    def damping(self) -> float:
        return lib.nvDistanceConstraint_get_damping(self._cons)
    
    @damping.setter
    def damping(self, damping: float) -> None:
        lib.nvDistanceConstraint_set_damping(self._cons, damping)


class HingeConstraint(Constraint):
    def __init__(
            self,
            body_a: "RigidBody | None",
            body_b: "RigidBody | None",
            anchor: Vector2,
            enable_limits: bool = False
        ) -> None:

        init = lib.nvHingeConstraintInitializer_default
        init.a = body_a._rigidbody if body_a is not None else ffi.NULL
        init.b = body_b._rigidbody if body_b is not None else ffi.NULL
        init.anchor = anchor.to_tuple()
        init.enable_limits = enable_limits
        ccons = lib.nvHingeConstraint_new(init)

        super().__init__(ccons)

    @property
    def anchor(self) -> Vector2:
        anchor = lib.nvHingeConstraint_get_anchor(self._cons)
        return Vector2(anchor.x, anchor.y)
    
    @anchor.setter
    def anchor(self, anchor: Vector2) -> None:
        lib.nvHingeConstraint_set_anchor(self._cons, anchor.to_tuple())

    @property
    def enable_limits(self) -> bool:
        return lib.nvHingeConstraint_get_limits(self._cons)
    
    @enable_limits.setter
    def enable_limits(self, enable_limits: bool) -> None:
        lib.nvHingeConstraint_set_limits(self._cons, enable_limits)

    @property
    def upper_limit(self) -> float:
        return lib.nvHingeConstraint_get_upper_limit(self._cons)
    
    @upper_limit.setter
    def upper_limit(self, upper_limit: float) -> None:
        lib.nvHingeConstraint_set_upper_limit(self._cons, upper_limit)

    @property
    def lower_limit(self) -> float:
        return lib.nvHingeConstraint_get_lower_limit(self._cons)
    
    @lower_limit.setter
    def lower_limit(self, lower_limit: float) -> None:
        lib.nvHingeConstraint_set_lower_limit(self._cons, lower_limit)

    @property
    def max_force(self) -> float:
        return lib.nvHingeConstraint_get_max_force(self._cons)
    
    @max_force.setter
    def max_force(self, max_force: float) -> None:
        lib.nvHingeConstraint_set_max_force(self._cons, max_force)