"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""


__version_major__ = 0
__version_minor__ = 2
__version_patch__ = 3
__version__ = f"{__version_major__}.{__version_minor__}.{__version_patch__}"

from nova.common import get_version_buffer
__nova_version__ = get_version_buffer()
del get_version_buffer


from nova.body import RigidBody
from nova.shape import Shape, Circle, Polygon, ShapeFactory
from nova.constraint import Constraint, DistanceConstraint, HingeConstraint
from nova.space import Space
from nova.models import (
    BroadPhaseAlgorithm,
    ShapeType,
    RigidBodyType,
    AABB,
    VisitorAuxiliary,
    Material
)
from nova.vector import Vector2


__all__ = (
    "__version_major__",
    "__version_minor__",
    "__version_patch__",
    "__version__",
    "__nova_version__",
    "RigidBody",
    "Shape",
    "Circle",
    "Polygon",
    "ShapeFactory",
    "Constraint",
    "DistanceConstraint",
    "HingeConstraint",
    "Space",
    "BroadPhaseAlgorithm",
    "ShapeType",
    "RigidBodyType",
    "AABB",
    "VisitorAuxiliary",
    "Material",
    "Vector2"
)