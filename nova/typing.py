"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import (
    Callable,
    TypeVar,
    Type,
    Any,
    TypeAliasType,
    Union,
    ForwardRef,
    get_args,
    get_origin,
    TYPE_CHECKING
)
from types import UnionType
from collections.abc import Iterable
import inspect

from nova.vector import Vector2

if TYPE_CHECKING:
    from nova.models import VisitorAuxiliary, ContactEvent
    from nova.space import Space
    from nova.body import RigidBody
    from nova.constraint import Constraint


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

    # Caller's module namespace
    caller_frame = inspect.currentframe().f_back
    caller_globals = caller_frame.f_globals
    caller_locals = caller_frame.f_locals

    if isinstance(expected_type, TypeAliasType):
        expected_type = expected_type.__value__

    if get_origin(expected_type) in {Union, UnionType}:
        resolved_types = []

        for t in get_args(expected_type):
            if isinstance(t, ForwardRef):
                t = t.evaluate(
                    globals=caller_globals,
                    locals=caller_locals
                )

            resolved_types.append(t)

        expected_type = tuple(resolved_types)

    elif isinstance(expected_type, ForwardRef):
        expected_type = expected_type.evaluate(
            globals=caller_globals,
            locals=caller_locals
        )

    if not isinstance(value, expected_type):
        raise TypeError(
            f"Argument '{name}' must be {expected_type.__name__}, "
            f"not {type(value).__name__}"
        )

    return value


type Coordinate = Vector2 | tuple[float, float] | Iterable[float]

ConstraintT = TypeVar("ConstraintT", bound="Constraint")
type ConstraintTarget = Union["RigidBody", None]

type ContactEventCallback = Callable[["Space", "ContactEvent", Any], None]

type PolygonVisitorCallback = Callable[[list[Vector2], "VisitorAuxiliary"], None]
type CircleVisitorCallback = Callable[[Vector2, float, "VisitorAuxiliary"], None]