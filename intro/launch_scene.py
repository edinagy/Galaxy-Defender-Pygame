import math

import pygame

from intro.cinematic_ui import CinematicOverlay, draw_camera_noise


# Durata lansării înainte de trecerea automată spre următoarea zonă.
SCENE_DURATION = 11.5

STORY_CUES = (
    (
        0.7,
        3.6,
        "FLIGHT CONTROL",
        "GF-01, emergency ascent approved. Hold Vector Seven until orbital separation.",
        "HOMEWORLD CONTROL",
    ),
    (
        3.7,
        7.4,
        "COMMANDER VALE",
        "Every defense channel is carrying the same signal. Do not answer it. Observe and report.",
        "SECURE CHANNEL 01",
    ),
    (
        7.5,
        11.2,
        "SHIP AI",
        "Unscheduled gravitational lens detected ahead. Flight corridor is no longer stable.",
        "NAVIGATION WARNING",
    ),
)


# Reprezintă lansarea navei și ieșirea din atmosfera planetei.
class LaunchScene:

    # Încarcă fundalul, nava și fonturile folosite în secvență.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "launch_background.png"
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
                self.width + 70,
                self.height + 40,
            ),
        )

        ship_image = pygame.image.load(
            "assets/images/player_galaxy_defender_v2.png"
        ).convert_alpha()

        # Elimină marginile transparente ale noului sprite înainte de animație.
        visible_bounds = ship_image.get_bounding_rect(min_alpha=8)
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            ship_image = ship_image.subsurface(visible_bounds).copy()
        self.original_ship_image = ship_image

        self.small_font = pygame.font.Font(None, 28)
        self.medium_font = pygame.font.Font(None, 42)
        self.title_font = pygame.font.Font(None, 72)
        self.cinematic = CinematicOverlay()

        self.reset()

    # Readuce lansarea la primul cadru.
    def reset(self):
        self.elapsed_time = 0.0
        self.launch_progress = 0.0
        self.altitude = 0
        self.velocity = 0
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
            return "vortex"

        if event.key == pygame.K_ESCAPE:
            return "menu"

        return None

    # Actualizează progresul lansării, viteza și altitudinea.
    def update(self, delta_time):
        self.elapsed_time += delta_time

        self.launch_progress = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )

        eased_progress = self._smoothstep(
            self.launch_progress
        )
        self.altitude = int(
            120000 * eased_progress
        )
        self.velocity = int(
            7600
            * self.launch_progress
            * self.launch_progress
        )

        if (
            self.elapsed_time >= SCENE_DURATION
            and not self.finished
        ):
            self.finished = True
            return "vortex"

        return None

    # Calculează o accelerare lină, fără schimbări bruște de viteză.
    @staticmethod
    def _smoothstep(value):
        return value * value * (3 - 2 * value)

    # Desenează fundalul, nava, informațiile de zbor și tranzițiile.
    def draw(self):
        self._draw_background()
        self._draw_ship()
        self._draw_flight_interface()
        draw_camera_noise(
            self.screen,
            self.elapsed_time,
            0.25 + max(0.0, self.launch_progress - 0.7) * 1.8,
        )
        self.cinematic.draw(
            self.screen,
            self.elapsed_time,
            STORY_CUES,
            "PROLOGUE 03  //  ORBITAL ASCENT",
            "VECTOR 07 // UNSTABLE" if self.elapsed_time >= 7.5 else "LAUNCH CORRIDOR CLEAR",
        )
        self._draw_fade()

    # Deplasează subtil fundalul pentru a sugera creșterea altitudinii.
    def _draw_background(self):
        vertical_offset = int(
            -35
            + 28 * self.launch_progress
        )
        horizontal_offset = int(
            -35
            + math.sin(
                self.elapsed_time * 0.35
            )
            * 6
        )

        self.screen.blit(
            self.background,
            (
                horizontal_offset,
                vertical_offset,
            ),
        )

    # Desenează nava urcând și micșorându-se ușor spre spațiu.
    def _draw_ship(self):
        eased_progress = self._smoothstep(
            self.launch_progress
        )

        ship_width = int(
            150 - 28 * eased_progress
        )
        ship_height = int(
            165 - 31 * eased_progress
        )
        ship_image = pygame.transform.smoothscale(
            self.original_ship_image,
            (ship_width, ship_height),
        )

        ship_x = (
            self.width // 2
            - ship_image.get_width() // 2
        )
        ship_y = int(
            505 - 225 * eased_progress
        )

        # Umbra dispare treptat pe măsură ce nava părăsește orașul.
        if self.launch_progress < 0.35:
            shadow_alpha = int(
                100
                * (
                    1
                    - self.launch_progress / 0.35
                )
            )
            shadow_surface = pygame.Surface(
                (180, 65),
                pygame.SRCALPHA,
            )
            pygame.draw.ellipse(
                shadow_surface,
                (0, 0, 12, shadow_alpha),
                (20, 20, 140, 28),
            )
            self.screen.blit(
                shadow_surface,
                (ship_x - 20, ship_y + 125),
            )

        # Vibrația crește puțin în etapa de accelerație.
        vibration_strength = min(
            2.0,
            self.launch_progress * 3,
        )
        vibration = int(
            math.sin(self.elapsed_time * 34)
            * vibration_strength
        )

        if self.launch_progress > 0.18:
            trail_alpha = int(115 * min(1.0, self.launch_progress * 1.8))
            trail = pygame.Surface((54, 150), pygame.SRCALPHA)
            pygame.draw.polygon(
                trail,
                (
                    65,
                    190,
                    255,
                    trail_alpha,
                ),
                ((16, 0), (38, 0), (48, 145), (27, 110), (6, 145)),
            )
            self.screen.blit(
                trail,
                (ship_x + ship_width // 2 - 27, ship_y + ship_height - 20),
            )

        self.screen.blit(ship_image, (ship_x + vibration, ship_y))

    # Desenează titlul, altitudinea, viteza și starea lansării.
    def _draw_flight_interface(self):
        self._draw_text_with_shadow(
            "EMERGENCY ASCENT  //  VECTOR 07",
            self.title_font,
            42,
            (232, 246, 255),
        )

        status_panel = pygame.Surface(
            (300, 145),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            status_panel,
            (5, 13, 30, 155),
            status_panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            status_panel,
            (80, 185, 255, 115),
            status_panel.get_rect(),
            2,
            border_radius=12,
        )

        altitude_text = self.small_font.render(
            f"ALTITUDE   {self.altitude:06d} M",
            True,
            (205, 230, 250),
        )
        velocity_text = self.small_font.render(
            f"VELOCITY   {self.velocity:04d} M/S",
            True,
            (205, 230, 250),
        )

        if self.launch_progress < 0.35:
            flight_status = "ATMOSPHERIC ASCENT"
        elif self.launch_progress < 0.75:
            flight_status = "LEAVING ATMOSPHERE"
        else:
            flight_status = "ORBITAL VECTOR LOCKED"

        status_text = self.small_font.render(
            flight_status,
            True,
            (90, 230, 255),
        )

        status_panel.blit(altitude_text, (20, 22))
        status_panel.blit(velocity_text, (20, 60))
        status_panel.blit(status_text, (20, 101))
        self.screen.blit(
            status_panel,
            (28, self.height - 175),
        )

        self._draw_progress_bar()


    # Desenează progresul călătoriei către spațiu.
    def _draw_progress_bar(self):
        bar_rect = pygame.Rect(
            self.width // 2 - 210,
            self.height - 48,
            420,
            10,
        )
        pygame.draw.rect(
            self.screen,
            (18, 30, 50),
            bar_rect,
            border_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            (70, 205, 255),
            (
                bar_rect.x,
                bar_rect.y,
                int(
                    bar_rect.width
                    * self.launch_progress
                ),
                bar_rect.height,
            ),
            border_radius=5,
        )

    # Desenează un text centrat și o umbră discretă.
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
            (3, 7, 18),
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

    # Creează fade-in la început și fade-out la sfârșitul lansării.
    def _draw_fade(self):
        fade_surface = pygame.Surface(
            (self.width, self.height)
        )
        fade_surface.fill((0, 0, 0))

        if self.elapsed_time < 1.2:
            fade_alpha = int(
                255
                * (
                    1
                    - self.elapsed_time / 1.2
                )
            )
        elif self.elapsed_time > 10.6:
            fade_alpha = int(
                255
                * min(
                    1.0,
                    (
                        self.elapsed_time - 10.6
                    )
                    / 0.9,
                )
            )
        else:
            return

        fade_surface.set_alpha(fade_alpha)
        self.screen.blit(fade_surface, (0, 0))
