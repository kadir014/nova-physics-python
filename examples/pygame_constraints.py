import nova
import pygame

from _pygamebase import PygameExample, draw_spring


class ConstraintsExample(PygameExample):
    def __init__(self):
        super().__init__((1280, 720))

        self.physics_dt = 1.0 / 60.0

        self.space = nova.Space()
        self.space.visitor(nova.ShapeType.POLYGON)(self.draw_poly)
        self.space.visitor(nova.ShapeType.CIRCLE)(self.draw_circle)

        ground = nova.RigidBody(position=nova.Vector2(0.0, 0.0))
        ground.add_shape(nova.ShapeFactory.box(40.5, 0.5, nova.Vector2(0.0, 10.0)))
        ground.add_shape(nova.ShapeFactory.box(40.5, 0.5, nova.Vector2(0.0, -10.0)))
        ground.add_shape(nova.ShapeFactory.box(0.5, 20.5, nova.Vector2(-20.0, 0.0)))
        ground.add_shape(nova.ShapeFactory.box(0.5, 20.5, nova.Vector2(20.0, 0.0)))
        ground.add_shape(nova.ShapeFactory.box(0.5, 20.5, nova.Vector2(-7.0, 0.0)))
        ground.add_shape(nova.ShapeFactory.box(0.5, 20.5, nova.Vector2(7.0, 0.0)))
        self.space.add_rigidbody(ground)

        # Hard distance constraint
        self.add_distance_constraint(nova.Vector2(-13.0, 0.0), False)

        # Soft distance constraint (spring)
        self.add_distance_constraint(nova.Vector2(0.0, 0.0), True)

        # Hinge constraint
        self.add_hinge_constraint(nova.Vector2(13.0, 0.0))

        self.grabber: nova.HingeConstraint | None = None

    def add_distance_constraint(self, position: nova.Vector2, soft: bool) -> None:
        body0 = nova.RigidBody(
            type=nova.RigidBodyType.DYNAMIC,
            position=position - nova.Vector2(0.0, -3.0)
        )
        body0.add_shape(nova.ShapeFactory.box(2.0, 2.0))
        self.space.add_rigidbody(body0)

        body1 = nova.RigidBody(
            type=nova.RigidBodyType.DYNAMIC,
            position=position + nova.Vector2(0.0, -3.0)
        )
        body1.add_shape(nova.ShapeFactory.box(2.0, 2.0))
        self.space.add_rigidbody(body1)

        cons = nova.DistanceConstraint(
            body_a=body0,
            body_b=body1,
            # Distance between center of masses as constraint length
            length=(body1.position - body0.position).len(),
            soft=soft,
            hertz=0.3,
            damping=0.5
        )
        self.space.add_constraint(cons)

    def add_hinge_constraint(self, position: nova.Vector2) -> None:
        body0 = nova.RigidBody(
            type=nova.RigidBodyType.DYNAMIC,
            position=position - nova.Vector2(0.0, -3.0)
        )
        body0.add_shape(nova.ShapeFactory.box(2.0, 2.0))
        self.space.add_rigidbody(body0)

        body1 = nova.RigidBody(
            type=nova.RigidBodyType.DYNAMIC,
            position=position + nova.Vector2(0.0, -3.0)
        )
        body1.add_shape(nova.ShapeFactory.box(2.0, 2.0))
        self.space.add_rigidbody(body1)

        cons = nova.HingeConstraint(
            body_a=body0,
            body_b=body1,
            # Midpoint between two balls
            anchor=(body0.position + body1.position) * 0.5
        )
        self.space.add_constraint(cons)

        cons.ignore_collision = True

    def draw_poly(self,
            vertices: list[nova.Vector2],
            aux: nova.VisitorAuxiliary
            ) -> None:
        points = [self.world_to_screen(v).to_tuple() for v in vertices]
        pygame.draw.polygon(self.display, (0, 0, 0), points, 2)

    def draw_circle(self,
            center: nova.Vector2,
            radius: float,
            aux: nova.VisitorAuxiliary
            ) -> None:
        pygame.draw.circle(
            self.display,
            (0, 0, 0),
            self.world_to_screen(center).to_tuple(),
            radius * self.zoom,
            2
        )

    def grab(self) -> None:
        results = self.space.query_point(self.pmouse)

        if len(results) == 0:
            return

        grabbed = results[0]

        if grabbed.type == nova.RigidBodyType.STATIC:
            return

        self.grabber = nova.DistanceConstraint(
            grabbed,
            None,
            0.01,
            (self.pmouse - grabbed.position).rotate(-grabbed.angle),
            self.pmouse,
            True,
            0.3,
            3.0
        )
        self.space.add_constraint(self.grabber)

    def ungrab(self) -> None:
        if self.grabber is None:
            return

        self.space.remove_constraint(self.grabber)

        self.grabber = None

    def update(self) -> None:
        for event in self.events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.grab()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.ungrab()

        if self.grabber is not None:
            self.grabber.anchor_b = self.pmouse

        self.space.step(self.physics_dt)

    def render(self) -> None:
        self.space.visit_geometry()

        for cons in self.space.iter_constraints():
            if isinstance(cons, nova.DistanceConstraint):
                self.draw_distance_constraint(cons)

            elif isinstance(cons, nova.HingeConstraint):
                self.draw_hinge_constraint(cons)

    def draw_distance_constraint(self, cons: nova.DistanceConstraint) -> None:
        color_a = (255, 65, 18)
        color_b = (112, 51, 255)
        color_cons = (0, 232, 131)

        a = cons.anchor_a
        b = cons.anchor_b

        # Transform anchor points to world space (if they're not connected to world itself)
        if cons.body_a is not None:
            a = a.rotate(cons.body_a.angle) + cons.body_a.position
        if cons.body_b is not None:
            b = b.rotate(cons.body_b.angle) + cons.body_b.position

        # Transform them from world space to screen space
        a = self.world_to_screen(a)
        b = self.world_to_screen(b)
        l = cons.length * self.zoom

        # Draw anchors
        pygame.draw.circle(self.display, color_a, a.to_tuple(), 4.0, 2)
        pygame.draw.circle(self.display, color_b, b.to_tuple(), 4.0, 2)

        # Draw links
        if cons.soft:
            draw_spring(
                self.display, color_cons, a.to_tuple(), b.to_tuple(), l, 2
            )
        else:
            pygame.draw.line(
                self.display, color_cons, a.to_tuple(), b.to_tuple(), 2
            )

    def draw_hinge_constraint(self, cons: nova.HingeConstraint) -> None:
        color_a = (255, 65, 18)
        color_b = (112, 51, 255)
        color_cons = (0, 232, 131)
        anchor_radius = 15.0

        anchor_a = cons.xanchor_a
        anchor_b = cons.xanchor_b
        anchor_a = self.world_to_screen(anchor_a)
        anchor_b = self.world_to_screen(anchor_b)

        anchor = (anchor_a + anchor_b) * 0.5

        # Anchor point in world space
        pygame.draw.circle(
            self.display,
            color_cons,
            anchor.to_tuple(),
            anchor_radius,
            2
        )

        # Draw the arm from body A's center of mass to constraint anchor
        delta_a = self.screen_to_world(anchor) - cons.body_a.position
        len_a = delta_a.len()
        n_a = delta_a / len_a
        arm_a = cons.body_a.position + n_a * (len_a - anchor_radius / self.zoom)
        pygame.draw.line(
            self.display,
            color_a,
            self.world_to_screen(cons.body_a.position).to_tuple(),
            self.world_to_screen(arm_a).to_tuple(),
            2
        )

        # Draw the arm from body A's center of mass to constraint anchor
        delta_b = self.screen_to_world(anchor) - cons.body_b.position
        len_b = delta_b.len()
        n_b = delta_b / len_b
        arm_b = cons.body_b.position + n_b * (len_b - anchor_radius / self.zoom)
        pygame.draw.line(
            self.display,
            color_b,
            self.world_to_screen(cons.body_b.position).to_tuple(),
            self.world_to_screen(arm_b).to_tuple(),
            2
        )


if __name__ == "__main__":
    example = ConstraintsExample()
    example.run()