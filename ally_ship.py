import math
import random

import pygame


# Proiectil tras automat de o navă aliată.
class AllyBullet:

    # Primește punctul de pornire și ținta spre care va zbura.
    def __init__(self, start_x, start_y, target_x, target_y):
        self.x = float(start_x)
        self.y = float(start_y)
        self.width = 7
        self.height = 18

        distance_x = target_x - start_x
        distance_y = target_y - start_y
        distance = max(
            1.0,
            math.hypot(distance_x, distance_y),
        )

        projectile_speed = 10.5
        self.speed_x = (
            distance_x / distance
        ) * projectile_speed
        self.speed_y = (
            distance_y / distance
        ) * projectile_speed

        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )

    # Deplasează proiectilul pe direcția calculată la lansare.
    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    # Desenează un laser cyan, diferit de proiectilele jucătorului.
    def draw(self, screen):
        glow_rect = self.rect.inflate(8, 8)
        pygame.draw.ellipse(
            screen,
            (25, 100, 190),
            glow_rect,
        )
        pygame.draw.ellipse(
            screen,
            (80, 225, 255),
            self.rect,
        )
        pygame.draw.line(
            screen,
            (235, 255, 255),
            self.rect.midtop,
            self.rect.midbottom,
            2,
        )


# Navă aliată care intră în arenă, luptă și apoi se retrage.
class AllyShip:

    # Configurează poziția de patrulare și încarcă imaginea navei.
    def __init__(
        self,
        target_center_x,
        target_y,
        screen_height,
        callsign,
    ):
        loaded_image = pygame.image.load(
            "assets/images/allies/"
            "allied_support_fighter.png"
        ).convert_alpha()
        self.image = pygame.transform.smoothscale(
            loaded_image,
            (112, 134),
        )

        self.home_x = float(
            target_center_x
            - self.image.get_width() / 2
        )
        self.home_y = float(target_y)
        self.x = self.home_x
        self.y = float(
            screen_height
            + self.image.get_height()
        )

        self.callsign = callsign
        self.health = 3
        self.state = "entering"
        self.age = random.randint(0, 300)
        self.patrol_phase = random.uniform(
            0,
            math.tau,
        )
        self.fire_timer = random.randint(20, 45)
        self.hit_flash_timer = 0

        self.rect = self.image.get_rect(
            topleft=(int(self.x), int(self.y))
        )

    # Actualizează intrarea, patrularea sau plecarea navei.
    def update(self):
        self.age += 1

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.state == "entering":
            self.y += (
                self.home_y - self.y
            ) * 0.075

            if abs(self.home_y - self.y) < 3:
                self.y = self.home_y
                self.state = "supporting"

        elif self.state == "supporting":
            self.x = (
                self.home_x
                + math.sin(
                    self.age * 0.026
                    + self.patrol_phase
                )
                * 70
            )
            self.y = (
                self.home_y
                + math.sin(
                    self.age * 0.019
                    + self.patrol_phase
                )
                * 22
            )

        elif self.state == "departing":
            self.y -= 8.0

        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    # Trage automat spre cel mai apropiat inamic aflat deasupra navei.
    def try_shoot(self, enemies):
        if self.state != "supporting":
            return None

        self.fire_timer -= 1

        if self.fire_timer > 0:
            return None

        valid_targets = [
            enemy
            for enemy in enemies
            if enemy.rect.centery < self.rect.centery
        ]

        if not valid_targets:
            self.fire_timer = 15
            return None

        target = min(
            valid_targets,
            key=lambda enemy: (
                enemy.rect.centerx
                - self.rect.centerx
            ) ** 2
            + (
                enemy.rect.centery
                - self.rect.centery
            ) ** 2,
        )
        self.fire_timer = random.randint(42, 62)

        return AllyBullet(
            self.rect.centerx - 3,
            self.rect.top,
            target.rect.centerx,
            target.rect.centery,
        )

    # Pornește retragerea fără să întrerupă brusc animația.
    def start_departure(self):
        if self.state not in (
            "destroyed",
            "finished",
        ):
            self.state = "departing"

    # Scade viața navei când este lovită de un proiectil inamic.
    def take_damage(self):
        self.health -= 1
        self.hit_flash_timer = 10

        if self.health <= 0:
            self.state = "destroyed"

    # Indică dacă nava trebuie eliminată cu explozie.
    def is_destroyed(self):
        return self.state == "destroyed"

    # Indică dacă nava a ieșit complet prin partea de sus a ecranului.
    def has_departed(self):
        return (
            self.state == "departing"
            and self.y < -self.image.get_height()
        )

    # Desenează motoarele, nava, indicativul și punctele sale de viață.
    def draw(self, screen, small_font):
        if self.state == "destroyed":
            return

        engine_y = int(
            self.y + self.image.get_height() - 4
        )

        engine_offsets = (
            int(self.image.get_width() * 0.39),
            int(self.image.get_width() * 0.61),
        )

        for engine_offset in engine_offsets:
            engine_x = int(self.x + engine_offset)
            flame_length = random.randint(10, 18)
            pygame.draw.line(
                screen,
                (25, 115, 255),
                (engine_x, engine_y),
                (
                    engine_x,
                    engine_y + flame_length,
                ),
                7,
            )
            pygame.draw.line(
                screen,
                (190, 245, 255),
                (engine_x, engine_y),
                (
                    engine_x,
                    engine_y + flame_length - 4,
                ),
                3,
            )

        if self.hit_flash_timer > 0:
            ship_image = self.image.copy()
            ship_image.fill(
                # Alpha 0 păstrează transparent fundalul imaginii navei.
                (180, 180, 180, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
        else:
            ship_image = self.image

        screen.blit(
            ship_image,
            (int(self.x), int(self.y)),
        )

        callsign_surface = small_font.render(
            self.callsign,
            True,
            (120, 225, 255),
        )
        screen.blit(
            callsign_surface,
            (
                self.rect.centerx
                - callsign_surface.get_width() // 2,
                self.rect.bottom + 8,
            ),
        )

        pip_start_x = self.rect.centerx - 16

        for pip_index in range(3):
            pip_color = (
                (70, 225, 255)
                if pip_index < self.health
                else (45, 60, 75)
            )
            pygame.draw.rect(
                screen,
                pip_color,
                (
                    pip_start_x + pip_index * 12,
                    self.rect.bottom + 27,
                    8,
                    3,
                ),
            )
