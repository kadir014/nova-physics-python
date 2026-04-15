"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import Callable, TypeVar, Type, TYPE_CHECKING
from collections.abc import Iterable

from nova.vector import Vector2
from nova.constraint import Constraint

if TYPE_CHECKING:
    from nova.models import VisitorAuxiliary


EnforcedT = TypeVar("T")
def enforce(
        name: str,
        value: object,
        expected_type: Type[EnforcedT]
    ) -> EnforcedT:
    """
    Enforce the expected type, raise TypeError if fails.
    
    Parameters
    ----------
    name
        Argument name
    value
        Argument value
    expected_type
        Expected argument type
    """

    if not isinstance(value, expected_type):
        raise TypeError(
            f"Argument '{name}' must be {expected_type.__name__}, "
            f"not {type(value).__name__}"
        )

    return value


Coordinate = Vector2 | tuple[float, float] | Iterable[float]

ConstraintT = TypeVar("ConstraintT", bound=Constraint)

PolygonVisitorCallback = Callable[[list[Vector2], "VisitorAuxiliary"], None]
CircleVisitorCallback = Callable[[Vector2, float, "VisitorAuxiliary"], None]