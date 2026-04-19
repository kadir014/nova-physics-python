import nova
import pygame

from _pygamebase import PygameExample


class PyramidExample(PygameExample):
    def __init__(self):
        super().__init__((1280, 720))

        self.physics_dt = 1.0 / 60.0

        self.space = nova.Space()
        self.space.visitor(nova.ShapeType.POLYGON)(self.draw_poly)
        self.space.visitor(nova.ShapeType.CIRCLE)(self.draw_circle)

        ground = nova.RigidBody(
            position=nova.Vector2(64.0, 0.0),
            material=nova.Material(restitution=0.1)
        )
        ground.add_shape(nova.ShapeFactory.box(100.0, 5.0))
        self.space.add_rigidbody(ground)

        self.camera = ground.position.copy()
        self.camera.y -= 30
        self.zoom = 10.0


        PYRAMID_BASE = 50
        BOX_SIZE = 1.0
        AIR_GAP = 0.0


        s2 = BOX_SIZE * 0.5
        start_y = 0.0 - 2.5 - s2

        for y in range(PYRAMID_BASE):
            for x in range(PYRAMID_BASE - y):
                box = nova.RigidBody(
                    type=nova.RigidBodyType.DYNAMIC,
                    position=nova.Vector2(
                        64.0 - (PYRAMID_BASE * s2 - s2) + x * BOX_SIZE + y * s2,
                        (start_y - y * (BOX_SIZE + AIR_GAP - 0.015))
                    ),
                    material=nova.Material(friction=0.6, restitution=0.0)
                )
                box.add_shape(nova.ShapeFactory.box(BOX_SIZE, BOX_SIZE))
                self.space.add_rigidbody(box)

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
        self.space.visit_geometry()


if __name__ == "__main__":
    example = PyramidExample()
    example.run()