import math

import pygame

from intro.cinematic_ui import CinematicOverlay, draw_camera_noise


# Durata secvenței din hangar înainte de lansarea automată.
SCENE_DURATION = 12.0

STORY_CUES = (
    (
        0.8,
        3.7,
        "FLIGHT CONTROL",
        "Hangar Seven is sealed. Emergency launch window opens in ninety seconds.",
        "HOMEWORLD CONTROL",
    ),
    (
        3.8,
        7.3,
        "SHIP AI",
        "Hull sealed. Navigation green. Weapons restricted until orbital clearance.",
        "GF-01 INTERNAL",
    ),
    (
        7.4,
        11.6,
        "COMMANDER VALE",
        "Three patrols vanished near the signal. You are not being sent to win a war. Find them, then come home.",
        "SECURE CHANNEL 01",
    ),
)


# Reprezintă pregătirea navei în hangarul bazei militare.
# Scena face legătura dintre planeta natală și lansare.
class HangarScene:

    # Încarcă fundalul, nava și fonturile folosite în scenă.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "hangar_background.png"
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
            (self.width, self.height),
        )

        ship_image = pygame.image.load(
            "assets/images/player_galaxy_defender_v2.png"
        ).convert_alpha()

        # Elimină marginile transparente ale noului sprite înainte de scalare.
        visible_bounds = ship_image.get_bounding_rect(min_alpha=8)
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            ship_image = ship_image.subsurface(visible_bounds).copy()
        self.ship_image = pygame.transform.smoothscale(
            ship_image,
            (145, 160),
        )

        self.small_font = pygame.font.Font(None, 28)
        self.medium_font = pygame.font.Font(None, 40)
        self.title_font = pygame.font.Font(None, 72)
        self.cinematic = CinematicOverlay()

        self.reset()

    # Readuce toate animațiile la începutul secvenței.
    def reset(self):
        self.elapsed_time = 0.0
        self.system_progress = 0.0
        self.engine_power = 0.0
        self.finished = False

    # ENTER sau SPACE continuă spre lansare, iar ESC revine la meniu.
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
            self.finished = True
            return "launch"

        if event.key == pygame.K_ESCAPE:
            return "menu"

        return None

    # Actualizează verificările navei și pornirea motoarelor.
    def update(self, delta_time):
        self.elapsed_time += delta_time

        self.system_progress = min(
            1.0,
            self.elapsed_time / 6.5,
        )

        if self.elapsed_time >= 5.0:
            self.engine_power = min(
                1.0,
                self.engine_power
                + delta_time * 0.55,
            )

        if (
            self.elapsed_time >= SCENE_DURATION
            and not self.finished
        ):
            self.finished = True
            return "launch"

        return None

    # Desenează fundalul, nava și interfața cinematică.
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self._draw_ship()
        self._draw_preflight_interface()
        draw_camera_noise(self.screen, self.elapsed_time, 0.35)
        self.cinematic.draw(
            self.screen,
            self.elapsed_time,
            STORY_CUES,
            "PROLOGUE 02  //  HANGAR SEVEN",
            "EMERGENCY SCRAMBLE",
        )
        self._draw_fade()

    # Desenează nava pe platforma centrală.
    def _draw_ship(self):
        ship_x = (
            self.width // 2
            - self.ship_image.get_width() // 2
        )
        ship_y = 430

        # Umbra fixează vizual nava pe podeaua hangarului.
        shadow_surface = pygame.Surface(
            (190, 70),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            shadow_surface,
            (0, 0, 10, 115),
            (20, 22, 150, 32),
        )
        self.screen.blit(
            shadow_surface,
            (ship_x - 22, ship_y + 120),
        )

        # Nava vibrează discret când motoarele sunt pregătite.
        vibration = int(
            math.sin(self.elapsed_time * 30)
            * self.engine_power
            * 2
        )
        self.screen.blit(
            self.ship_image,
            (ship_x + vibration, ship_y),
        )

        # Linia de scanare traversează nava în timpul verificărilor.
        if self.system_progress < 1.0:
            scan_y = int(
                ship_y
                + self.ship_image.get_height()
                * self.system_progress
            )
            scan_surface = pygame.Surface(
                (220, 12),
                pygame.SRCALPHA,
            )
            pygame.draw.line(
                scan_surface,
                (70, 220, 255, 170),
                (10, 6),
                (210, 6),
                2,
            )
            self.screen.blit(
                scan_surface,
                (
                    self.width // 2 - 110,
                    scan_y,
                ),
            )

    # Desenează titlul, verificările și bara de progres.
    def _draw_preflight_interface(self):
        self._draw_text_with_shadow(
            "GF-01  //  EMERGENCY SCRAMBLE",
            self.title_font,
            42,
            (225, 242, 255),
        )

        checks = [
            ("NAVIGATION", 0.18),
            ("LIFE SUPPORT", 0.38),
            ("WEAPONS", 0.58),
            ("MAIN ENGINES", 0.78),
        ]

        panel = pygame.Surface(
            (330, 230),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (5, 12, 28, 155),
            panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel,
            (80, 180, 255, 120),
            panel.get_rect(),
            2,
            border_radius=12,
        )

        panel_title = self.small_font.render(
            "SYSTEM DIAGNOSTICS",
            True,
            (125, 215, 255),
        )
        panel.blit(panel_title, (22, 18))

        for index, (
            system_name,
            required_progress,
        ) in enumerate(checks):
            is_online = (
                self.system_progress
                >= required_progress
            )
            status_text = (
                "ONLINE"
                if is_online
                else "CHECKING"
            )
            status_color = (
                (80, 255, 180)
                if is_online
                else (255, 190, 80)
            )
            line_y = 62 + index * 38

            name_surface = self.small_font.render(
                system_name,
                True,
                (210, 225, 240),
            )
            status_surface = self.small_font.render(
                status_text,
                True,
                status_color,
            )
            panel.blit(name_surface, (22, line_y))
            panel.blit(
                status_surface,
                (
                    305
                    - status_surface.get_width(),
                    line_y,
                ),
            )

        self.screen.blit(panel, (35, 435))
        self._draw_progress_bar()

        if self.system_progress >= 1.0:
            ready_text = self.medium_font.render(
                "LAUNCH CLEARANCE PENDING",
                True,
                (100, 255, 190),
            )
            self.screen.blit(
                ready_text,
                (
                    self.width // 2
                    - ready_text.get_width() // 2,
                    595,
                ),
            )


    # Desenează progresul total al verificărilor.
    def _draw_progress_bar(self):
        progress_rect = pygame.Rect(
            440,
            655,
            400,
            12,
        )
        pygame.draw.rect(
            self.screen,
            (20, 35, 55),
            progress_rect,
            border_radius=6,
        )
        pygame.draw.rect(
            self.screen,
            (60, 205, 255),
            (
                progress_rect.x,
                progress_rect.y,
                int(
                    progress_rect.width
                    * self.system_progress
                ),
                progress_rect.height,
            ),
            border_radius=6,
        )

    # Desenează un text centrat și o umbră pentru lizibilitate.
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

    # Creează un fade-in din negru la începutul scenei.
    def _draw_fade(self):
        fade_duration = 1.2

        if self.elapsed_time >= fade_duration:
            return

        fade_alpha = int(
            255
            * (
                1
                - self.elapsed_time
                / fade_duration
            )
        )
        fade_surface = pygame.Surface(
            (self.width, self.height)
        )
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade_alpha)
        self.screen.blit(fade_surface, (0, 0))
