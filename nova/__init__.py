from typing import Type, TypeVar, Callable, Any
from collections.abc import Iterator

from dataclasses import dataclass
from enum import Enum
from math import sqrt, cos, sin, radians

import _nova

lib = _nova.lib
ffi = _nova.ffi

__version_major__ = 0
__version_minor__ = 2
__version_patch__ = 2
__version__ = f"{__version_major__}.{__version_minor__}.{__version_patch__}"


EnforcedT = TypeVar("T")
def _enforce(
        name: str,
        value: object,
        expected_type: Type[EnforcedT]
    ) -> EnforcedT:
    """ Enforce the expected type, raise TypeError if fails. """

    if not isinstance(value, expected_type):
        raise TypeError(
            f"Argument '{name}' must be {expected_type.__name__}, "
            f"not {type(value).__name__}"
        )

    return value


def get_error_buffer() -> str:
    error_buf = ffi.string(lib.nv_get_error())
    return error_buf.decode("utf-8")

def get_version_buffer() -> str:
    error_buf = ffi.string(lib.nv_get_version())
    return error_buf.decode("utf-8")


class NovaError(Exception):
    """ A low-level error occured in the C library. """

class DuplicateError(Exception):
    """ Either a body or constraint is added to space more than once. """


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
            x: "float | Vector2 | tuple[float, float] | None" = None,
            y: float | int | None = None
        ) -> None:
        """
        `Vector2()` -> `Vector2(0.0, 0.0)`

        `Vector2(float)` -> `Vector2(float, float)`

        `Vector2(x_float, y_float)` -> `Vector2(x_float, y_float)`

        `Vector2(Vector2)` -> `Vector2(Vector2.x, Vector2.y)`

        `Vector2(tuple[float, ...])` -> `Vector2(x_float, y_float)`

        Parameters
        ----------
        x
            X component of the vector.
        y
            Y component of the vector.
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
        
        elif isinstance(x, tuple):
            self.x = x[0]
            self.y = x[1] if len(x) > 1 else x[0]

        else:
            raise TypeError("Arguments must be float, Vector2 or a tuple of floats")

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
    

Coordinate = Vector2 | tuple[float, float]


@dataclass
class AABB:
    """
    Axis-aligned bounding box.
    """

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def collide_aabb(self, aabb: "AABB") -> bool:
        """ Check collision against another AABB. """
    
        return not (self.max_x <= aabb.min_x or aabb.max_x <= self.min_x or
                    self.max_y <= aabb.min_y or aabb.max_y <= self.min_y)

    def collide_point(self, point: Vector2) -> bool:
        """ Check if point is inside AABB. """

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


class BroadPhaseAlgorithm(Enum):
    BRUTE_FORCE = 0
    BVH = 1


class SpaceSettings:
    def __init__(self, space: "Space") -> None:
        self.__settings = lib.nvSpace_get_settings(space._space)

    @property
    def baumgarte(self) -> float:
        return self.__settings.baumgarte
    
    @baumgarte.setter
    def baumgarte(self, value: float) -> None:
        self.__settings.baumgarte = value

    @property
    def penetration_slop(self) -> float:
        return self.__settings.penetration_slop
    
    @penetration_slop.setter
    def penetration_slop(self, value: float) -> None:
        self.__settings.penetration_slop = value

    @property
    def velocity_iterations(self) -> float:
        return self.__settings.velocity_iterations
    
    @velocity_iterations.setter
    def velocity_iterations(self, value: float) -> None:
        self.__settings.velocity_iterations = value

    @property
    def substeps(self) -> int:
        return self.__settings.substeps
    
    @substeps.setter
    def substeps(self, value: int) -> None:
        self.__settings.substeps = value

    @property
    def linear_damping(self) -> float:
        return self.__settings.linear_damping
    
    @linear_damping.setter
    def linear_damping(self, value: float) -> None:
        self.__settings.linear_damping = value

    @property
    def angular_damping(self) -> float:
        return self.__settings.angular_damping
    
    @angular_damping.setter
    def angular_damping(self, value: float) -> None:
        self.__settings.angular_damping = value

    @property
    def warmstarting(self) -> bool:
        return self.__settings.warmstarting
    
    @warmstarting.setter
    def warmstarting(self, value: bool) -> None:
        self.__settings.warmstarting = value

PolygonVisitorCallback = Callable[[list[Vector2], "Space", "RigidBody", "Shape", Any | None], None]
CircleVisitorCallback = Callable[[Vector2, float, "Space", "RigidBody", "Shape", Any | None], None]

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

class Space:
    def __init__(self) -> None:
        self._space = lib.nvSpace_new()
        self._body_ref: list[RigidBody] = [] # To keep bodies from GC'd
        self._cons_ref: list[Type["ConstraintT"]] = []

        if self._space == ffi.NULL:
            raise NovaError(get_error_buffer())
        
        self._profiler = Profiler()

        self._settings = SpaceSettings(self)

        self._poly_visitor: PolygonVisitorCallback | None = None
        self._circle_visitor: CircleVisitorCallback | None = None

    def __del__(self) -> None:

        # TODO: nvSpace_free is going to free all bodies and shapes?

        lib.nvSpace_free(self._space)

    def _get_body_by_pointer(self, cbody) -> "RigidBody | None":
        for body in self._body_ref:
            if body._rigidbody == cbody:
                return body
        return None
    
    def _get_constraint_by_pointer(self, ccons) -> Type["ConstraintT"]:
        for cons in self._cons_ref:
            if cons._cons == ccons:
                return cons
        return None

    def add_rigidbody(self, body: "RigidBody") -> None:
        body._refd = True
        ret = lib.nvSpace_add_rigidbody(self._space, body._rigidbody)
        if ret == 2:
            raise DuplicateError("Can't add same body to same space more than once.")
        elif ret != 0:
            raise NovaError(get_error_buffer())
        self._body_ref.append(body)

    def remove_rigidbody(self, body: "RigidBody") -> None:
        body._refd = False
        if lib.nvSpace_remove_rigidbody(self._space, body._rigidbody):
            raise NovaError(get_error_buffer())
        self._body_ref.remove(body)

    def add_constraint(self, constraint: Type["ConstraintT"]) -> None:
        constraint._refd = True
        constraint._space = self
        ret = lib.nvSpace_add_constraint(self._space, constraint._cons)
        if ret == 2:
            raise DuplicateError("Can't add same constraint to same space more than once.")
        elif ret != 0:
            raise NovaError(get_error_buffer())
        self._cons_ref.append(constraint)

    def remove_constraint(self, constraint: Type["ConstraintT"]) -> None:
        constraint._refd = False
        constraint._space = None
        if lib.nvSpace_remove_constraint(self._space, constraint._cons):
            raise NovaError(get_error_buffer())
        self._cons_ref.remove(constraint)

    def iter_bodies(self) -> Iterator["RigidBody"]:
        #body = ffi.new("nvRigidBody **")
        #index = ffi.new("size_t *")
        #while lib.nvSpace_iter_bodies(self._space, body, index):
        #    yield self._get_body_by_pointer(body[0])

        for body in self._body_ref:
            yield body

    def iter_constraints(self) -> Iterator[Type["ConstraintT"]]:
        for cons in self._cons_ref:
            yield cons

    def step(self, dt: float) -> None:
        self._profiler.raycasts = self._space.profiler.raycasts

        lib.nvSpace_step(self._space, dt)

        self._profiler.step = self._space.profiler.step
        self._profiler.broadphase = self._space.profiler.broadphase
        self._profiler.broadphase_finalize = self._space.profiler.broadphase_finalize
        self._profiler.bvh_build = self._space.profiler.bvh_build
        self._profiler.bvh_traverse = self._space.profiler.bvh_traverse
        self._profiler.narrowphase = self._space.profiler.narrowphase
        self._profiler.integrate_accelerations = self._space.profiler.integrate_accelerations
        self._profiler.presolve = self._space.profiler.presolve
        self._profiler.warmstart = self._space.profiler.warmstart
        self._profiler.solve_velocities = self._space.profiler.solve_velocities
        self._profiler.integrate_velocities = self._space.profiler.integrate_velocities

    def visitor(self,
            type: "ShapeType"
            ) -> Callable:

        def decorator(
                visitor_callback: PolygonVisitorCallback | CircleVisitorCallback
                ) -> PolygonVisitorCallback | CircleVisitorCallback:
            if type == ShapeType.POLYGON:
                self._poly_visitor = visitor_callback
            elif type == ShapeType.CIRCLE:
                self._circle_visitor = visitor_callback
            else:
                raise TypeError(f"Visitor type '{type}' is not a valid nova.ShapeType")

            # Original callback is not mutated
            return visitor_callback

        return decorator

    def visit_geometry(self, user_arg: Any | None = None) -> None:
        
        # TODO: Use nvSpace_set_geometry_visitor_callbacks for possibly faster transforms

        for body in self.iter_bodies():
            for shape in body.iter_shapes():

                shape.transform(body)

                if shape.type == ShapeType.POLYGON:
                    if self._poly_visitor is not None:
                        self._poly_visitor(
                            shape.transformed_vertices,
                            VisitorAuxiliary(
                                self,
                                body,
                                shape,
                                user_arg
                            )
                        )
                else:
                    if self._circle_visitor is not None:
                        self._circle_visitor(
                            shape.transformed_center,
                            shape.radius,
                            VisitorAuxiliary(
                                self,
                                body,
                                shape,
                                user_arg
                            )
                        )

    def cast_ray(self,
            ray_from: Vector2,
            ray_to: Vector2,
            max_results: int = 512
            ) -> list[RayCastResult]:
        from_ = ray_from.to_tuple()
        to_ = ray_to.to_tuple()

        results_ = ffi.new(f"nvRayCastResult[{max_results}]")
        num_hits_ = ffi.new("size_t *")

        lib.nvSpace_cast_ray(
            self._space, from_, to_, results_, num_hits_, max_results
        )

        num_hits = int(num_hits_[0])
        results = []

        for i in range(num_hits):
            result = results_[i]
            body = self._get_body_by_pointer(result.body)
            shape = body._get_shape_by_pointer(result.shape)

            results.append(RayCastResult(
                Vector2(result.position.x, result.position.y),
                Vector2(result.normal.x, result.normal.y),
                body,
                shape
            ))

        return results
    
    def total_memory_used(self) -> int:
        """ Get the total amount of memory used by this space instance in bytes. """
        return lib.nvSpace_total_memory_used(self._space)
    
    @property
    def profiler(self) -> Profiler:
        return self._profiler
    
    @property
    def settings(self) -> SpaceSettings:
        return self._settings

    @property
    def broadphase(self) -> BroadPhaseAlgorithm:
        bph = lib.nvSpace_get_broadphase(self._space)
        return BroadPhaseAlgorithm(bph)
    
    @broadphase.setter
    def broadphase(self, broadphase_algorithm: BroadPhaseAlgorithm) -> None:
        if lib.nvSpace_set_broadphase(self._space, broadphase_algorithm.value):
            raise NovaError(get_error_buffer())
        
    @property
    def gravity(self) -> Vector2:
        gravity = lib.nvSpace_get_gravity(self._space)
        return Vector2(gravity.x, gravity.y)
    
    @gravity.setter
    def gravity(self, gravity: Vector2) -> None:
        lib.nvSpace_set_gravity(self._space, gravity.to_tuple())


class ShapeType(Enum):
    CIRCLE = 0
    POLYGON = 1

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
    
    def transform(self, body: "RigidBody") -> None:
        """
        Transform the shape data to world space from local (body) space.

        Shape subclasses must implement this function.

        Parameters
        ----------
        body
            Rigid body to use as the origin for transform
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
    
    def transform(self, body: "RigidBody") -> None:
        """
        Transform the shape data to world space from local (body) space.

        Parameters
        ----------
        body
            Rigid body to use as the origin for transform
        """

        lib.nvPolygon_transform(self._shape, (body._rigidbody.origin, body.angle))

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

    def transform(self, body: "RigidBody") -> None:
        """
        Transform the shape data to world space from local (body) space.

        Parameters
        ----------
        body
            Rigid body to use as the origin for transform
        """

        center = Vector2(self._shape.circle.center.x, self._shape.circle.center.y)
        center = center.rotate(body.angle)
        center.x += body._rigidbody.origin.x
        center.y += body._rigidbody.origin.y

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

        Same as `box` method.

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


@dataclass
class Material:
    density: float = 1.0
    restitution: float = 0.2
    friction: float = 0.5

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.density, self.restitution, self.friction)


class RigidBodyType(Enum):
    STATIC = 0
    DYNAMIC = 1

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
        type = _enforce("type", type, RigidBodyType)
        position = _enforce("position", position, Coordinate)
        angle = _enforce("angle", angle, float)
        linear_velocity = _enforce("linear_velocity", linear_velocity, Coordinate)
        angular_velocity = _enforce("angular_velocity", angular_velocity, float)
        material = _enforce("material", material, Material)

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
        self._shape_ref: list[Shape] = []

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

    def _get_shape_by_pointer(self, cshape) -> Shape | None:
        for shape in self._shape_ref:
            if shape._shape == cshape:
                return shape
        return None

    def add_shape(self, shape: Shape) -> None:
        shape._refd = True
        if (lib.nvRigidBody_add_shape(self._rigidbody, shape._shape)):
            raise NovaError(get_error_buffer())
        self._shape_ref.append(shape)

    def remove_shape(self, shape: Shape) -> None:
        shape._refd = False
        if (lib.nvRigidBody_remove_shape(self._rigidbody, shape._shape)):
            raise NovaError(get_error_buffer())
        self._shape_ref.remove(shape)

    def iter_shapes(self) -> Iterator[Shape]:
        for shape in self._shape_ref:
            yield shape

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


class Constraint:
    def __init__(self, ccons) -> None:
        self._cons = ccons
        self._refd = False

        # This is only existent when constraint is managed by the space
        # it is to access Python representations by pointers
        self._space: Space | None = None

    @property
    def body_a(self) -> RigidBody | None:
        if self._space is None:
            return None
        
        cbody = self._cons.a
        return self._space._get_body_by_pointer(cbody)
    
    @property
    def body_b(self) -> RigidBody | None:
        if self._space is None:
            return None
        
        cbody = self._cons.b
        return self._space._get_body_by_pointer(cbody)

    def __del__(self) -> None:
        if self._refd: return
        lib.nvConstraint_free(self._cons)

ConstraintT = TypeVar("ConstraintT", bound=Constraint)


class DistanceConstraint(Constraint):
    def __init__(
            self,
            body_a: RigidBody | None,
            body_b: RigidBody | None,
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
            body_a: RigidBody,
            body_b: RigidBody,
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