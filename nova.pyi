from typing import overload, Union


nova_version: str
version: str

STATIC: int
DYNAMIC: int


class Vector2:
    x: float
    y: float

    @overload
    def __init__(self, x: float, y: float) -> None: ...

    @overload
    def __add__(self, vector: Vector2) -> Vector2: ...

    @overload
    def __sub__(self, vector: Vector2) -> Vector2: ...

    @overload
    def __mul__(self, scalar: float) -> Vector2: ...

    @overload
    def __truediv__(self, scalar: float) -> Vector2: ...


class Space:
    @overload
    def step(self, dt: float, velocity_iters: int, position_iters: int, constraint_iters: int, substeps: int) -> None: ...

    @overload
    def add(self, body: "Body") -> None: ...

    @overload
    def add_constraint(self, constraint: Union["DistanceJoint", "HingeJoint"]) -> None: ...

    @overload
    def remove(self, body: "Body") -> None: ...

    @overload
    def get_bodies(self) -> tuple["Body"]: ...

    @overload
    def get_constraints(self) -> tuple[int, Vector2, Vector2]: ...

    @overload
    def set_shg(self, min_x: float, min_y: float, max_x: float, max_y: float, cell_width: float, cell_height: float) -> None: ...

    @overload
    def get_shg(self) -> tuple[float, float, float, float, float, float]: ...

    @overload
    def set_kill_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float) -> None: ...


class Body:
    type: int
    shape: int
    position: Vector2
    angle: float
    radius: float
    id: int

    @overload
    def __init__(self, type: int, shape: int, x: float, y: float, angle: float, density: float, restitution: float, friction: float, radius: float) -> None: ...

    @overload
    def __repr__(self) -> str: ...

    @overload
    def get_vertices(self) -> tuple[float]: ...

    @overload
    def get_aabb(self) -> tuple[float, float, float, float]: ...

    @overload
    def apply_force(self, force: Vector2) -> None: ...

    @overload
    def apply_force_at(self, force: Vector2, position: Vector2) -> None: ...

    @overload
    def apply_torque(self, torque: float) -> None: ...

    @overload
    def apply_impulse(self, force: Vector2, position: Vector2) -> None: ...

    @overload
    def set_inertia(self, inertia: float) -> None: ...

    @overload
    def get_inertia(self) -> float: ...

    @overload
    def set_position(self, position: Vector2) -> None: ...

    @overload
    def enable_collision(self, collide: bool) -> None: ...

    @overload
    def get_collision_group(self) -> int: ...

    @overload
    def set_collision_group(self, group: int) -> None: ...

    @property
    @overload
    def mass(self) -> float: ...

    @property
    @overload
    def mass(self, value: float) -> None: ...



@overload
def create_circle(type: int, x: float, y: float, angle: float, density: float, restitution: float, friction: float, radius: float) -> Body: ...

@overload
def create_rect(type: int, x: float, y: float, angle: float, density: float, restitution: float, friction: float, width: float, height: float) -> Body: ...

@overload
def create_polygon(type: int, x: float, y: float, angle: float, density: float, restitution: float, friction: float, points: list[tuple[float, float]], hull: bool = False) -> Body: ...


class DistanceJoint:
    length: float

    @overload
    def __init__(self, a: Body, b: Body, anchor_a: Vector2, anchor_b: Vector2, length: float) -> None: ...


class HingeJoint: ...