"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import TYPE_CHECKING

from math import pi

from nova.common import lib, ffi, get_error_buffer
from nova.typing import Coordinate, ConstraintTarget, enforce
from nova.error import NovaError
from nova.vector import Vector2
from nova.body import RigidBody # For type enforcer

if TYPE_CHECKING:
    from nova.space import Space


class Constraint:
    def __init__(self, ccons) -> None:
        self._cons = ccons
        self._refd = False

        # This is only existent when constraint is managed by the space
        # it is to access Python representations by pointers
        self._space: "Space | None" = None

    def __del__(self) -> None:
        # No memory in C has been allocated yet
        if not hasattr(self, "_refd"): return
        if self._refd: return

        lib.nvConstraint_free(self._cons)

    @property
    def body_a(self) -> ConstraintTarget:
        if self._space is None:
            return None
        
        cbody = self._cons.a
        return self._space._get_body_by_pointer(cbody)
    
    @property
    def body_b(self) -> ConstraintTarget:
        if self._space is None:
            return None
        
        cbody = self._cons.b
        return self._space._get_body_by_pointer(cbody)

    @property
    def ignore_collision(self) -> bool:
        return lib.nvConstraint_get_ignore_collision(self._cons)

    @ignore_collision.setter
    def ignore_collision(self, ignore_collision: bool) -> None:
        if lib.nvConstraint_set_ignore_collision(self._cons, ignore_collision):
            raise NovaError(get_error_buffer())


class DistanceConstraint(Constraint):
    def __init__(
            self,
            body_a: ConstraintTarget,
            body_b: ConstraintTarget,
            length: float,
            anchor_a: Coordinate = Vector2(0.0, 0.0),
            anchor_b: Coordinate = Vector2(0.0, 0.0),
            soft: bool = False,
            hertz: float = 3.0,
            damping: float = 0.3
        ) -> None:
        enforce("body_a", body_a, ConstraintTarget)
        enforce("body_b", body_b, ConstraintTarget)
        enforce("length", length, float)
        enforce("anchor_a", anchor_a, Coordinate)
        enforce("anchor_b", anchor_b, Coordinate)
        enforce("soft", soft, bool)
        enforce("hertz", hertz, float)
        enforce("damping", damping, float)

        anchor_a = Vector2(anchor_a)
        anchor_b = Vector2(anchor_b)

        init = lib.nvDistanceConstraintInitializer_default
        init.a = body_a._rigidbody if body_a is not None else ffi.NULL
        init.b = body_b._rigidbody if body_b is not None else ffi.NULL
        init.length = length
        init.anchor_a = anchor_a.to_tuple()
        init.anchor_b = anchor_b.to_tuple()
        init.soft = soft
        init.hertz = hertz
        init.damping = damping

        ccons = lib.nvDistanceConstraint_new(init)

        super().__init__(ccons)

        # Error after parent __init__ so it can initialize deconstructor.
        if ccons == ffi.NULL:
            raise NovaError(get_error_buffer())

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
    def soft(self) -> bool:
        return lib.nvDistanceConstraint_get_soft(self._cons)
    
    @soft.setter
    def soft(self, soft: bool) -> None:
        lib.nvDistanceConstraint_set_soft(self._cons, soft)

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
            body_a: ConstraintTarget,
            body_b: ConstraintTarget,
            anchor: Coordinate,
            enable_limits: bool = False,
            upper_limit: float = pi * 0.5,
            lower_limit: float = pi * -0.5
        ) -> None:
        enforce("body_a", body_a, ConstraintTarget)
        enforce("body_b", body_b, ConstraintTarget)
        enforce("anchor", anchor, Coordinate)
        enforce("enable_limits", enable_limits, bool)
        enforce("upper_limit", upper_limit, float)
        enforce("lower_limit", lower_limit, float)

        anchor = Vector2(anchor)

        init = lib.nvHingeConstraintInitializer_default
        init.a = body_a._rigidbody if body_a is not None else ffi.NULL
        init.b = body_b._rigidbody if body_b is not None else ffi.NULL
        init.anchor = anchor.to_tuple()
        init.enable_limits = enable_limits
        init.upper_limit = upper_limit
        init.lower_limit = lower_limit
        ccons = lib.nvHingeConstraint_new(init)

        super().__init__(ccons)

        if ccons == ffi.NULL:
            raise NovaError(get_error_buffer())

    @property
    def anchor(self) -> Vector2:
        anchor = lib.nvHingeConstraint_get_anchor(self._cons)
        return Vector2(anchor.x, anchor.y)
    
    @anchor.setter
    def anchor(self, anchor: Vector2) -> None:
        lib.nvHingeConstraint_set_anchor(self._cons, anchor.to_tuple())

    @property
    def xanchor_a(self) -> Vector2:
        """
        Anchor point local to body A, transformed into world space.
        """

        hinge = getattr(self._cons, "def")
        hinge = ffi.cast("nvHingeConstraint *", hinge)

        xanchor = Vector2(hinge.xanchor_a.x, hinge.xanchor_a.y)
        xanchor += self.body_a.position

        return xanchor

    @property
    def xanchor_b(self) -> Vector2:
        """
        Anchor point local to body B, transformed into world space.
        """

        hinge = getattr(self._cons, "def")
        hinge = ffi.cast("nvHingeConstraint *", hinge)

        xanchor = Vector2(hinge.xanchor_b.x, hinge.xanchor_b.y)
        xanchor += self.body_b.position

        return xanchor

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