import math

import pygame

from intro.cinematic_ui import CinematicOverlay, draw_camera_noise


# Durata ultimei secvențe cinematice înainte de lupta principală.
SCENE_DURATION = 13.0

ENEMY_REVEAL_ASSETS = {
    "scout": ("enemy_alien_scout_v2.png", (74, 118)),
    "fighter": ("enemy_alien_fighter_v2.png", (116, 116)),
    "tank": ("enemy_alien_tank_v2.png", (142, 112)),
    "shield_carrier": (
        "enemy_alien_shield_carrier.png",
        (128, 132),
    ),
    "phase_hunter": (
        "enemy_alien_phase_hunter.png",
        (100, 126),
    ),
}

STORY_CUES = (
    (
        0.5,
        3.2,
        "SHIP AI",
        "Transit complete. These coordinates do not exist in Coalition records.",
        "SENSOR REBOOT",
    ),
    (
        3.3,
        5.7,
        "SHIP AI",
        "Source signal confirmed. The structure ahead is not a natural body.",
        "THREAT ANALYSIS",
    ),
    (
        5.8,
        7.9,
        "COMMANDER VALE",
        "GF-01... if you can hear me... find a way home.",
        "FRAGMENTED UPLINK",
    ),
    (
        8.0,
        10.2,
        "SHIP AI",
        "Hostile target locks detected. Five... twelve... twenty-seven.",
        "EMERGENCY",
    ),
    (
        10.3,
        12.5,
        "SHIP AI",
        "No return vector. Weapons restrictions removed.",
        "COMBAT AUTHORITY // LOCAL",
    ),
)


# Reprezintă intrarea în sistemul Dead Star și începutul războiului.
class DeadStarScene:

    # Încarcă fundalul, navele și fonturile folosite în secvență.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "dead_star_background.png"
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
                self.height + 50,
            ),
        )

        player_image = pygame.image.load(
            "assets/images/player_galaxy_defender_v2.png"
        ).convert_alpha()

        # Elimină marginile transparente ale noului sprite înainte de scalare.
        visible_bounds = player_image.get_bounding_rect(min_alpha=8)
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            player_image = player_image.subsurface(visible_bounds).copy()
        self.player_image = pygame.transform.smoothscale(
            player_image,
            (112, 128),
        )

        # Reveal-ul foloseste exact lineup-ul actual din gameplay, nu vechile
        # doua sprite-uri care ramasesera din prima versiune a cinematicului.
        self.enemy_images = {
            enemy_type: self._load_enemy_sprite(
                file_name,
                target_size,
            )
            for enemy_type, (
                file_name,
                target_size,
            ) in ENEMY_REVEAL_ASSETS.items()
        }

        self.small_font = pygame.font.Font(None, 27)
        self.contact_font = pygame.font.Font(None, 18)
        self.medium_font = pygame.font.Font(None, 43)
        self.title_font = pygame.font.Font(None, 75)
        self.logo_font = pygame.font.Font(None, 112)
        self.cinematic = CinematicOverlay()

        self.enemy_formation = [
            {
                "type": "shield_carrier",
                "image": self.enemy_images[
                    "shield_carrier"
                ],
                "start": (-150, -130),
                "target": (230, 205),
                "delay": 0.00,
            },
            {
                "type": "phase_hunter",
                "image": self.enemy_images[
                    "phase_hunter"
                ],
                "start": (
                    self.width + 150,
                    -130,
                ),
                "target": (950, 210),
                "delay": 0.08,
            },
            {
                "type": "tank",
                "image": self.enemy_images["tank"],
                "start": (
                    self.width // 2,
                    -180,
                ),
                "target": (
                    self.width // 2 - 71,
                    170,
                ),
                "delay": 0.15,
            },
            {
                "type": "fighter",
                "image": self.enemy_images[
                    "fighter"
                ],
                "start": (-100, 120),
                "target": (390, 325),
                "delay": 0.22,
            },
            {
                "type": "scout",
                "image": self.enemy_images["scout"],
                "start": (
                    self.width + 100,
                    120,
                ),
                "target": (825, 318),
                "delay": 0.28,
            },
        ]

        self.reset()

    # Incarca, decupeaza transparenta si scaleaza un sprite pentru cinematic.
    @staticmethod
    def _load_enemy_sprite(file_name, target_size):
        image = pygame.image.load(
            f"assets/images/enemies/{file_name}"
        ).convert_alpha()
        visible_bounds = image.get_bounding_rect(
            min_alpha=8
        )
        if (
            visible_bounds.width > 0
            and visible_bounds.height > 0
        ):
            image = image.subsurface(
                visible_bounds
            ).copy()
        return pygame.transform.smoothscale(
            image,
            target_size,
        )

    # Resetează secvența la apariția în sistemul Dead Star.
    def reset(self):
        self.elapsed_time = 0.0
        self.scene_progress = 0.0
        self.enemy_reveal_progress = 0.0
        self.finished = False

    # ENTER sau SPACE pornește lupta, iar ESC revine la meniu.
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
            self.finished = True
            return "gameplay"

        if event.key == pygame.K_ESCAPE:
            return "menu"

        return None

    # Actualizează progresul general și intrarea formației inamice.
    def update(self, delta_time):
        self.elapsed_time += delta_time
        self.scene_progress = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )

        if self.elapsed_time >= 4.0:
            self.enemy_reveal_progress = min(
                1.0,
                (self.elapsed_time - 4.0) / 3.5,
            )

        if (
            self.elapsed_time >= SCENE_DURATION
            and not self.finished
        ):
            self.finished = True
            return "gameplay"

        return None

    # Calculează o tranziție lină pentru pozițiile navelor.
    @staticmethod
    def _smoothstep(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3 - 2 * value)

    # Desenează toate elementele secvenței.
    def draw(self):
        self._draw_background()
        self._draw_player_ship()
        self._draw_enemy_formation()
        self._draw_story_titles()
        self._draw_contact_interface()
        draw_camera_noise(
            self.screen,
            self.elapsed_time,
            0.45 + self.enemy_reveal_progress * 0.8,
        )
        self.cinematic.draw(
            self.screen,
            self.elapsed_time,
            STORY_CUES,
            "PROLOGUE 08  //  UNRECORDED SYSTEM",
            "NO RETURN VECTOR" if self.elapsed_time >= 10.3 else "DEEP SPACE CONTACT",
        )
        self._draw_fade()

    # Deplasează lent fundalul pentru a sugera apropierea de Dead Star.
    def _draw_background(self):
        horizontal_offset = int(
            -35
            + math.sin(self.elapsed_time * 0.20)
            * 8
        )
        vertical_offset = int(
            -25
            + math.cos(self.elapsed_time * 0.16)
            * 5
        )
        self.screen.blit(
            self.background,
            (
                horizontal_offset,
                vertical_offset,
            ),
        )

        # O tentă roșie discretă crește când apar navele inamice.
        if self.enemy_reveal_progress > 0:
            color_overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
            color_overlay.fill(
                (
                    90,
                    0,
                    15,
                    int(
                        28
                        * self.enemy_reveal_progress
                    ),
                )
            )
            self.screen.blit(
                color_overlay,
                (0, 0),
            )

    # Desenează nava jucătorului plutind în partea de jos a cadrului.
    def _draw_player_ship(self):
        if self.elapsed_time >= 10.4:
            return

        entrance_progress = self._smoothstep(
            min(1.0, self.elapsed_time / 2.2)
        )
        ship_x = (
            self.width // 2
            - self.player_image.get_width() // 2
        )
        ship_y = int(
            self.height + 40
            - 195 * entrance_progress
            + math.sin(self.elapsed_time * 2.0)
            * 5
        )

        glow_surface = pygame.Surface(
            (
                self.player_image.get_width() + 46,
                self.player_image.get_height() + 46,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            glow_surface,
            (70, 175, 255, 42),
            glow_surface.get_rect(),
        )
        self.screen.blit(
            glow_surface,
            (ship_x - 23, ship_y - 23),
        )

        # Sprite-ul conține deja flăcările motoarelor.
        self.screen.blit(
            self.player_image,
            (ship_x, ship_y),
        )

    # Desenează navele inamice intrând pe rând în formație.
    def _draw_enemy_formation(self):
        if self.elapsed_time < 4.0:
            return

        # Formația dispare înainte ca logo-ul jocului să ocupe centrul.
        if self.elapsed_time >= 8.4:
            formation_alpha = max(
                0,
                int(
                    255
                    * (
                        1
                        - (self.elapsed_time - 8.4)
                        / 1.0
                    )
                ),
            )
        else:
            formation_alpha = 255

        if formation_alpha <= 0:
            return

        for enemy_data in self.enemy_formation:
            local_progress = (
                self.enemy_reveal_progress
                - enemy_data["delay"]
            ) / (
                1.0 - enemy_data["delay"]
            )
            local_progress = self._smoothstep(
                local_progress
            )

            start_x, start_y = enemy_data[
                "start"
            ]
            target_x, target_y = enemy_data[
                "target"
            ]
            enemy_x = int(
                start_x
                + (target_x - start_x)
                * local_progress
            )
            enemy_y = int(
                start_y
                + (target_y - start_y)
                * local_progress
            )
            enemy_y += int(
                math.sin(
                    self.elapsed_time * 1.8
                    + enemy_data["delay"] * 8
                )
                * 4
                * local_progress
            )

            enemy_type = enemy_data["type"]
            enemy_image = enemy_data["image"].copy()
            if enemy_type == "phase_hunter":
                phase_visibility = (
                    0.72
                    + math.sin(
                        self.elapsed_time * 18.0
                        + enemy_data["delay"] * 11
                    )
                    * 0.18
                )
                enemy_alpha = int(
                    formation_alpha
                    * phase_visibility
                )
            else:
                enemy_alpha = formation_alpha
            enemy_image.set_alpha(
                enemy_alpha
            )

            if local_progress > 0.72:
                accent_color = {
                    "scout": (255, 55, 65),
                    "fighter": (65, 145, 255),
                    "tank": (125, 255, 55),
                    "shield_carrier": (75, 215, 255),
                    "phase_hunter": (235, 70, 255),
                }[enemy_type]
                glow_surface = pygame.Surface(
                    (
                        enemy_image.get_width() + 32,
                        enemy_image.get_height() + 32,
                    ),
                    pygame.SRCALPHA,
                )
                pygame.draw.ellipse(
                    glow_surface,
                    (*accent_color, 34),
                    glow_surface.get_rect(),
                )
                self.screen.blit(
                    glow_surface,
                    (
                        enemy_x - 16,
                        enemy_y - 16,
                    ),
                )

                self._draw_enemy_signature(
                    enemy_type,
                    enemy_image,
                    enemy_x,
                    enemy_y,
                    formation_alpha,
                    local_progress,
                    accent_color,
                )

            self.screen.blit(
                enemy_image,
                (enemy_x, enemy_y),
            )

            if local_progress > 0.84:
                label_alpha = min(
                    formation_alpha,
                    int(
                        255
                        * (local_progress - 0.84)
                        / 0.16
                    ),
                )
                label = self.contact_font.render(
                    enemy_type.replace("_", " ").upper(),
                    True,
                    accent_color,
                )
                label.set_alpha(label_alpha)
                self.screen.blit(
                    label,
                    (
                        enemy_x
                        + enemy_image.get_width() // 2
                        - label.get_width() // 2,
                        enemy_y
                        + enemy_image.get_height()
                        + 4,
                    ),
                )

    # Adauga semnatura vizuala a claselor speciale din gameplay.
    def _draw_enemy_signature(
        self,
        enemy_type,
        enemy_image,
        enemy_x,
        enemy_y,
        formation_alpha,
        local_progress,
        accent_color,
    ):
        center = (
            enemy_x + enemy_image.get_width() // 2,
            enemy_y + enemy_image.get_height() // 2,
        )

        if enemy_type == "shield_carrier":
            shield = pygame.Surface(
                (190, 190),
                pygame.SRCALPHA,
            )
            pulse = (
                0.5
                + math.sin(self.elapsed_time * 4.5)
                * 0.5
            )
            shield_alpha = int(
                min(105, formation_alpha * 0.36)
                * local_progress
            )
            pygame.draw.circle(
                shield,
                (*accent_color, int(shield_alpha * 0.20)),
                (95, 95),
                74,
            )
            pygame.draw.circle(
                shield,
                (*accent_color, shield_alpha),
                (95, 95),
                int(74 + pulse * 4),
                2,
            )
            pygame.draw.arc(
                shield,
                (*accent_color, min(150, shield_alpha + 35)),
                pygame.Rect(14, 14, 162, 162),
                self.elapsed_time * 1.7,
                self.elapsed_time * 1.7 + math.pi * 0.72,
                3,
            )
            self.screen.blit(
                shield,
                (center[0] - 95, center[1] - 95),
            )

        elif enemy_type == "phase_hunter":
            ghost_alpha = int(
                min(72, formation_alpha * 0.24)
                * local_progress
            )
            for offset_x in (-8, 8):
                ghost = enemy_image.copy()
                ghost.set_alpha(ghost_alpha)
                ghost.fill(
                    (*accent_color, 255),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
                self.screen.blit(
                    ghost,
                    (enemy_x + offset_x, enemy_y),
                )

    # Afișează pe rând cele trei momente narative finale.
    def _draw_story_titles(self):
        if self.elapsed_time < 4.0:
            self._draw_centered_text(
                "UNRECORDED SYSTEM",
                self.title_font,
                48,
                (240, 225, 225),
            )
            subtitle = (
                "DISTANCE FROM HOMEWORLD: UNKNOWN"
            )
            subtitle_color = (255, 115, 120)

        elif self.elapsed_time < 8.4:
            self._draw_centered_text(
                "THE SIGNAL HAS A SOURCE",
                self.title_font,
                48,
                (255, 115, 120),
            )
            subtitle = (
                "HOSTILE LOCKS MULTIPLYING"
            )
            subtitle_color = (255, 185, 135)

        else:
            self._draw_centered_text(
                "GALAXY DEFENDER",
                self.logo_font,
                235,
                (225, 244, 255),
            )
            subtitle = (
                "NO ORDERS  //  NO WAY HOME"
            )
            subtitle_color = (115, 220, 255)

        subtitle_surface = self.medium_font.render(
            subtitle,
            True,
            subtitle_color,
        )
        subtitle_y = (
            127
            if self.elapsed_time < 8.4
            else 345
        )
        self.screen.blit(
            subtitle_surface,
            (
                self.width // 2
                - subtitle_surface.get_width() // 2,
                subtitle_y,
            ),
        )


    # Desenează numărul contactelor inamice în faza de confruntare.
    def _draw_contact_interface(self):
        if not (
            4.0
            <= self.elapsed_time
            < 8.4
        ):
            return

        visible_contacts = 0
        for enemy_data in self.enemy_formation:
            local_progress = (
                self.enemy_reveal_progress
                - enemy_data["delay"]
            )
            if local_progress > 0.20:
                visible_contacts += 1

        panel = pygame.Surface(
            (285, 112),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (20, 4, 10, 190),
            panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel,
            (255, 75, 85, 140),
            panel.get_rect(),
            2,
            border_radius=12,
        )

        contacts_text = self.small_font.render(
            (
                "HOSTILE CONTACTS  "
                f"{visible_contacts:02d}"
            ),
            True,
            (255, 135, 140),
        )
        weapons_text = self.small_font.render(
            "WEAPONS SYSTEMS    READY",
            True,
            (220, 230, 240),
        )
        panel.blit(contacts_text, (18, 20))
        panel.blit(weapons_text, (18, 65))
        self.screen.blit(
            panel,
            (25, self.height - 140),
        )

    # Desenează un text centrat și umbra acestuia.
    def _draw_centered_text(
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
            (4, 2, 8),
        )
        text_x = (
            self.width // 2
            - text_surface.get_width() // 2
        )
        self.screen.blit(
            shadow_surface,
            (text_x + 4, y_position + 4),
        )
        self.screen.blit(
            text_surface,
            (text_x, y_position),
        )

    # Creează fade-in la început și fade-out înainte de gameplay.
    def _draw_fade(self):
        fade_alpha = 0

        if self.elapsed_time < 1.0:
            fade_alpha = int(
                255
                * (1 - self.elapsed_time)
            )
        elif self.elapsed_time > 12.1:
            fade_alpha = int(
                255
                * min(
                    1.0,
                    (
                        self.elapsed_time - 12.1
                    )
                    / 0.9,
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
