"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from collections.abc import Iterator, Iterable
from math import sqrt, cos, sin, radians


class Vector2:
    """
    2D vector type.

    Attributes
    ----------
    x
        X component of the vector.
    y
        Y component of the vector.
    """

    __slots__ = ("x", "y")
    
    def __init__(self,
            x: "float | Vector2 | Iterable[float, float] | None" = None,
            y: float | int | None = None
        ) -> None:
        """
        Overloads
        ---------
        Vector2()
            Creates a zero vector (0.0, 0.0).

        Vector2(scalar)
            Sets both components to the same value.

        Vector2(x, y)
            Creates a vector with explicit components.

        Vector2(Vector2)
            Copies another vector.

        Vector2((x, y))
            Creates a vector from a 2-element tuple or iterable.

        Parameters
        ----------
        x
            X component of the vector.
        y
            Y component of the vector (optional if `x` provides both values).
        """
        if x is None:
            self.x = 0.0
            self.y = 0.0

        elif isinstance(x, float):
            self.x = x
            self.y = x if y is None else y

        elif isinstance(x, int):
            self.x = float(x)
            self.y = self.x if y is None else float(y)

        elif isinstance(x, Vector2):
            self.x = x.x
            self.y = x.y
        
        elif isinstance(x, Iterable):
            x = tuple(x)
            if len(x) != 2:
                raise ValueError("Iterable must have exactly 2 elements")
            self.x = float(x[0])
            self.y = float(x[1])

        else:
            raise TypeError("Arguments must be float, Vector2 or an iterable of floats")

    def __repr__(self) -> str:
        return f"<nova.Vector2({round(self.x, 3)}, {round(self.y, 3)})>"
    
    def __getitem__(self, index: int) -> float:
        return (self.x, self.y)[index]

    def __setitem__(self, index: int, value: float) -> float:
        if index == 0:
            self.x = value
        elif index == 1:
            self.y == value
        else:
            raise ValueError(f"Index '{index}' is out of range of a 2 dimensional vector")
        
    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        
    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def __add__(self, vector: "Vector2") -> "Vector2":
        return Vector2(self.x + vector.x, self.y + vector.y)
    
    def __sub__(self, vector: "Vector2") -> "Vector2":
        return Vector2(self.x - vector.x, self.y - vector.y)
    
    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> "Vector2":
        return Vector2(self.x / scalar, self.y / scalar)
    
    def __eq__(self, vector: "Vector2") -> bool:
        return self.x == vector.x and self.y == vector.y
    
    def __neg__(self) -> "Vector2":
        return Vector2(-self.x, -self.y)
    
    def copy(self) -> "Vector2":
        return Vector2(self.x, self.y)
    
    def rotate(self, angle: float) -> "Vector2":
        c = cos(angle)
        s = sin(angle)
        return Vector2(c * self.x - s * self.y, s * self.x + c * self.y)
    
    def rotate_deg(self, angle_degrees: float) -> "Vector2":
        return self.rotate(radians(angle_degrees))
    
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
        dx = (vector.x - self.x)
        dy = (vector.y - self.y)
        return dx * dx + dy * dy
    
    def dist(self, vector: "Vector2") -> float:
        return sqrt(self.dist2(vector))
    
    def normalize(self) -> "Vector2":
        return self / self.len()
    
    def lerp(self, vector: "Vector2", t: float) -> "Vector2":
        alpha = 1.0 - t
        return Vector2(
            alpha * self.x + t * vector.x,
            alpha * self.y + t * vector.y
        )