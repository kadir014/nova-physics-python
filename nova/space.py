"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

from typing import Callable, Any, Type, TYPE_CHECKING
from collections.abc import Iterator

from nova.common import lib, ffi, get_error_buffer
from nova.typing import (
    Coordinate,
    ContactEventCallback,
    PolygonVisitorCallback,
    CircleVisitorCallback,
    ConstraintT
)
from nova.error import NovaError, DuplicateError
from nova.models import (
    Profiler,
    BroadPhaseAlgorithm,
    RayCastResult,
    VisitorAuxiliary,
    ShapeType,
    ContactEventType,
    ContactEvent,
    CollisionFilter
)
from nova.vector import Vector2

if TYPE_CHECKING:
    from nova.body import RigidBody


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

        listener_ret = lib.nvSpace_set_contact_listener(
            self._space,
            (ffi.NULL, ffi.NULL, ffi.NULL),
            ffi.NULL
        )
        if listener_ret != 0:
            raise NovaError(get_error_buffer())

        # These need to stay alive with Space
        self._on_added_callback = None
        self._on_persisted_callback = None
        self._on_removed_callback = None
        self._listener_arg_handle = None
        self._listener_arg = None

    def __del__(self) -> None:

        # TODO: nvSpace_free is going to free all bodies and shapes?

        self._on_added_callback = None
        self._on_persisted_callback = None
        self._on_removed_callback = None
        self._listener_arg_handle = None
        self._listener_arg = None

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
        # Remove constraints before altering body in any way
        to_be_removed = []
        for c in self._cons_ref:
            if c.body_a is body or c.body_b is body:
                to_be_removed.append(c)

        for c in to_be_removed:
            self.remove_constraint(c)

        body._refd = False

        ret = lib.nvSpace_remove_rigidbody(self._space, body._rigidbody)
        if ret:
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
        self._profiler.casts = self._space.profiler.casts
        self._profiler.queries = self._space.profiler.queries

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
            ray_from: Coordinate,
            ray_to: Coordinate,
            max_results: int = 512,
            filter: CollisionFilter = CollisionFilter()
            ) -> list[RayCastResult]:
        from_ = Vector2(ray_from).to_tuple()
        to_ = Vector2(ray_to).to_tuple()

        results_ref = lib.nvSpace_cast_ray(
            self._space, from_, to_, max_results, filter.as_c_type()
        )

        if not lib.nvArray_valid(results_ref):
            raise NovaError(get_error_buffer())

        results = []

        for i in range(results_ref.size):
            result = results_ref.data[i * results_ref.element_size]
            body = self._get_body_by_pointer(result.body)
            shape = body._get_shape_by_pointer(result.shape)

            results.append(RayCastResult(
                Vector2(result.position.x, result.position.y),
                Vector2(result.normal.x, result.normal.y),
                body,
                shape
            ))

        lib.nvArray_free(results_ref)

        return results

    def query_point(self,
            point: Coordinate,
            filter: CollisionFilter = CollisionFilter(),
            cheap: bool = False
            ) -> list[RigidBody]:
        point = Vector2(point).to_tuple()

        results_ref = lib.nvSpace_query_point(
            self._space, point, filter.as_c_type(), cheap
        )

        if not lib.nvRefArray_valid(results_ref):
            raise NovaError(get_error_buffer())

        results = []

        for i in range(results_ref.size):
            result = results_ref.data[i]
            body = self._get_body_by_pointer(result)

            results.append(body)

        lib.nvRefArray_free(results_ref)

        return results

    def set_contact_callback(self,
            func: ContactEventCallback,
            type: ContactEventType,
            user_arg: Any | None = None
            ) -> None:
        self._listener_arg = user_arg
        self._listener_arg_handle = ffi.new_handle(self._listener_arg )
        self._space.listener_arg = self._listener_arg_handle

        # All of these arguments are <cdata>, I don't know how to typehint them
        def decorator(c_space, c_event, c_user_arg) -> None:
            # First, validate pointers

            if c_space != self._space:
                raise ValueError(f"Listener space and caller space is not the same. {self._space} != {c_space}.")

            user_arg = ffi.from_handle(c_user_arg)
            if (user_arg is not self._listener_arg):
                raise ValueError(f"Given user argument and caller user argument is not the same. {id(self._listener_arg)} != {id(user_arg)}")

            # Then retrieve event fields

            body_a = self._get_body_by_pointer(c_event.body_a)
            body_b = self._get_body_by_pointer(c_event.body_b)
            event = ContactEvent(
                body_a,
                body_b,
                body_a._get_shape_by_pointer(c_event.shape_a),
                body_b._get_shape_by_pointer(c_event.shape_b),
                Vector2(c_event.normal.x, c_event.normal.y),
                c_event.penetration,
                Vector2(c_event.position.x, c_event.position.y),
                Vector2(c_event.normal_impulse.x, c_event.normal_impulse.y),
                Vector2(c_event.friction_impulse.x, c_event.friction_impulse.y),
                c_event.id
            )

            func(self, event, user_arg)

        c_callback = ffi.callback("nvContactListenerCallback", decorator)

        if type == ContactEventType.ADDED:
            self._space.listener.on_contact_added = c_callback
            self._on_added_callback = c_callback

        elif type == ContactEventType.PERSISTED:
            self._space.listener.on_contact_persisted = c_callback
            self._on_persisted_callback = c_callback

        elif type == ContactEventType.REMOVED:
            self._space.listener.on_contact_removed = c_callback
            self._on_removed_callback = c_callback

        else:
            raise ValueError(f"Unknown contact event type {type}")

        return decorator

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
    def num_bodies(self) -> int:
        return self._space.bodies.size
    
    @property
    def num_constraints(self) -> int:
        return self._space.constraints.size

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