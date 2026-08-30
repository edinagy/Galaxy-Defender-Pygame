import math

import pygame

from intro.cinematic_ui import CinematicOverlay, draw_camera_noise


# Durata totală a călătoriei prin wormhole.
SCENE_DURATION = 12.0

STORY_CUES = (
    (
        0.4,
        3.1,
        "SHIP AI",
        "No star map. No command link. External clocks are diverging from ship time.",
        "ISOLATED TRANSIT",
    ),
    (
        3.2,
        5.9,
        "SHIP AI",
        "Navigation solution impossible. Holding the ship together is now the only priority.",
        "SPATIAL FIELD 78%",
    ),
    (
        6.0,
        8.7,
        "SHIP AI",
        "Source signal detected ahead. It is responding with our own encrypted handshake.",
        "UNKNOWN RESPONSE",
    ),
    (
        8.8,
        10.2,
        "SHIP AI",
        "Brace for uncontrolled emergence.",
        "IMPACT WARNING",
    ),
)


# Reprezintă secvența „Entering Wormhole” și momentul „Emerging...”.
class WormholeScene:

    # Încarcă fundalul, nava și fonturile secvenței.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "wormhole_background.png"
        ),
    ):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        original_background = pygame.image.load(
            background_path
        ).convert()
        self.background = pygame.transform.smoothscale(
            original_background,
            (
                self.width + 100,
                self.height + 70,
            ),
        )

        ship_image = pygame.image.load(
            "assets/images/player_galaxy_defender_v2.png"
        ).convert_alpha()

        # Elimină marginile transparente ale noului sprite înainte de scalare.
        visible_bounds = ship_image.get_bounding_rect(min_alpha=8)
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            ship_image = ship_image.subsurface(visible_bounds).copy()
        self.original_ship_image = pygame.transform.smoothscale(
            ship_image,
            (122, 138),
        )

        self.small_font = pygame.font.Font(None, 27)
        self.medium_font = pygame.font.Font(None, 40)
        self.title_font = pygame.font.Font(None, 74)
        self.cinematic = CinematicOverlay()

        self.reset()

    # Resetează timpul și valorile spațiu-timp afișate de HUD.
    def reset(self):
        self.elapsed_time = 0.0
        self.travel_progress = 0.0
        self.warp_velocity = 0
        self.spatial_integrity = 100
        self.time_distortion = 0
        self.finished = False

    # ENTER sau SPACE continuă, iar ESC revine la meniu.
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
            self.finished = True
            return "dead_star"

        if event.key == pygame.K_ESCAPE:
            return "menu"

        return None

    # Actualizează progresul și valorile fictive măsurate de navă.
    def update(self, delta_time):
        self.elapsed_time += delta_time
        self.travel_progress = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )

        if self.travel_progress < 0.72:
            transit_progress = (
                self.travel_progress / 0.72
            )
            self.warp_velocity = int(
                98000
                + 802000 * transit_progress
            )
            self.time_distortion = int(
                8 + 87 * transit_progress
            )
            self.spatial_integrity = int(
                100 - 31 * transit_progress
            )
        else:
            emergence_progress = (
                self.travel_progress - 0.72
            ) / 0.28
            self.warp_velocity = max(
                0,
                int(
                    880000
                    * (1 - emergence_progress)
                ),
            )
            self.time_distortion = max(
                0,
                int(
                    95
                    * (1 - emergence_progress)
                ),
            )
            self.spatial_integrity = min(
                100,
                int(
                    69
                    + 31 * emergence_progress
                ),
            )

        if (
            self.elapsed_time >= SCENE_DURATION
            and not self.finished
        ):
            self.finished = True
            return "dead_star"

        return None

    # Calculează o tranziție lină între două poziții.
    @staticmethod
    def _smoothstep(value):
        return value * value * (3 - 2 * value)

    # Desenează toate straturile secvenței.
    def draw(self):
        self._draw_background()
        self._draw_energy_rings()
        self._draw_ship()
        self._draw_transit_interface()
        draw_camera_noise(
            self.screen,
            self.elapsed_time,
            1.0 + self.travel_progress * 0.8,
        )
        self.cinematic.draw(
            self.screen,
            self.elapsed_time,
            STORY_CUES,
            "PROLOGUE 07  //  UNKNOWN TRANSIT",
            "NO EXTERNAL REFERENCE",
        )
        self._draw_emergence_flash()
        self._draw_fade()

    # Mișcă fundalul pentru a accentua viteza din interiorul tunelului.
    def _draw_background(self):
        transit_strength = min(
            1.0,
            self.travel_progress / 0.65,
        )
        horizontal_offset = int(
            -50
            + math.sin(
                self.elapsed_time * 2.4
            )
            * 7
            * transit_strength
        )
        vertical_offset = int(
            -35
            + math.cos(
                self.elapsed_time * 1.9
            )
            * 5
            * transit_strength
        )

        self.screen.blit(
            self.background,
            (
                horizontal_offset,
                vertical_offset,
            ),
        )

    # Desenează inele translucide care traversează tunelul.
    def _draw_energy_rings(self):
        if self.travel_progress >= 0.86:
            return

        ring_surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        tunnel_center = (
            self.width // 2,
            235,
        )

        for index in range(5):
            ring_phase = (
                self.elapsed_time * 0.74
                + index / 5
            ) % 1.0
            ring_width = int(
                95 + ring_phase * 650
            )
            ring_height = int(
                55 + ring_phase * 390
            )
            ring_alpha = int(
                60 * (1 - ring_phase)
            )
            ring_rect = pygame.Rect(
                0,
                0,
                ring_width,
                ring_height,
            )
            ring_rect.center = tunnel_center

            pygame.draw.ellipse(
                ring_surface,
                (
                    120,
                    215,
                    255,
                    ring_alpha,
                ),
                ring_rect,
                2,
            )

        self.screen.blit(
            ring_surface,
            (0, 0),
        )

    # Desenează nava îndepărtându-se spre punctul luminos al tunelului.
    def _draw_ship(self):
        if self.travel_progress >= 0.84:
            return

        ship_progress = min(
            1.0,
            self.travel_progress / 0.84,
        )
        eased_progress = self._smoothstep(
            ship_progress
        )
        ship_scale = max(
            0.28,
            1.0 - 0.72 * eased_progress,
        )
        ship_rotation = (
            math.sin(self.elapsed_time * 3.0)
            * (
                2
                + 9 * eased_progress
            )
        )

        ship_image = pygame.transform.rotozoom(
            self.original_ship_image,
            ship_rotation,
            ship_scale,
        )

        sideways_motion = (
            math.sin(self.elapsed_time * 2.1)
            * (
                8
                + 24 * eased_progress
            )
            * (1 - eased_progress * 0.65)
        )
        ship_x = int(
            self.width // 2
            - ship_image.get_width() // 2
            + sideways_motion
        )
        ship_y = int(
            520 - 300 * eased_progress
        )

        glow_surface = pygame.Surface(
            (
                ship_image.get_width() + 44,
                ship_image.get_height() + 44,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            glow_surface,
            (
                110,
                210,
                255,
                int(
                    32
                    + 55 * ship_progress
                ),
            ),
            glow_surface.get_rect(),
        )
        self.screen.blit(
            glow_surface,
            (ship_x - 22, ship_y - 22),
        )

        # Nava se micșorează treptat pe măsură ce înaintează prin tunel.
        self.screen.blit(
            ship_image,
            (ship_x, ship_y),
        )

    # Desenează etapa curentă și informațiile de tranzit.
    def _draw_transit_interface(self):
        if self.travel_progress < 0.22:
            title = "FORCED TRANSIT"
            status = "REFERENCE FRAME LOST"
            status_color = (120, 225, 255)
        elif self.travel_progress < 0.72:
            title = "SPACETIME TRANSIT"
            status = "NAVIGATION DATA UNRELIABLE"
            status_color = (195, 175, 255)
        else:
            title = "EMERGING..."
            status = "RECALIBRATING SENSORS"
            status_color = (235, 245, 255)

        self._draw_text_with_shadow(
            title,
            self.title_font,
            38,
            (235, 245, 255),
        )

        status_surface = self.medium_font.render(
            status,
            True,
            status_color,
        )
        self.screen.blit(
            status_surface,
            (
                self.width // 2
                - status_surface.get_width() // 2,
                108,
            ),
        )

        if self.travel_progress < 0.84:
            self._draw_telemetry_panel(
                status_color
            )
            self._draw_progress_bar()


    # Desenează viteza, integritatea spațială și distorsiunea temporală.
    def _draw_telemetry_panel(
        self,
        accent_color,
    ):
        panel = pygame.Surface(
            (335, 150),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (5, 9, 28, 180),
            panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel,
            (
                *accent_color,
                120,
            ),
            panel.get_rect(),
            2,
            border_radius=12,
        )

        velocity_text = self.small_font.render(
            (
                "WARP VELOCITY "
                f"{self.warp_velocity:06d}"
            ),
            True,
            (215, 235, 250),
        )
        integrity_text = self.small_font.render(
            (
                "SPATIAL FIELD "
                f"{self.spatial_integrity:03d}%"
            ),
            True,
            (
                (255, 175, 115)
                if self.spatial_integrity < 75
                else (170, 225, 255)
            ),
        )
        distortion_text = self.small_font.render(
            (
                "TIME OFFSET   "
                f"{self.time_distortion:02d}%"
            ),
            True,
            accent_color,
        )

        panel.blit(velocity_text, (20, 20))
        panel.blit(integrity_text, (20, 61))
        panel.blit(distortion_text, (20, 103))
        self.screen.blit(
            panel,
            (26, self.height - 180),
        )

    # Desenează bara de progres prin tunel.
    def _draw_progress_bar(self):
        bar_rect = pygame.Rect(
            self.width // 2 - 210,
            self.height - 48,
            420,
            10,
        )
        pygame.draw.rect(
            self.screen,
            (18, 23, 45),
            bar_rect,
            border_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            (115, 130, 255),
            (
                bar_rect.x,
                bar_rect.y,
                int(
                    bar_rect.width
                    * self.travel_progress
                ),
                bar_rect.height,
            ),
            border_radius=5,
        )

    # Creează lumina puternică din momentul ieșirii din wormhole.
    def _draw_emergence_flash(self):
        if self.travel_progress < 0.72:
            return

        emergence_progress = (
            self.travel_progress - 0.72
        ) / 0.28
        flash_alpha = int(
            245
            * min(
                1.0,
                emergence_progress / 0.58,
            )
        )

        flash_surface = pygame.Surface(
            (self.width, self.height)
        )
        flash_surface.fill(
            (225, 242, 255)
        )
        flash_surface.set_alpha(
            flash_alpha
        )
        self.screen.blit(
            flash_surface,
            (0, 0),
        )

        if emergence_progress >= 0.42:
            emerging_text = self.title_font.render(
                "EMERGING...",
                True,
                (25, 55, 95),
            )
            self.screen.blit(
                emerging_text,
                (
                    self.width // 2
                    - emerging_text.get_width()
                    // 2,
                    self.height // 2 - 30,
                ),
            )

    # Desenează textul centrat și umbra lui.
    def _draw_text_with_shadow(
        self,
        text,
        font,
        y_position,
        color,
    ):
        text_surface = font.render(
            text,
            True,
            color,
        )
        shadow_surface = font.render(
            text,
            True,
            (2, 4, 16),
        )
        text_x = (
            self.width // 2
            - text_surface.get_width() // 2
        )
        self.screen.blit(
            shadow_surface,
            (text_x + 3, y_position + 3),
        )
        self.screen.blit(
            text_surface,
            (text_x, y_position),
        )

    # Creează fade-in la început și fade-out după flash-ul de ieșire.
    def _draw_fade(self):
        fade_alpha = 0

        if self.elapsed_time < 1.0:
            fade_alpha = int(
                255
                * (1 - self.elapsed_time)
            )
        elif self.elapsed_time > 10.9:
            fade_alpha = int(
                255
                * min(
                    1.0,
                    (
                        self.elapsed_time - 10.9
                    )
                    / 0.6,
                )
            )

        if fade_alpha <= 0:
            return

        fade_surface = pygame.Surface(
            (self.width, self.height)
        )
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade_alpha)
        self.screen.blit(
            fade_surface,
            (0, 0),
        )
