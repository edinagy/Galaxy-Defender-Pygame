import math

import pygame


# Durata totală a scenei înainte de trecerea automată spre hangar.
SCENE_DURATION = 10.0


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

        # Nava folosește același design ca în gameplay.
        ship_image = pygame.image.load(
            "assets/images/player_galaxy_defender.png"
        ).convert_alpha()
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

        self.reset()

    # Readuce scena la început atunci când începe o campanie nouă.
    def reset(self):
        self.elapsed_time = 0.0
        self.camera_offset = 0.0
        self.ship_engine_power = 0.0
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

        # Motoarele încep să se încarce după prezentarea orașului.
        if self.elapsed_time > 5.0:
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

        # Imaginea navei conține deja flăcările motoarelor.
        # Adăugăm doar o vibrație mică atunci când motoarele sunt pornite.
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
        if self.elapsed_time < 2.6:
            self._draw_text_with_fade(
                "YEAR 2248",
                self.small_font,
                54,
                0.2,
                2.6,
                (180, 220, 255),
            )

        if 1.8 <= self.elapsed_time < 6.4:
            self._draw_text_with_fade(
                "WE DEPART FROM OUR HOME",
                self.title_font,
                92,
                1.8,
                6.4,
                (235, 248, 255),
            )

        if 3.7 <= self.elapsed_time < 8.2:
            self._draw_text_with_fade(
                "MISSION 01  //  DESTINATION: ENEMY TERRITORY",
                self.medium_font,
                180,
                3.7,
                8.2,
                (80, 210, 255),
            )

        if self.elapsed_time >= 7.2:
            continue_text = self.small_font.render(
                "ENTER / SPACE - CONTINUE",
                True,
                (210, 230, 255),
            )

            alpha = int(
                130
                + 125
                * (
                    0.5
                    + 0.5
                    * math.sin(
                        self.elapsed_time * 3
                    )
                )
            )
            continue_text.set_alpha(alpha)

            hint_panel = pygame.Surface(
                (
                    continue_text.get_width() + 26,
                    continue_text.get_height() + 14,
                ),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                hint_panel,
                (5, 12, 30, 145),
                hint_panel.get_rect(),
                border_radius=8,
            )
            hint_panel.blit(
                continue_text,
                (13, 7),
            )

            self.screen.blit(
                hint_panel,
                (
                    self.width
                    - hint_panel.get_width()
                    - 35,
                    self.height
                    - hint_panel.get_height()
                    - 28,
                ),
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
