import random
from pathlib import Path

import pygame


class Player:

    # Creează nava jucătorului și toate stările temporare ale acesteia.
    def __init__(self):
        self.image = self._load_ship_image()

        # Noul sprite ocupă aproape toată imaginea, așa că îl afișăm puțin
        # mai mic pentru a păstra suficient spațiu de evitare în arenă.
        self.image = pygame.transform.smoothscale(
            self.image,
            (118, 124),
        )

        self.x = 640 - self.image.get_width() // 2
        self.y = 550
        self.speed = 8

        self.rect = self.image.get_rect(
            topleft=(self.x, self.y)
        )

        # Particulele motoarelor continuă să se miște după navă.
        self.engine_particles = []

        # Invincibilitate scurtă după ce nava este lovită.
        self.invincible = False
        self.invincible_timer = 0

        # Sistemul permanent al armei pentru run-ul curent.
        self.weapon_level = 1
        self.maximum_weapon_level = 4
        self.weapon_feedback_timer = 0
        self.weapon_feedback_type = None

        # Energia abilității speciale se păstrează pe navă în timpul rundei.
        # La 100 de puncte, jucătorul poate activa unda cu tasta E.
        self.special_energy = 0
        self.maximum_special_energy = 100

        # Atributul vechi rămâne disponibil pentru elementele HUD existente.
        self.double_shot = False
        self.double_shot_timer = 0

        # Power-up pentru scutul temporar.
        self.shield = False
        self.shield_timer = 0

    # Sincronizează starea veche DUAL FIRE cu noul nivel al armei.
    def _sync_weapon_state(self):
        self.double_shot = self.weapon_level >= 2
        self.double_shot_timer = 0

    # Crește arma cu un nivel și returnează True dacă upgrade-ul a fost aplicat.
    def upgrade_weapon(self):
        if self.weapon_level >= self.maximum_weapon_level:
            self.weapon_feedback_timer = 70
            self.weapon_feedback_type = "maximum"
            return False

        self.weapon_level += 1
        self._sync_weapon_state()
        self.weapon_feedback_timer = 100
        self.weapon_feedback_type = "upgrade"
        return True

    # Pierde un singur nivel după damage, dar nu coboară niciodată sub nivelul 1.
    def downgrade_weapon(self):
        if self.weapon_level <= 1:
            return False

        self.weapon_level -= 1
        self._sync_weapon_state()
        self.weapon_feedback_timer = 120
        self.weapon_feedback_type = "downgrade"
        return True

    # Încarcă noul sprite premium și elimină spațiul transparent din jurul lui.
    def _load_ship_image(self):
        images_folder = (
            Path(__file__).resolve().parent
            / "assets"
            / "images"
        )
        premium_image_path = (
            images_folder
            / "player_galaxy_defender_v2.png"
        )
        old_image_path = (
            images_folder
            / "player_galaxy_defender.png"
        )

        # Imaginea veche rămâne rezervă dacă noul PNG nu a fost încă adăugat.
        image_path = (
            premium_image_path
            if premium_image_path.exists()
            else old_image_path
        )

        ship_image = pygame.image.load(
            str(image_path)
        ).convert_alpha()

        visible_bounds = ship_image.get_bounding_rect(
            min_alpha=8
        )
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            ship_image = ship_image.subsurface(
                visible_bounds
            ).copy()

        return ship_image

    # Returnează pozițiile celor două duze ale motoarelor.
    def _get_engine_positions(self):
        return (
            (
                self.x + self.image.get_width() * 0.39,
                self.y + self.image.get_height() - 4,
            ),
            (
                self.x + self.image.get_width() * 0.61,
                self.y + self.image.get_height() - 4,
            ),
        )

    # Citește tastele WASD și deplasează nava în interiorul ecranului.
    def move(self, screen_width, screen_height):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.x -= self.speed

        if keys[pygame.K_d]:
            self.x += self.speed

        if keys[pygame.K_w]:
            self.y -= self.speed

        if keys[pygame.K_s]:
            self.y += self.speed

        # Nava nu poate ieși în afara arenei.
        if self.x < 0:
            self.x = 0

        if self.x > screen_width - self.image.get_width():
            self.x = screen_width - self.image.get_width()

        if self.y < 0:
            self.y = 0

        if self.y > screen_height - self.image.get_height():
            self.y = screen_height - self.image.get_height()

        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    # Actualizează motoarele și timerele power-up-urilor.
    def update(self):
        self.update_engine()

        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        if self.weapon_feedback_timer > 0:
            self.weapon_feedback_timer -= 1
        else:
            self.weapon_feedback_type = None

        if self.shield:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield = False

    # Creează particule exact sub cele două motoare ale navei.
    def update_engine(self):
        if random.randint(1, 2) == 1:
            for engine_x, engine_y in self._get_engine_positions():
                maximum_life = random.randint(16, 27)
                self.engine_particles.append(
                    {
                        "x": engine_x + random.uniform(-2.0, 2.0),
                        "y": engine_y + random.uniform(4.0, 8.0),
                        "velocity_x": random.uniform(-0.35, 0.35),
                        "velocity_y": random.uniform(3.6, 5.8),
                        "size": random.randint(2, 5),
                        "life": maximum_life,
                        "maximum_life": maximum_life,
                    }
                )

        for particle in self.engine_particles[:]:
            particle["x"] += particle["velocity_x"]
            particle["y"] += particle["velocity_y"]
            particle["life"] -= 1
            particle["size"] = max(
                1,
                particle["size"] - 0.08,
            )

            if particle["life"] <= 0:
                self.engine_particles.remove(particle)

    # Desenează o flacără animată, stratificată și luminoasă.
    def _draw_engine_flame(
        self,
        screen,
        engine_x,
        engine_y,
    ):
        flame_surface = pygame.Surface(
            (48, 72),
            pygame.SRCALPHA,
        )
        center_x = 24
        flame_start_y = 7
        flame_length = random.randint(24, 34)

        # Aura albastră moale din jurul jetului.
        pygame.draw.ellipse(
            flame_surface,
            (0, 105, 255, 55),
            (7, 1, 34, flame_length + 29),
        )

        # Stratul exterior al flăcării.
        pygame.draw.polygon(
            flame_surface,
            (0, 115, 255, 185),
            (
                (center_x - 9, flame_start_y),
                (center_x + 9, flame_start_y),
                (center_x + 5, flame_start_y + flame_length * 0.58),
                (center_x, flame_start_y + flame_length),
                (center_x - 5, flame_start_y + flame_length * 0.58),
            ),
        )

        # Miezul cyan și alb al motorului.
        pygame.draw.polygon(
            flame_surface,
            (60, 225, 255, 225),
            (
                (center_x - 5, flame_start_y),
                (center_x + 5, flame_start_y),
                (center_x + 3, flame_start_y + flame_length * 0.46),
                (center_x, flame_start_y + flame_length * 0.72),
                (center_x - 3, flame_start_y + flame_length * 0.46),
            ),
        )
        pygame.draw.ellipse(
            flame_surface,
            (235, 255, 255, 245),
            (center_x - 4, flame_start_y - 2, 8, 13),
        )

        screen.blit(
            flame_surface,
            (
                int(engine_x - center_x),
                int(engine_y - flame_start_y),
            ),
        )

    # Desenează particulele care se sting treptat în urma navei.
    def _draw_engine_particles(self, screen):
        for particle in self.engine_particles:
            life_ratio = (
                particle["life"]
                / particle["maximum_life"]
            )
            particle_color = (
                int(30 + 80 * life_ratio),
                int(120 + 120 * life_ratio),
                255,
            )
            pygame.draw.circle(
                screen,
                particle_color,
                (
                    int(particle["x"]),
                    int(particle["y"]),
                ),
                max(1, int(particle["size"])),
            )

    # Desenează motoarele, nava și efectele power-up-urilor.
    def draw(self, screen):
        self._draw_engine_particles(screen)

        for engine_x, engine_y in self._get_engine_positions():
            self._draw_engine_flame(
                screen,
                engine_x,
                engine_y,
            )

        # În timpul invincibilității, nava clipește pentru feedback vizual.
        if (
            not self.invincible
            or pygame.time.get_ticks() % 200 < 100
        ):
            screen.blit(
                self.image,
                (int(self.x), int(self.y)),
            )

        # Scutul urmărește forma verticală a noii nave.
        if self.shield:
            shield_rect = self.rect.inflate(26, 16)
            pygame.draw.ellipse(
                screen,
                (20, 105, 255),
                shield_rect,
                5,
            )
            pygame.draw.ellipse(
                screen,
                (100, 225, 255),
                shield_rect.inflate(-7, -7),
                2,
            )
