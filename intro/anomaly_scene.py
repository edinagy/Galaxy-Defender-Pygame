import math

import pygame

from intro.cinematic_ui import CinematicOverlay, draw_camera_noise


# Durata avertizării gravitaționale înainte de apariția wormhole-ului.
SCENE_DURATION = 9.5

STORY_CUES = (
    (
        0.4,
        2.9,
        "SHIP AI",
        "Debris field cleared. Main drive is not responding to helm input.",
        "DAMAGE CONTROL",
    ),
    (
        3.0,
        5.7,
        "SHIP AI",
        "The gravity field ahead is collapsing into an artificial transit aperture.",
        "UNKNOWN PHYSICS",
    ),
    (
        5.8,
        7.7,
        "COMMANDER VALE",
        "GF-01, do not enter. Shut down everything and—",
        "WEAK SIGNAL",
    ),
    (
        7.8,
        9.3,
        "SHIP AI",
        "External command link terminated.",
        "SIGNAL LOST",
    ),
)


# Reprezintă scena cinematică „Anomaly Detected”.
class AnomalyScene:

    # Încarcă fundalul, nava și fonturile folosite în această secvență.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "anomaly_background.png"
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
                self.width + 90,
                self.height + 60,
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
            (118, 134),
        )

        self.small_font = pygame.font.Font(None, 27)
        self.medium_font = pygame.font.Font(None, 39)
        self.title_font = pygame.font.Font(None, 76)
        self.cinematic = CinematicOverlay()

        self.reset()

    # Readuce scena la primul cadru și resetează valorile senzorilor.
    def reset(self):
        self.elapsed_time = 0.0
        self.anomaly_progress = 0.0
        self.gravity_percent = 12
        self.navigation_error = 0
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
            return "wormhole"

        if event.key == pygame.K_ESCAPE:
            return "menu"

        return None

    # Actualizează intensitatea anomaliei și erorile de navigație.
    def update(self, delta_time):
        self.elapsed_time += delta_time
        self.anomaly_progress = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )

        accelerated_progress = (
            self.anomaly_progress
            * self.anomaly_progress
        )
        self.gravity_percent = int(
            12 + 215 * accelerated_progress
        )
        self.navigation_error = int(
            3 + 94 * accelerated_progress
        )

        if (
            self.elapsed_time >= SCENE_DURATION
            and not self.finished
        ):
            self.finished = True
            return "wormhole"

        return None

    # Calculează o tranziție lină între două valori.
    @staticmethod
    def _smoothstep(value):
        return value * value * (3 - 2 * value)

    # Desenează toate elementele scenei în ordinea corectă.
    def draw(self):
        self._draw_background()
        self._draw_gravitational_waves()
        self._draw_ship()
        self._draw_warning_interface()
        self._draw_danger_border()
        draw_camera_noise(
            self.screen,
            self.elapsed_time,
            0.7 + self.anomaly_progress * 1.8,
        )
        self.cinematic.draw(
            self.screen,
            self.elapsed_time,
            STORY_CUES,
            "PROLOGUE 06  //  APERTURE COLLAPSE",
            "COMMAND LINK LOST" if self.elapsed_time >= 7.8 else "GRAVITY FAILURE",
        )
        self._draw_fade()

    # Mișcă fundalul din ce în ce mai puternic pe măsură ce nava este atrasă.
    def _draw_background(self):
        shake_strength = (
            1
            + 8
            * self.anomaly_progress
            * self.anomaly_progress
        )
        horizontal_shake = int(
            math.sin(self.elapsed_time * 18)
            * shake_strength
        )
        vertical_shake = int(
            math.cos(self.elapsed_time * 15)
            * shake_strength
            * 0.65
        )

        self.screen.blit(
            self.background,
            (
                -45 + horizontal_shake,
                -30 + vertical_shake,
            ),
        )

    # Desenează unde circulare care arată deformarea spațiului.
    def _draw_gravitational_waves(self):
        wave_surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        anomaly_center = (
            self.width // 2,
            210,
        )

        for index in range(4):
            wave_phase = (
                self.elapsed_time * 0.72
                + index / 4
            ) % 1.0
            radius = int(
                105 + wave_phase * 245
            )
            alpha = int(
                (
                    1 - wave_phase
                )
                * (
                    15
                    + 42 * self.anomaly_progress
                )
            )
            pygame.draw.circle(
                wave_surface,
                (105, 175, 255, alpha),
                anomaly_center,
                radius,
                2,
            )

        self.screen.blit(
            wave_surface,
            (0, 0),
        )

    # Desenează nava deviată și rotită de atracția gravitațională.
    def _draw_ship(self):
        eased_progress = self._smoothstep(
            self.anomaly_progress
        )

        ship_scale = 1.0 - 0.20 * eased_progress
        ship_rotation = (
            math.sin(self.elapsed_time * 2.5)
            * (
                3
                + 13 * eased_progress
            )
        )
        ship_image = pygame.transform.rotozoom(
            self.original_ship_image,
            ship_rotation,
            ship_scale,
        )

        sideways_pull = (
            math.sin(self.elapsed_time * 1.65)
            * (
                12
                + 42 * eased_progress
            )
        )
        vibration = (
            math.sin(self.elapsed_time * 30)
            * 3
            * eased_progress
        )

        ship_x = int(
            self.width // 2
            - ship_image.get_width() // 2
            + sideways_pull
            + vibration
        )
        ship_y = int(
            505 - 155 * eased_progress
        )

        glow_surface = pygame.Surface(
            (
                ship_image.get_width() + 54,
                ship_image.get_height() + 54,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            glow_surface,
            (
                75,
                145,
                255,
                int(
                    18
                    + 48 * eased_progress
                ),
            ),
            glow_surface.get_rect(),
        )
        self.screen.blit(
            glow_surface,
            (ship_x - 27, ship_y - 27),
        )

        # Nava este desenată deasupra câmpului luminos al anomaliei.
        self.screen.blit(
            ship_image,
            (ship_x, ship_y),
        )

    # Desenează titlul și datele de avertizare transmise de senzori.
    def _draw_warning_interface(self):
        title_color = (
            (255, 105, 125)
            if self.anomaly_progress >= 0.55
            else (225, 240, 255)
        )
        self._draw_text_with_shadow(
            "GRAVITY WELL COLLAPSE",
            self.title_font,
            38,
            title_color,
        )

        if self.anomaly_progress < 0.38:
            warning_message = (
                "SCANNING GRAVITATIONAL FIELD"
            )
            warning_color = (100, 215, 255)
        elif self.anomaly_progress < 0.72:
            warning_message = (
                "TRAJECTORY CORRECTION FAILED"
            )
            warning_color = (255, 185, 90)
        else:
            warning_message = (
                "MANUAL CONTROL LOST"
            )
            warning_color = (255, 95, 115)

        warning_surface = self.medium_font.render(
            warning_message,
            True,
            warning_color,
        )
        self.screen.blit(
            warning_surface,
            (
                self.width // 2
                - warning_surface.get_width() // 2,
                112,
            ),
        )

        panel = pygame.Surface(
            (325, 150),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (5, 9, 25, 188),
            panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel,
            (
                *warning_color,
                130,
            ),
            panel.get_rect(),
            2,
            border_radius=12,
        )

        gravity_text = self.small_font.render(
            (
                "GRAVITY       "
                f"{self.gravity_percent:03d}%"
            ),
            True,
            warning_color,
        )
        error_text = self.small_font.render(
            (
                "NAV ERROR     "
                f"{self.navigation_error:02d}%"
            ),
            True,
            (215, 230, 245),
        )
        engine_text = self.small_font.render(
            (
                "ENGINES       OVERRIDDEN"
                if self.anomaly_progress >= 0.72
                else "ENGINES       MAXIMUM"
            ),
            True,
            (
                (255, 105, 120)
                if self.anomaly_progress >= 0.72
                else (150, 215, 255)
            ),
        )

        panel.blit(gravity_text, (20, 20))
        panel.blit(error_text, (20, 60))
        panel.blit(engine_text, (20, 103))
        self.screen.blit(
            panel,
            (26, self.height - 180),
        )

        self._draw_progress_bar()


    # Desenează o margine roșie intermitentă când pericolul devine critic.
    def _draw_danger_border(self):
        if self.anomaly_progress < 0.55:
            return

        pulse = (
            math.sin(self.elapsed_time * 8)
            + 1
        ) / 2
        danger_surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        border_alpha = int(
            25
            + 65
            * pulse
            * self.anomaly_progress
        )
        pygame.draw.rect(
            danger_surface,
            (255, 45, 70, border_alpha),
            danger_surface.get_rect(),
            9,
        )
        self.screen.blit(
            danger_surface,
            (0, 0),
        )

    # Desenează bara de progres până la pierderea completă a controlului.
    def _draw_progress_bar(self):
        bar_rect = pygame.Rect(
            self.width // 2 - 210,
            self.height - 48,
            420,
            10,
        )
        pygame.draw.rect(
            self.screen,
            (18, 23, 42),
            bar_rect,
            border_radius=5,
        )

        if self.anomaly_progress < 0.60:
            progress_color = (90, 195, 255)
        else:
            progress_color = (255, 80, 105)

        pygame.draw.rect(
            self.screen,
            progress_color,
            (
                bar_rect.x,
                bar_rect.y,
                int(
                    bar_rect.width
                    * self.anomaly_progress
                ),
                bar_rect.height,
            ),
            border_radius=5,
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
            (2, 4, 14),
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

    # Creează tranziția neagră de la început și de la final.
    def _draw_fade(self):
        fade_surface = pygame.Surface(
            (self.width, self.height)
        )
        fade_surface.fill((0, 0, 0))

        if self.elapsed_time < 1.0:
            fade_alpha = int(
                255
                * (1 - self.elapsed_time)
            )
        elif self.elapsed_time > 8.65:
            fade_alpha = int(
                255
                * min(
                    1.0,
                    (
                        self.elapsed_time - 8.65
                    )
                    / 0.8,
                )
            )
        else:
            return

        fade_surface.set_alpha(fade_alpha)
        self.screen.blit(
            fade_surface,
            (0, 0),
        )
