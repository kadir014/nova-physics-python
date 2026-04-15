"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from nova.typing import Coordinate
from nova.vector import Vector2

if TYPE_CHECKING:
    from nova.space import Space
    from nova.body import RigidBody
    from nova.shape import Shape


class BroadPhaseAlgorithm(Enum):
    BRUTE_FORCE = 0
    BVH = 1


class ShapeType(Enum):
    CIRCLE = 0
    POLYGON = 1


class RigidBodyType(Enum):
    STATIC = 0
    DYNAMIC = 1


@dataclass
class AABB:
    """
    Axis-aligned bounding box.

    Attributes
    ----------
    min_x
        Minimum X coordinate of the boundary (left).
    min_y
        Minimum Y coordinate of the boundary (bottom).
    max_x
        Maximum X coordinate of the boundary (right).
    max_y
        Maximum Y coordinate of the boundary (top).
    """

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def collide_aabb(self, aabb: "AABB") -> bool:
        """ Check collision against another AABB. """
    
        return not (self.max_x <= aabb.min_x or aabb.max_x <= self.min_x or
                    self.max_y <= aabb.min_y or aabb.max_y <= self.min_y)

    def collide_point(self, point: Coordinate) -> bool:
        """ Check if point is inside AABB. """

        point = Vector2(*point)
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
    raycasts
        Time spent for ray casts until last simulation step.
    """

    step: float = 0.0
    broadphase: float = 0.0
    broadphase_finalize: float = 0.0
    bvh_build: float = 0.0
    bvh_traverse: float = 0.0
    narrowphase: float = 0.0
    integrate_accelerations: float = 0.0
    presolve: float = 0.0
    warmstart: float = 0.0
    solve_velocities: float = 0.0
    integrate_velocities: float = 0.0
    raycasts: float = 0.0


@dataclass
class RayCastResult:
    """
    Result of a single ray cast query.

    Attributes
    ----------
    position
        Point in world space where ray intersects shape.
    normal
        Normal of the surface ray hit.
    body
        The rigid body that was hit
    shape
        First (and only) shape of the body which is involved in the collision.
    """

    position: Vector2
    normal: Vector2
    body: "RigidBody"
    shape: "Shape"


@dataclass
class VisitorAuxiliary:
    """
    Auxiliary information for visitor callback functions.
    
    Attributes
    ----------
    space
        Current space
    body
        Currently visited rigid body
    shape
        Currently visited shape
    user_arg
        User argument
    """

    space: "Space"
    body: "RigidBody"
    shape: "Shape"
    user_arg: Any | None = None


@dataclass
class Material:
    density: float = 1.0
    restitution: float = 0.2
    friction: float = 0.5

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.density, self.restitution, self.friction)