"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from nova.common import lib, ffi
from nova.typing import Coordinate
from nova.vector import Vector2


def circle_area(radius: float) -> float:
    """
    Calculate area of a circle.

    Parameters
    ----------
    radius
        Radius of the circle.
    """

    return lib.nv_circle_area(radius)

def circle_inertia(
        mass: float,
        radius: float,
        offset: Coordinate = Vector2(0.0, 0.0)
        ) -> float:
    """
    Calculate moment of inertia of a circle.

    Parameters
    ----------
    mass
        Mass of the circle.
    radius
        Radius of the circle.
    offset
        Offset of the circle center.
    """

    offset = Vector2(offset)
    return lib.nv_circle_inertia(mass, radius, offset.to_tuple())

def polygon_area(vertices: list[Coordinate]) -> float:
    """
    Calculate the area of a convex polygon.

    Parameters
    ----------
    vertices
        List of polygon vertices.
    """

    n = len(vertices)
    c_vertices = ffi.new(f"nvVector2[{n}]")
    for i, v in enumerate(vertices):
        v = Vector2(v)
        c_vertices[i] = v.to_tuple()

    return lib.nv_polygon_area(c_vertices, n)

def polygon_inertia(mass: float, vertices: list[Coordinate]) -> float:
    """
    Calculate the moment of inertia of a convex polygon.

    Parameters
    ----------
    mass
        Mass of the polygon.
    vertices
        List of polygon vertices.
    """

    n = len(vertices)
    c_vertices = ffi.new(f"nvVector2[{n}]")
    for i, v in enumerate(vertices):
        v = Vector2(v)
        c_vertices[i] = v.to_tuple()

    return lib.nv_polygon_inertia(mass, c_vertices, n)

def polygon_centroid(vertices: list[Coordinate]) -> float:
    """
    Calculate the centroid of a convex polygon.

    Parameters
    ----------
    vertices
        List of polygon vertices.
    """

    n = len(vertices)
    c_vertices = ffi.new(f"nvVector2[{n}]")
    for i, v in enumerate(vertices):
        v = Vector2(v)
        c_vertices[i] = v.to_tuple()

    return lib.nv_polygon_centroid(c_vertices, n)

def quickhull(points: list[Coordinate]) -> list[Vector2]:
    """
    Generate a convex hull around the given point cloud using QuickHull algorithm.

    Parameters
    ----------
    points
        Point cloud.
    """

    n = len(points)
    c_points = ffi.new(f"nvVector2[{n}]")
    for i, v in enumerate(points):
        v = Vector2(v)
        c_points[i] = v.to_tuple()

    # number of initial point cloud points should be sufficient
    c_hull = ffi.new(f"nvVector2[{n}]")

    n_hull = lib.nv_quickhull(c_points, n, c_hull)

    hull: list[Vector2] = []
    for i in range(n_hull):
        c_hull_v = c_hull[i]
        hull.append(Vector2(c_hull_v.x, c_hull_v.y))

    return hull