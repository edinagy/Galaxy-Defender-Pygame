import math
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
        self.controller_movement = (0.0, 0.0)

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
        self.shield_animation_time = random.uniform(0.0, math.tau)
        self.shield_expire_timer = 0
        self.shield_impact_timer = 0
        self.shield_impact_duration = 26
        self.shield_shards = []

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
    def set_controller_movement(self, movement):
        self.controller_movement = (
            float(movement[0]),
            float(movement[1]),
        )

    def move(self, screen_width, screen_height):
        keys = pygame.key.get_pressed()
        horizontal = self.controller_movement[0]
        vertical = self.controller_movement[1]

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            horizontal -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            horizontal += 1.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            vertical -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            vertical += 1.0

        magnitude = math.hypot(horizontal, vertical)
        if magnitude > 1.0:
            horizontal /= magnitude
            vertical /= magnitude

        self.x += horizontal * self.speed
        self.y += vertical * self.speed

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

    # Hitbox-ul de luptă urmărește cockpitul, nu aripile și motoarele navei.
    # Dimensiunea mică permite trecerea corectă printre salvele dense ale bossului.
    def get_hitbox(self):
        hitbox = pygame.Rect(0, 0, 32, 44)
        hitbox.center = (
            self.rect.centerx,
            self.rect.centery,
        )
        return hitbox

    # Actualizează motoarele și timerele power-up-urilor.
    def update(self):
        self.update_engine()
        self.shield_animation_time += 1.0

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
                self.shield_timer = 0
                self.shield_expire_timer = 18

        if self.shield_expire_timer > 0:
            self.shield_expire_timer -= 1

        if self.shield_impact_timer > 0:
            self.shield_impact_timer -= 1
            for shard in self.shield_shards:
                shard["radius"] += shard["speed"]
                shard["angle"] += shard["spin"]
                shard["life"] -= 1
        elif self.shield_shards:
            self.shield_shards.clear()

    # Activează scutul și resetează orice efect vechi de distrugere.
    def activate_shield(self, duration=300):
        self.shield = True
        self.shield_timer = max(1, int(duration))
        self.shield_expire_timer = 0
        self.shield_impact_timer = 0
        self.shield_shards.clear()

    # Consumă scutul la impact și pregătește fragmentele energetice.
    def absorb_shield_hit(self):
        if not self.shield:
            return False

        self.shield = False
        self.shield_timer = 0
        self.shield_expire_timer = 0
        self.shield_impact_timer = self.shield_impact_duration
        self.shield_shards = []

        impact_angle = random.uniform(0.0, math.tau)
        for shard_index in range(22):
            angle = (
                impact_angle
                + shard_index * math.tau / 22
                + random.uniform(-0.10, 0.10)
            )
            self.shield_shards.append(
                {
                    "angle": angle,
                    "radius": random.uniform(54.0, 66.0),
                    "speed": random.uniform(1.8, 4.2),
                    "spin": random.uniform(-0.025, 0.025),
                    "size": random.randint(4, 9),
                    "life": self.shield_impact_duration,
                }
            )
        return True

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

    # Desenează suprafața transparentă, rețeaua hexagonală și arcurile.
    def _draw_shield_field(self, screen, opacity_scale=1.0):
        shield_width = self.rect.width + 42
        shield_height = self.rect.height + 28
        shield_surface = pygame.Surface(
            (shield_width, shield_height),
            pygame.SRCALPHA,
        )
        local_rect = shield_surface.get_rect()
        center_x, center_y = local_rect.center

        # Când scutul este aproape de final, pulsația devine mai rapidă.
        if self.shield and self.shield_timer < 90:
            pulse_speed = 0.48
            minimum_pulse = 0.48
        else:
            pulse_speed = 0.13
            minimum_pulse = 0.76

        pulse = minimum_pulse + (
            1.0 - minimum_pulse
        ) * (
            0.5
            + 0.5 * math.sin(
                self.shield_animation_time * pulse_speed
            )
        )
        opacity = max(
            0.0,
            min(1.0, pulse * opacity_scale),
        )

        pygame.draw.ellipse(
            shield_surface,
            (20, 105, 255, int(28 * opacity)),
            local_rect.inflate(-8, -6),
        )

        # Hexagoanele sunt afișate numai în interiorul câmpului eliptic.
        hex_radius = 10
        horizontal_step = int(math.sqrt(3) * hex_radius)
        vertical_step = int(hex_radius * 1.5)
        row_index = 0
        for hex_y in range(15, shield_height - 10, vertical_step):
            row_offset = horizontal_step // 2 if row_index % 2 else 0
            for hex_x in range(
                10 + row_offset,
                shield_width - 8,
                horizontal_step,
            ):
                normalized_x = (
                    (hex_x - center_x)
                    / max(1.0, shield_width * 0.46)
                )
                normalized_y = (
                    (hex_y - center_y)
                    / max(1.0, shield_height * 0.46)
                )
                if normalized_x ** 2 + normalized_y ** 2 > 0.90:
                    continue

                hex_points = []
                for corner in range(6):
                    angle = math.radians(60 * corner - 30)
                    hex_points.append(
                        (
                            int(hex_x + math.cos(angle) * hex_radius),
                            int(hex_y + math.sin(angle) * hex_radius),
                        )
                    )
                pygame.draw.polygon(
                    shield_surface,
                    (75, 190, 255, int(54 * opacity)),
                    hex_points,
                    1,
                )
            row_index += 1

        # Două margini eliptice și trei arcuri se rotesc independent.
        pygame.draw.ellipse(
            shield_surface,
            (70, 165, 255, int(150 * opacity)),
            local_rect.inflate(-5, -4),
            2,
        )
        pygame.draw.ellipse(
            shield_surface,
            (155, 235, 255, int(185 * opacity)),
            local_rect.inflate(-11, -10),
            1,
        )

        rotation = self.shield_animation_time * 0.035
        arc_rect = local_rect.inflate(-3, -3)
        for arc_index in range(3):
            arc_start = rotation + arc_index * math.tau / 3
            pygame.draw.arc(
                shield_surface,
                (120, 235, 255, int(225 * opacity)),
                arc_rect,
                arc_start,
                arc_start + 0.72,
                4,
            )

        # Punctele energetice circulă pe margine în sens opus arcurilor.
        for mote_index in range(6):
            mote_angle = (
                -rotation * 1.6
                + mote_index * math.tau / 6
            )
            mote_position = (
                int(center_x + math.cos(mote_angle) * shield_width * 0.47),
                int(center_y + math.sin(mote_angle) * shield_height * 0.46),
            )
            pygame.draw.circle(
                shield_surface,
                (205, 250, 255, int(235 * opacity)),
                mote_position,
                2,
            )

        screen.blit(
            shield_surface,
            shield_surface.get_rect(center=self.rect.center),
        )

    # După blocarea loviturii, câmpul se sparge în fragmente luminoase.
    def _draw_shield_impact(self, screen):
        if self.shield_impact_timer <= 0:
            return

        remaining = (
            self.shield_impact_timer
            / self.shield_impact_duration
        )
        progress = 1.0 - remaining
        center = self.rect.center

        wave_width = int(self.rect.width + 45 + progress * 90)
        wave_height = int(self.rect.height + 32 + progress * 70)
        wave_surface = pygame.Surface(
            (wave_width + 12, wave_height + 12),
            pygame.SRCALPHA,
        )
        wave_rect = wave_surface.get_rect().inflate(-8, -8)
        pygame.draw.ellipse(
            wave_surface,
            (75, 190, 255, int(210 * remaining)),
            wave_rect,
            max(1, int(5 * remaining)),
        )
        pygame.draw.ellipse(
            wave_surface,
            (205, 250, 255, int(130 * remaining)),
            wave_rect.inflate(-7, -7),
            2,
        )
        screen.blit(
            wave_surface,
            wave_surface.get_rect(center=center),
        )

        for shard in self.shield_shards:
            if shard["life"] <= 0:
                continue
            shard_fade = shard["life"] / self.shield_impact_duration
            position = (
                int(center[0] + math.cos(shard["angle"]) * shard["radius"]),
                int(center[1] + math.sin(shard["angle"]) * shard["radius"] * 0.78),
            )
            tangent_angle = shard["angle"] + math.pi / 2
            half_size = shard["size"] * 0.65
            shard_start = (
                int(position[0] - math.cos(tangent_angle) * half_size),
                int(position[1] - math.sin(tangent_angle) * half_size),
            )
            shard_end = (
                int(position[0] + math.cos(tangent_angle) * half_size),
                int(position[1] + math.sin(tangent_angle) * half_size),
            )
            shard_color = (
                int(90 * shard_fade),
                int(210 * shard_fade),
                int(255 * shard_fade),
            )
            pygame.draw.line(
                screen,
                shard_color,
                shard_start,
                shard_end,
                max(1, int(3 * shard_fade)),
            )

        if progress < 0.42:
            flash_radius = max(2, int(24 * (1.0 - progress / 0.42)))
            pygame.draw.circle(
                screen,
                (225, 255, 255),
                center,
                flash_radius,
                3,
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

        # Scutul activ are structură hexagonală și arcuri rotative.
        if self.shield:
            self._draw_shield_field(screen)
        elif self.shield_expire_timer > 0:
            self._draw_shield_field(
                screen,
                self.shield_expire_timer / 18,
            )

        self._draw_shield_impact(screen)
