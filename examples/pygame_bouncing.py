import nova
import pygame

from _pygamebase import PygameExample


class BouncingExample(PygameExample):
    def __init__(self):
        super().__init__((1280, 720))

        self.physics_dt = 1.0 / 60.0

        self.space = nova.Space()
        self.space.visitor(nova.ShapeType.POLYGON)(self.draw_poly)
        self.space.visitor(nova.ShapeType.CIRCLE)(self.draw_circle)

        ground = nova.RigidBody(
            position=nova.Vector2(0.0, 10.0),
            material=nova.Material(restitution=1.0)
        )
        ground.add_shape(nova.ShapeFactory.box(50.0, 1.0))
        self.space.add_rigidbody(ground)

        radius = 0.5
        num_balls = 35

        for i in range(num_balls):
            restitution = i / (num_balls - 1)

            # Perfect (1.0 on 1.0) restitution can lead to overshoot
            # better lose energy
            restitution *= 0.98

            x = -(num_balls - 1) * radius + i * radius * 2

            ball = nova.RigidBody(
                type=nova.RigidBodyType.DYNAMIC,
                position=nova.Vector2(x, -10.0),
                material=nova.Material(restitution=restitution)
            )

            # Reduce the radius just a little bit so balls don't touch each other
            ball.add_shape(nova.ShapeFactory.circle(radius * 0.95))

            self.space.add_rigidbody(ball)

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

    def update(self) -> None:
        self.space.step(self.physics_dt)

    def render(self) -> None:
        # Draw the spawn point for reference
        pygame.draw.line(
            self.display,
            (255, 150, 115),
            self.world_to_screen((-50, -10)).to_tuple(),
            self.world_to_screen((50, -10)).to_tuple()
        )

        self.space.visit_geometry()


if __name__ == "__main__":
    example = BouncingExample()
    example.run()