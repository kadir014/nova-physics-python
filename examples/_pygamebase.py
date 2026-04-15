import pygame
import nova


class PygameExample:
    """
    Base example class that handles most pygame boilerplate.
    """

    def __init__(self,
            window_size: tuple[int, int],
            target_fps: float = 60.0
            ) -> None:
        """
        Parameters
        ----------
        window_size
            Window dimensions in pixels
        target_fps
            Maximum FPS cap
        """
        self.window_size = window_size
        
        pygame.init()
        self.display = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Pygame-CE & Nova Physics Example")
        self.clock = pygame.Clock()
        self.font = pygame.font.SysFont("FiraCode-Medium", 14)
        self.text_bg = pygame.Surface((1, 1))
        self.is_running = False

        self.target_fps = target_fps
        self.mouse = pygame.Vector2()
        self.pmouse = nova.Vector2()
        self.events: list[pygame.Event] = []

        self.zoom = 30.0
        self.camera = pygame.Vector2()

        self.space: nova.Space

    def world_to_screen(self,
            p: nova.Vector2 | pygame.Vector2 | tuple[float, float]
            ) -> nova.Vector2:
        """
        Transform position from physics world space into screen space.
        """
        p = nova.Vector2(*p)
        half_screen = pygame.Vector2(*self.window_size) / (self.zoom * 2.0)
        return (p - (self.camera - half_screen)) * self.zoom

    def screen_to_world(self,
            p: nova.Vector2 | pygame.Vector2 | tuple[float, float]
            ) -> nova.Vector2:
        """
        Transform position from screen space into physics world space.
        """
        p = nova.Vector2(*p)
        half_screen = pygame.Vector2(*self.window_size) / (self.zoom * 2.0)
        return (p / self.zoom) + (self.camera - half_screen)

    def stop(self) -> None:
        self.is_running = False

    def run(self) -> None:
        self.is_running = True

        while self.is_running:
            self.clock.tick(self.target_fps)

            self.events = pygame.event.get()

            self.mouse = pygame.Vector2(*pygame.mouse.get_pos())
            self.pmouse = self.screen_to_world(self.mouse)

            for event in self.events:
                if event.type == pygame.QUIT:
                    self.stop()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.stop()

            self.update()

            self.display.fill((255, 255, 255))
            
            self.render()

            ui_text = (
                f"Pygame-CE: {pygame.ver}\n"
                f"Nova (py): {nova.__version__}\n"
                f"Nova:      {nova.__nova_version__}\n"
                "\n"
                f"FPS: {round(self.clock.get_fps(), 1)}\n"
                f"Physics: {round(self.space.profiler.step * 1000, 3)}ms\n"
                f"Raycasts: {round(self.space.profiler.raycasts * 1000, 3)}ms\n"
                f"Bodies: {self.space.num_bodies}\n"
                f"Constraints: {self.space.num_constraints}\n"
                "\n"
                f"Zoom: {self.zoom}x\n"
                f"Camera: {round(self.camera.x, 2)}, {round(self.camera.y, 2)}"
            )
            text_surf = self.font.render(ui_text, True, (255, 255, 255))

            new_text_bg = pygame.Surface(text_surf.get_rect().inflate(20, 20).size)
            if new_text_bg.get_rect() > self.text_bg.get_rect():
                self.text_bg = new_text_bg
                self.text_bg.set_alpha(160)

            self.display.blit(self.text_bg, (0, 0))
            self.display.blit(text_surf, (10, 10))

            pygame.display.flip()

    def update(self) -> None:
        ...

    def render(self) -> None:
        ...