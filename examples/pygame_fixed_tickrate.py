from math import cos, sin, atan2
from random import uniform

import nova
import pygame

from _pygamebase import PygameExample


Transform = tuple[nova.Vector2, float]


def xform_lerp(a: Transform, b: Transform, t: float) -> Transform:
    """
    Interpolate between two transforms.

    Parameters
    ----------
    a
        First transform
    b
        Second transform
    t
        Interpolation alpha
    """

    x = (1.0 - t) * a[0].x + t * b[0].x
    y = (1.0 - t) * a[0].y + t * b[0].y

    # https://stackoverflow.com/a/67219519
    c = (1 - t) * cos(a[1]) + t * cos(b[1])
    s = (1 - t) * sin(a[1]) + t * sin(b[1])
    angle = atan2(s, c)

    return (nova.Vector2(x, y), angle)


class FixedTickRateExample(PygameExample):
    def __init__(self):
        super().__init__((1280, 720))

        # This example implements "Fix Your Timestep!" article
        # https://gafferongames.com/post/fix_your_timestep/

        # Set target FPS to 0 (boundless) so rendering is done as fast as possible
        # (decoupled from physics)
        self.target_fps = 0

        # Fixed physics tick rate
        # (I chose a low value as 20Hz to be able to see the difference
        #  between interpolation on and off more clearly.)
        self.physics_dt = 1.0 / 20.0

        # For interpolation between last physics ticks and rendering
        self.old_xforms: dict[nova.RigidBody, Transform] = {}
        self.xforms: dict[nova.RigidBody, Transform] = {}

        # When the framerate drops too low because of fixed ticks, the accumulator
        # tries to fight this by increasing the amount of physics ticks done per
        # frame. And in the end it enters a feedback loop, dropping the framerate to 0.
        # To combat this, we limit the amount of physics ticks per frame.
        self.maximum_ticks_per_frame = 3

        # dt accumulator
        self.accumulator = 0.0

        self.interpolation = True

        self.space = nova.Space()
        self.space.visitor(nova.ShapeType.POLYGON)(self.draw_poly)
        self.space.visitor(nova.ShapeType.CIRCLE)(self.draw_circle)

        self.crate = nova.RigidBody(
            type=nova.RigidBodyType.DYNAMIC,
            position=nova.Vector2(0.0, 0.0),
        )
        self.crate.add_shape(nova.ShapeFactory.box(22.0, 2.0, nova.Vector2(0.0, -10.0)))
        self.crate.add_shape(nova.ShapeFactory.box(22.0, 2.0, nova.Vector2(0.0, 10.0)))
        self.crate.add_shape(nova.ShapeFactory.box(2.0, 22.0, nova.Vector2(-10.0, 0.0)))
        self.crate.add_shape(nova.ShapeFactory.box(2.0, 22.0, nova.Vector2(10.0, 0.0)))
        self.space.add_rigidbody(self.crate)

        hinge = nova.HingeConstraint(None, self.crate, nova.Vector2())
        self.space.add_constraint(hinge)

        for _ in range(100):
            box = nova.RigidBody(
                type=nova.RigidBodyType.DYNAMIC,
                position=nova.Vector2(uniform(-7.5, 7.5), uniform(-7.5, 7.5))
            )
            box.add_shape(nova.ShapeFactory.box(uniform(0.5, 1.5), uniform(0.5, 1.5)))
            self.space.add_rigidbody(box)

    def draw_poly(self,
            vertices: list[nova.Vector2],
            aux: nova.VisitorAuxiliary
            ) -> None:
        
        # Visitor callbacks take already transformed shape data
        # So for interpolation we need to transform manually using the data
        # we have been keeping track of between fixed tick calls.
        
        if not self.interpolation:
            points = [self.world_to_screen(v).to_tuple() for v in vertices]
            pygame.draw.polygon(self.display, (207, 100, 64), points, 2)

        elif aux.body in self.xforms:
            xform = self.xforms[aux.body]

            delta_xform = (xform[0] - aux.body.position, xform[1] - aux.body.angle)

            aux.shape.transform(aux.body, delta_xform)

            points = [self.world_to_screen(v).to_tuple() for v in aux.shape.transformed_vertices]
            pygame.draw.polygon(self.display, (0, 0, 0), points, 2)

    def draw_circle(self,
            center: nova.Vector2,
            radius: float,
            aux: nova.VisitorAuxiliary
            ) -> None:
        
        if not self.interpolation:
            pygame.draw.circle(
                self.display,
                (207, 100, 64),
                self.world_to_screen(center).to_tuple(),
                radius * self.zoom,
                2
            )

        elif aux.body in self.xforms:
            xform = self.xforms[aux.body] 

            delta_xform = (xform[0] - aux.body.position, xform[1] - aux.body.angle)

            aux.shape.transform(aux.body, delta_xform)

            pygame.draw.circle(
                self.display,
                (0, 0, 0),
                self.world_to_screen(aux.shape.transformed_center).to_tuple(),
                radius * self.zoom,
                2
            )

    def update(self) -> None:
        if pygame.key.get_just_pressed()[pygame.K_q]:
            self.interpolation = not self.interpolation

        # self.dt => time elapsed to render the last frame in seconds
        self.accumulator += self.dt
        current_ticks = 0

        while self.accumulator >= self.physics_dt:
            if current_ticks < self.maximum_ticks_per_frame:
                self.tick()

            self.accumulator -= self.physics_dt
            current_ticks += 1

        # Interpolation alpha (t)
        alpha = self.accumulator / self.physics_dt

        # Interpolate transforms from last tick to current rendering frame
        for body, xform in self.old_xforms.items():
            new_xform = (body.position, body.angle)
            self.xforms[body] = xform_lerp(xform, new_xform, alpha)

    def tick(self) -> None:
        # This is the method called only at fixed intervals, decoupled from rendering.
        # You can also implement game logic, not only physics.

        if self.crate.angular_velocity < 0.5:
            self.crate.apply_torque(10000)

        # Make sure to store old transforms *before* advancing the simulation
        for body in self.space.iter_bodies():
            self.old_xforms[body] = (body.position, body.angle)

        self.space.step(self.physics_dt)

    def render(self) -> None:
        self.ui_text = [
            f"Tickrate: {round(1.0 / self.physics_dt)}Hz",
            f"Interpolation: {('Off', 'On')[self.interpolation]}",
            "  ^ Press [Q]"
        ]

        self.space.visit_geometry()


if __name__ == "__main__":
    example = FixedTickRateExample()
    example.run()