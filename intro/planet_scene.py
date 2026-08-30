import math

import pygame

from intro.cinematic_ui import CinematicOverlay, draw_camera_noise


# Durata totală a scenei înainte de trecerea automată spre hangar.
SCENE_DURATION = 13.0

STORY_CUES = (
    (
        3.0,
        5.9,
        "SHIP AI",
        "Orbital Defense Grid has gone dark. Multiple civilian lanes are collapsing.",
        "EMERGENCY",
    ),
    (
        6.0,
        9.8,
        "COMMANDER VALE",
        "GF-01, an unknown signal breached the perimeter. Report to Hangar Seven. Now.",
        "SECURE CHANNEL 01",
    ),
    (
        9.9,
        12.7,
        "COMMANDER VALE",
        "Your orders are simple: trace the signal, identify the threat, and protect Homeworld.",
        "MISSION PRIORITY // BLACK",
    ),
)


# Reprezintă primul capitol al campaniei: „We Depart From Our Home”.
# Scena prezintă planeta natală, orașul și nava pregătită de plecare.
class PlanetScene:

    # Încarcă fundalul, nava, fonturile și elementele animate.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "planet_home_background.png"
        ),
        alert_background_path=(
            "assets/images/intro/"
            "planet_home_alert_background.png"
        ),
    ):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Fundalul este puțin mai mare decât ecranul pentru efectul de cameră.
        original_background = pygame.image.load(
            background_path
        ).convert()
        self.background = pygame.transform.smoothscale(
            original_background,
            (
                self.width + 80,
                self.height + 45,
            ),
        )
        alert_background = pygame.image.load(
            alert_background_path
        ).convert()
        self.alert_background = pygame.transform.smoothscale(
            alert_background,
            (self.width + 80, self.height + 45),
        )

        # Nava folosește același design ca în gameplay.
        ship_image = pygame.image.load(
            "assets/images/player_galaxy_defender_v2.png"
        ).convert_alpha()

        # Elimină marginile transparente ale noului sprite înainte de scalare.
        visible_bounds = ship_image.get_bounding_rect(min_alpha=8)
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            ship_image = ship_image.subsurface(visible_bounds).copy()
        self.ship_image = pygame.transform.smoothscale(
            ship_image,
            (130, 145),
        )

        # Fonturile folosite pentru titlul capitolului și mesajele cinematice.
        self.small_font = pygame.font.Font(None, 30)
        self.medium_font = pygame.font.Font(None, 38)
        self.title_font = pygame.font.Font(
            None,
            82,
        )
        self.cinematic = CinematicOverlay()

        self.reset()

    # Readuce scena la început atunci când începe o campanie nouă.
    def reset(self):
        self.elapsed_time = 0.0
        self.camera_offset = 0.0
        self.ship_engine_power = 0.0
        self.alert_progress = 0.0
        self.finished = False

    # Primește comenzile utilizatorului.
    # ENTER sau SPACE continuă, iar ESC revine la meniu.
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
            self.finished = True
            return "hangar"

        if event.key == pygame.K_ESCAPE:
            return "menu"

        return None

    # Actualizează timpul, mișcarea camerei, traficul și motoarele navei.
    def update(self, delta_time):
        self.elapsed_time += delta_time

        # Camera se deplasează lent spre dreapta pentru profunzime.
        self.camera_offset = (
            math.sin(self.elapsed_time * 0.16)
            * 28
        )

        self.alert_progress = max(
            0.0,
            min(1.0, (self.elapsed_time - 2.15) / 0.65),
        )

        # Motoarele încep să se încarce după primirea ordinului de plecare.
        if self.elapsed_time > 8.0:
            self.ship_engine_power = min(
                1.0,
                self.ship_engine_power
                + delta_time * 0.45,
            )

        # După terminarea scenei se cere tranziția automată spre hangar.
        if (
            self.elapsed_time >= SCENE_DURATION
            and not self.finished
        ):
            self.finished = True
            return "hangar"

        return None

    # Desenează toate straturile scenei în ordinea corectă.
    def draw(self):
        self._draw_background()
        self._draw_ship()
        self._draw_cinematic_text()
        draw_camera_noise(
            self.screen,
            self.elapsed_time,
            0.35 + self.alert_progress * 0.65,
        )
        self.cinematic.draw(
            self.screen,
            self.elapsed_time,
            STORY_CUES,
            "PROLOGUE 01  //  HOMEWORLD",
            "ORBITAL EMERGENCY" if self.alert_progress else "DAWN WATCH",
        )
        self._draw_fade()

    # Desenează fundalul cu o mișcare lentă de cameră.
    def _draw_background(self):
        background_x = int(
            -40 + self.camera_offset
        )
        self.screen.blit(
            self.background,
            (background_x, -22),
        )
        if self.alert_progress > 0:
            alert_surface = self.alert_background.copy()
            alert_surface.set_alpha(int(255 * self.alert_progress))
            self.screen.blit(alert_surface, (background_x, -22))

        # Flash-ul scurt marchează ruperea apărării orbitale.
        flash_distance = abs(self.elapsed_time - 2.22)
        if flash_distance < 0.32:
            flash_alpha = int(155 * (1.0 - flash_distance / 0.32))
            flash = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
            flash.fill((255, 220, 180, flash_alpha))
            self.screen.blit(flash, (0, 0))

    # Desenează nava pe platformă și energia motoarelor.
    def _draw_ship(self):
        ship_x = 270
        ship_y = 520

        # Umbra discretă fixează vizual nava pe platformă.
        shadow_surface = pygame.Surface(
            (150, 65),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            shadow_surface,
            (0, 0, 12, 95),
            (15, 24, 120, 28),
        )
        self.screen.blit(
            shadow_surface,
            (ship_x - 10, ship_y + 105),
        )

        # O vibrație discretă arată că motoarele navei sunt pornite.
        vibration = int(
            math.sin(self.elapsed_time * 28)
            * self.ship_engine_power
            * 2
        )

        self.screen.blit(
            self.ship_image,
            (
                ship_x + vibration,
                ship_y,
            ),
        )

    # Desenează textele succesive care prezintă începutul misiunii.
    def _draw_cinematic_text(self):
        if self.elapsed_time < 2.4:
            self._draw_text_with_fade(
                "HOMEWORLD  //  05:42 LOCAL TIME",
                self.small_font,
                76,
                0.2,
                2.4,
                (180, 220, 255),
            )

        if 0.7 <= self.elapsed_time < 2.55:
            self._draw_text_with_fade(
                "THE LAST QUIET MORNING",
                self.title_font,
                112,
                0.7,
                2.55,
                (235, 248, 255),
            )

        if 2.45 <= self.elapsed_time < 5.3:
            self._draw_text_with_fade(
                "ORBITAL DEFENSE FAILURE",
                self.medium_font,
                88,
                2.45,
                5.3,
                (255, 120, 92),
            )

    # Desenează un text care apare și dispare progresiv.
    def _draw_text_with_fade(
        self,
        text,
        font,
        y_position,
        start_time,
        end_time,
        color,
    ):
        fade_duration = 0.8

        fade_in = min(
            1.0,
            (
                self.elapsed_time - start_time
            )
            / fade_duration,
        )
        fade_out = min(
            1.0,
            (
                end_time - self.elapsed_time
            )
            / fade_duration,
        )
        alpha = int(
            255
            * max(
                0.0,
                min(fade_in, fade_out),
            )
        )

        text_surface = font.render(
            text,
            True,
            color,
        )
        text_surface.set_alpha(alpha)

        # O umbră fină păstrează textul lizibil peste zonele luminoase.
        shadow_surface = font.render(
            text,
            True,
            (4, 10, 25),
        )
        shadow_surface.set_alpha(
            int(alpha * 0.75)
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
            (
                text_x,
                y_position,
            ),
        )

    # Creează efectul de apariție din negru la începutul scenei.
    def _draw_fade(self):
        fade_duration = 1.8

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
        self.screen.blit(
            fade_surface,
            (0, 0),
        )
