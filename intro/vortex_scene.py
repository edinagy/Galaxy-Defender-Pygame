import math

import pygame


# Durata apropierii de vortex înainte de următoarea zonă a campaniei.
SCENE_DURATION = 11.0


# Reprezintă secvența cinematică „Beyond the Vortex”.
class VortexScene:

    # Încarcă fundalul, nava jucătorului și fonturile scenei.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "vortex_background.png"
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
                self.width + 110,
                self.height + 70,
            ),
        )

        self.original_ship_image = pygame.image.load(
            "assets/images/player_galaxy_defender.png"
        ).convert_alpha()

        self.small_font = pygame.font.Font(None, 27)
        self.medium_font = pygame.font.Font(None, 38)
        self.title_font = pygame.font.Font(None, 72)

        self.reset()

    # Readuce scena la primul cadru și resetează datele de navigație.
    def reset(self):
        self.elapsed_time = 0.0
        self.approach_progress = 0.0
        self.distance = 8200
        self.gravity_level = 0
        self.finished = False

    # ENTER sau SPACE continuă, iar ESC revine la meniul principal.
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
            self.finished = True
            return "asteroids"

        if event.key == pygame.K_ESCAPE:
            return "menu"

        return None

    # Actualizează apropierea, distanța și intensitatea gravitației.
    def update(self, delta_time):
        self.elapsed_time += delta_time

        self.approach_progress = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )

        eased_progress = self._smoothstep(
            self.approach_progress
        )
        self.distance = max(
            340,
            int(8200 - 7860 * eased_progress),
        )
        self.gravity_level = min(
            99,
            int(
                8
                + 91
                * self.approach_progress
                * self.approach_progress
            ),
        )

        if (
            self.elapsed_time >= SCENE_DURATION
            and not self.finished
        ):
            self.finished = True
            return "asteroids"

        return None

    # Calculează o mișcare lină pentru apropierea navei de vortex.
    @staticmethod
    def _smoothstep(value):
        return value * value * (3 - 2 * value)

    # Desenează toate elementele scenei în ordinea corectă.
    def draw(self):
        self._draw_background()
        self._draw_gravity_distortion()
        self._draw_ship()
        self._draw_navigation_interface()
        self._draw_fade()

    # Mișcă foarte puțin fundalul pentru a sugera instabilitatea spațiului.
    def _draw_background(self):
        pull_strength = (
            self.approach_progress
            * self.approach_progress
        )

        horizontal_shake = int(
            math.sin(self.elapsed_time * 10.5)
            * 3
            * pull_strength
        )
        vertical_shake = int(
            math.cos(self.elapsed_time * 8.5)
            * 2
            * pull_strength
        )

        self.screen.blit(
            self.background,
            (
                -55 + horizontal_shake,
                -35 + vertical_shake,
            ),
        )

    # Desenează unde circulare discrete în jurul vortexului.
    def _draw_gravity_distortion(self):
        distortion_surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )

        vortex_center = (
            self.width // 2,
            245,
        )
        pulse = (
            math.sin(self.elapsed_time * 2.8)
            + 1
        ) / 2

        for index in range(3):
            radius = int(
                180
                + index * 45
                + pulse * 12
            )
            alpha = int(
                (
                    22
                    + 18 * self.approach_progress
                )
                / (index + 1)
            )

            pygame.draw.circle(
                distortion_surface,
                (100, 195, 255, alpha),
                vortex_center,
                radius,
                2,
            )

        self.screen.blit(
            distortion_surface,
            (0, 0),
        )

    # Desenează nava apropiindu-se de vortex și fiind deviată ușor.
    def _draw_ship(self):
        eased_progress = self._smoothstep(
            self.approach_progress
        )

        ship_width = int(
            136 - 48 * eased_progress
        )
        ship_height = int(
            150 - 53 * eased_progress
        )
        ship_image = pygame.transform.smoothscale(
            self.original_ship_image,
            (ship_width, ship_height),
        )

        gravitational_sway = (
            math.sin(self.elapsed_time * 1.8)
            * (
                8
                + 20
                * self.approach_progress
            )
        )
        vibration = (
            math.sin(self.elapsed_time * 25)
            * 2
            * self.approach_progress
        )

        ship_x = int(
            self.width // 2
            - ship_image.get_width() // 2
            + gravitational_sway
            + vibration
        )
        ship_y = int(
            530 - 205 * eased_progress
        )

        # O lumină albastră discretă arată că vortexul influențează nava.
        glow_surface = pygame.Surface(
            (
                ship_width + 50,
                ship_height + 50,
            ),
            pygame.SRCALPHA,
        )
        glow_alpha = int(
            15 + 38 * self.approach_progress
        )
        pygame.draw.ellipse(
            glow_surface,
            (55, 150, 255, glow_alpha),
            glow_surface.get_rect(),
        )
        self.screen.blit(
            glow_surface,
            (ship_x - 25, ship_y - 25),
        )

        # Imaginea navei conține deja flăcările motoarelor.
        # Nu desenăm alte flăcări pentru a evita suprapunerea vizuală.
        self.screen.blit(
            ship_image,
            (ship_x, ship_y),
        )

    # Desenează titlul, avertizarea și informațiile de navigație.
    def _draw_navigation_interface(self):
        self._draw_text_with_shadow(
            "BEYOND THE VORTEX",
            self.title_font,
            38,
            (232, 242, 255),
        )

        warning_color = (
            (255, 115, 150)
            if self.gravity_level >= 70
            else (105, 220, 255)
        )
        warning_text = (
            "CRITICAL GRAVITATIONAL PULL"
            if self.gravity_level >= 70
            else "UNKNOWN ANOMALY DETECTED"
        )
        warning_surface = self.medium_font.render(
            warning_text,
            True,
            warning_color,
        )
        self.screen.blit(
            warning_surface,
            (
                self.width // 2
                - warning_surface.get_width() // 2,
                108,
            ),
        )

        panel = pygame.Surface(
            (315, 150),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (4, 10, 28, 175),
            panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel,
            (95, 175, 255, 125),
            panel.get_rect(),
            2,
            border_radius=12,
        )

        distance_text = self.small_font.render(
            f"DISTANCE     {self.distance:04d} KM",
            True,
            (210, 230, 250),
        )
        gravity_text = self.small_font.render(
            f"GRAVITY PULL {self.gravity_level:02d}%",
            True,
            warning_color,
        )

        if self.approach_progress < 0.38:
            navigation_status = "TRAJECTORY STABLE"
        elif self.approach_progress < 0.72:
            navigation_status = "NAVIGATION UNSTABLE"
        else:
            navigation_status = "AUTOPILOT OVERRIDDEN"

        status_text = self.small_font.render(
            navigation_status,
            True,
            (155, 210, 255),
        )

        panel.blit(distance_text, (20, 22))
        panel.blit(gravity_text, (20, 62))
        panel.blit(status_text, (20, 105))
        self.screen.blit(
            panel,
            (28, self.height - 180),
        )

        self._draw_progress_bar()

        if self.elapsed_time >= 8.0:
            continue_text = self.small_font.render(
                "ENTER / SPACE - CONTINUE",
                True,
                (215, 232, 255),
            )
            self.screen.blit(
                continue_text,
                (
                    self.width
                    - continue_text.get_width()
                    - 30,
                    self.height
                    - continue_text.get_height()
                    - 24,
                ),
            )

    # Desenează progresul apropierii de anomalia spațială.
    def _draw_progress_bar(self):
        bar_rect = pygame.Rect(
            self.width // 2 - 210,
            self.height - 48,
            420,
            10,
        )
        pygame.draw.rect(
            self.screen,
            (16, 24, 47),
            bar_rect,
            border_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            (105, 105, 255),
            (
                bar_rect.x,
                bar_rect.y,
                int(
                    bar_rect.width
                    * self.approach_progress
                ),
                bar_rect.height,
            ),
            border_radius=5,
        )

    # Desenează un text centrat, însoțit de o umbră discretă.
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
            (2, 5, 18),
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

    # Creează fade-in la început și fade-out la finalul scenei.
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
        elif self.elapsed_time > 10.0:
            fade_alpha = int(
                255
                * min(
                    1.0,
                    self.elapsed_time - 10.0,
                )
            )
        else:
            return

        fade_surface.set_alpha(fade_alpha)
        self.screen.blit(fade_surface, (0, 0))
