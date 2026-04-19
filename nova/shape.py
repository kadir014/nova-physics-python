"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import TYPE_CHECKING

from nova.common import lib, ffi, get_error_buffer
from nova.typing import Coordinate
from nova.models import ShapeType
from nova.error import NovaError
from nova.vector import Vector2

if TYPE_CHECKING:
    from nova.body import RigidBody


class Shape:
    def __init__(self, cshape) -> None:
        self._shape = cshape
        self._refd = False

        if self._shape == ffi.NULL:
            raise NovaError(get_error_buffer())

    def __del__(self) -> None:
        if self._refd: return
        lib.nvShape_free(self._shape)

    @property
    def type(self) -> ShapeType:
        return ShapeType(self._shape.type)
    
    def transform(self,
            body: "RigidBody",
            offset: tuple[Coordinate, float] | None = None
        ) -> None:
        """
        Transform the shape data to world space from local (body) space.

        The optional `offset` argument is useful for rendering interpolation.

        Shape subclasses must implement this function.

        Parameters
        ----------
        body
            Rigid body to use as the origin for transform
        offset
            Optional relative transform (pair of position and rotation).
        """
        
        raise NotImplementedError()


class Polygon(Shape):
    @property
    def num_vertices(self) -> int:
        """ Number of polygon vertices. """

        return self._shape.polygon.num_vertices
    
    @property
    def vertices(self) -> list[Vector2]:
        """ Polygon vertices in local (body) space. """
        
        verts = []

        for i in range(self._shape.polygon.num_vertices):
            verts.append(Vector2(
                self._shape.polygon.vertices[i].x,
                self._shape.polygon.vertices[i].y
            ))

        return verts
    
    @property
    def transformed_vertices(self) -> list[Vector2]:
        """
        Polygon transformed vertices in world space.
        
        You need to call `transform` method before accessing this property.
        """
        
        verts = []

        for i in range(self._shape.polygon.num_vertices):
            verts.append(Vector2(
                self._shape.polygon.xvertices[i].x,
                self._shape.polygon.xvertices[i].y
            ))

        return verts
    
    def transform(self,
            body: "RigidBody",
            offset: tuple[Coordinate, float] | None = None
        ) -> None:
        """
        Transform the shape data to world space from local (body) space.

        The optional `offset` argument is useful for rendering interpolation.

        Parameters
        ----------
        body
            Rigid body to use as the origin for transform
        offset
            Optional relative transform (pair of position and rotation).
        """

        if offset is None:
            offset = (Vector2(), 0.0)

        offset = (Vector2(offset[0]), offset[1])

        origin = body._rigidbody.origin
        new_xform = (
            (origin.x + offset[0].x, origin.y + offset[0].y),
            body.angle + offset[1]
        )

        lib.nvPolygon_transform(self._shape, new_xform)


class Circle(Shape):
    def __init__(self, cshape) -> None:
        super().__init__(cshape)

        self.__transformed_center = Vector2(-1, -1)

    @property
    def radius(self) -> float:
        """ Radius of circle. """

        return self._shape.circle.radius

    @property
    def center(self) -> Vector2:
        """ Center of circle in local (body) space. """

        return Vector2(self._shape.circle.center.x, self._shape.circle.center.y)
    
    @property
    def transformed_center(self) -> Vector2:
        """
        Center of circle transformed in world space.
        
        You need to call `transform` method before accessing this property.
        """

        return self.__transformed_center

    def transform(self,
            body: "RigidBody",
            offset: tuple[Coordinate, float] | None = None
        ) -> None:
        """
        Transform the shape data to world space from local (body) space.

        The optional `offset` argument is useful for rendering interpolation.

        Parameters
        ----------
        body
            Rigid body to use as the origin for transform
        offset
            Optional relative transform (pair of position and rotation).
        """

        if offset is None:
            offset = (Vector2(), 0.0)

        offset = (Vector2(offset[0]), offset[1])

        center = Vector2(self._shape.circle.center.x, self._shape.circle.center.y)
        center = center.rotate(body.angle + offset[1])

        center.x += body._rigidbody.origin.x
        center.y += body._rigidbody.origin.y

        center += offset[0]

        self.__transformed_center = center


class ShapeFactory:
    """
    Factory class for creating common shapes.

    Methods return specific subclasses of `Shape`, either `Circle` or `Polygon`
    """

    @staticmethod
    def circle(radius: float, center: Vector2 = Vector2(0.0, 0.0)) -> Circle:
        """
        Create a circle shape.

        Parameters
        ----------
        radius
            Radius of the circle.
        center
            Center of the circle in local (body) space.
        """

        shape = lib.nvCircleShape_new(center.to_tuple(), radius)
        if shape == ffi.NULL:
            raise NovaError(get_error_buffer())
        
        return Circle(shape)
    
    @staticmethod
    def polygon(
            vertices: list[Vector2],
            offset: Vector2 = Vector2(0.0, 0.0)
        ) -> Polygon:
        """
        Create a convex polygon shape from given vertices.

        Parameters
        ----------
        vertices
            List of vertices in local (body) space.
        offset
            Offset of the polygon centroid from body origin.
        """

        n = len(vertices)
        vertices_buf = ffi.new(f"nvVector2[{n}]")
        for i in range(n):
            vertices_buf[i] = (vertices[i].x, vertices[i].y)

        shape = lib.nvPolygonShape_new(vertices_buf, n, offset.to_tuple())
        if shape == ffi.NULL:
            raise NovaError(get_error_buffer())

        return Polygon(shape)

    @staticmethod
    def rect(width: float, height: float, offset: Vector2 = Vector2(0.0, 0.0)) -> Polygon:
        """
        Create a rectangle shape with given dimensions.

        Same as `box` method.

        Parameters
        ----------
        width
            Width of the rectangle.
        height
            Height of the rectangle.
        offset
            Offset of the polygon centroid from body origin.
        """

        shape = lib.nvRectShape_new(width, height, offset.to_tuple())
        if shape == ffi.NULL:
            raise NovaError(get_error_buffer())
        
        return Polygon(shape)
    
    @staticmethod
    def box(width: float, height: float, offset: Vector2 = Vector2(0.0, 0.0)) -> Polygon:
        """
        Create a rectangle shape with given dimensions.

        Same as `rect` method.

        Parameters
        ----------
        width
            Width of the rectangle.
        height
            Height of the rectangle.
        offset
            Offset of the polygon centroid from body origin.
        """

        shape = lib.nvRectShape_new(width, height, offset.to_tuple())
        if shape == ffi.NULL:
            raise NovaError(get_error_buffer())
        
        return Polygon(shape)
    
    @staticmethod
    def ngon(n: int, radius: float, offset: Vector2 = Vector2(0.0, 0.0)) -> Polygon:
        """
        Create a convex regular polygon with given number of vertices.

        Parameters
        ----------
        n
            Number of vertices.
        radius
            Distance of one vertex to the polygon centroid.
        offset
            Offset of the polygon centroid from body origin.
        """

        shape = lib.nvNGonShape_new(n, radius, offset.to_tuple())
        if shape == ffi.NULL:
            raise NovaError(get_error_buffer())
        
        return Polygon(shape)