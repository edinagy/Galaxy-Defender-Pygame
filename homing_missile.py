import math
import random
from pathlib import Path

import pygame


# Rachetă ghidată folosită de ultimul challenge înainte de boss.
class HomingMissile:

    # Păstrează sprite-urile deja încărcate, ca fiecare rachetă nouă să nu
    # citească din nou aceleași imagini de pe disc.
    _sprite_cache = {}

    # Configurează tipul, intrarea, combustibilul și manevrabilitatea.
    def __init__(
        self,
        screen_width,
        screen_height,
        missile_type,
        entry_direction,
        wave,
    ):
        self.missile_type = missile_type
        self.entry_direction = entry_direction

        if missile_type == "heavy":
            self.body_length = 64
            self.body_height = 26
            self.sprite_filename = "missile_heavy.png"
            self.render_size = (98, 46)
            self.health = 3
            self.maximum_health = 3
            self.speed = 2.85
            self.turn_rate = 0.036
            self.fuel = 540
            self.points = 85
            self.blast_radius = 78
            self.color = (255, 105, 55)
        elif missile_type == "interceptor":
            self.body_length = 48
            self.body_height = 18
            self.sprite_filename = "missile_interceptor.png"
            self.render_size = (72, 28)
            self.health = 1
            self.maximum_health = 1
            self.speed = 5.1
            self.turn_rate = 0.031
            self.fuel = 330
            self.points = 45
            self.blast_radius = 52
            self.color = (220, 75, 255)
        else:
            self.body_length = 52
            self.body_height = 20
            self.sprite_filename = "missile_standard.png"
            self.render_size = (78, 32)
            self.health = 1
            self.maximum_health = 1
            self.speed = 3.85
            self.turn_rate = 0.058
            self.fuel = 430
            self.points = 30
            self.blast_radius = 58
            self.color = (255, 65, 120)

        self.speed += min(
            0.8,
            max(1, int(wave)) * 0.035,
        )
        self.x = 0.0
        self.y = 0.0
        self.angle = 0.0
        self._configure_entry(
            screen_width,
            screen_height,
        )

        self.arming_timer = 45
        self.age = 0
        self.hit_flash_timer = 0
        self.tracking_enabled = True
        self.expired = False
        self.has_entered_screen = False
        self.trail_points = []

        self.base_image = self._create_image()
        self.image = self.base_image
        self.rect = self.image.get_rect(
            center=(int(self.x), int(self.y))
        )
        collision_size = (
            22 if missile_type == "heavy" else 16
        )
        self.collision_rect = pygame.Rect(
            0,
            0,
            collision_size,
            collision_size,
        )
        self.collision_rect.center = self.rect.center

    # Așază racheta în exterior și o orientează spre arenă.
    def _configure_entry(
        self,
        screen_width,
        screen_height,
    ):
        margin = self.body_length + 25

        if self.entry_direction == "left":
            self.x = float(-margin)
            self.y = float(
                random.randint(100, screen_height - 170)
            )
            self.angle = 0.0
        elif self.entry_direction == "right":
            self.x = float(screen_width + margin)
            self.y = float(
                random.randint(100, screen_height - 170)
            )
            self.angle = math.pi
        else:
            self.x = float(
                random.randint(55, screen_width - 55)
            )
            self.y = float(-margin)
            self.angle = math.pi / 2

    # Încarcă sprite-ul premium potrivit tipului și îl pregătește pentru joc.
    def _create_image(self):
        cache_key = (
            self.sprite_filename,
            self.render_size,
        )
        cached_image = self._sprite_cache.get(cache_key)
        if cached_image is not None:
            return cached_image

        image_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "images"
            / "missiles"
            / self.sprite_filename
        )

        if image_path.exists():
            try:
                missile_image = pygame.image.load(
                    str(image_path)
                ).convert_alpha()

                # Elimină spațiul transparent înainte de redimensionare.
                visible_bounds = missile_image.get_bounding_rect(
                    min_alpha=8
                )
                if (
                    visible_bounds.width > 0
                    and visible_bounds.height > 0
                ):
                    missile_image = missile_image.subsurface(
                        visible_bounds
                    ).copy()

                missile_image = pygame.transform.smoothscale(
                    missile_image,
                    self.render_size,
                )
                self._sprite_cache[cache_key] = missile_image
                return missile_image
            except pygame.error:
                # Dacă un PNG este deteriorat, jocul folosește varianta veche.
                pass

        missile_image = self._create_procedural_image()
        self._sprite_cache[cache_key] = missile_image
        return missile_image

    # Construiește vechiul desen procedural doar ca variantă de rezervă.
    def _create_procedural_image(self):
        surface_width = self.body_length + 18
        surface_height = self.body_height + 24
        missile_surface = pygame.Surface(
            (surface_width, surface_height),
            pygame.SRCALPHA,
        )
        center_y = surface_height // 2
        nose_x = surface_width - 4
        tail_x = 10
        body_top = center_y - self.body_height // 2
        body_bottom = center_y + self.body_height // 2

        pygame.draw.polygon(
            missile_surface,
            (70, 42, 82),
            [
                (tail_x, body_top),
                (surface_width - 18, body_top),
                (nose_x, center_y),
                (surface_width - 18, body_bottom),
                (tail_x, body_bottom),
            ],
        )
        pygame.draw.polygon(
            missile_surface,
            self.color,
            [
                (tail_x + 5, body_top),
                (surface_width - 20, body_top),
                (nose_x - 4, center_y),
                (surface_width - 20, center_y),
                (tail_x + 5, center_y),
            ],
        )
        pygame.draw.polygon(
            missile_surface,
            (115, 55, 135),
            [
                (tail_x + 12, body_top + 2),
                (tail_x - 2, 2),
                (tail_x + 27, body_top + 5),
            ],
        )
        pygame.draw.polygon(
            missile_surface,
            (115, 55, 135),
            [
                (tail_x + 12, body_bottom - 2),
                (tail_x - 2, surface_height - 2),
                (tail_x + 27, body_bottom - 5),
            ],
        )
        pygame.draw.circle(
            missile_surface,
            (255, 240, 250),
            (surface_width - 21, center_y),
            max(3, self.body_height // 5),
        )
        return missile_surface

    # Actualizează armarea, urmărirea, combustibilul și rotația imaginii.
    def update(
        self,
        player_rect,
        screen_width,
        screen_height,
    ):
        self.age += 1

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.arming_timer > 0:
            self.arming_timer -= 1
            movement_speed = 1.65
        else:
            movement_speed = self.speed
            self.fuel -= 1

            if self.tracking_enabled:
                desired_angle = math.atan2(
                    player_rect.centery - self.y,
                    player_rect.centerx - self.x,
                )
                angle_difference = (
                    desired_angle
                    - self.angle
                    + math.pi
                ) % math.tau - math.pi
                angle_difference = max(
                    -self.turn_rate,
                    min(self.turn_rate, angle_difference),
                )
                self.angle += angle_difference

        self.x += math.cos(self.angle) * movement_speed
        self.y += math.sin(self.angle) * movement_speed

        if self.age % 3 == 0:
            # Trail-ul pornește din motor, nu din centrul sprite-ului.
            trail_distance = self.render_size[0] * 0.46
            self.trail_points.append(
                [
                    self.x
                    - math.cos(self.angle) * trail_distance,
                    self.y
                    - math.sin(self.angle) * trail_distance,
                    18,
                ]
            )

        for trail_point in self.trail_points[:]:
            trail_point[2] -= 1

            if trail_point[2] <= 0:
                self.trail_points.remove(trail_point)

        if (
            0 <= self.x <= screen_width
            and 0 <= self.y <= screen_height
        ):
            self.has_entered_screen = True

        if self.fuel <= 0:
            self.expired = True

        rotation_degrees = -math.degrees(self.angle)
        rotated_image = pygame.transform.rotate(
            self.base_image,
            rotation_degrees,
        )

        if self.hit_flash_timer > 0:
            rotated_image = rotated_image.copy()
            rotated_image.fill(
                (150, 130, 150, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

        self.image = rotated_image
        self.rect = self.image.get_rect(
            center=(int(self.x), int(self.y))
        )
        self.collision_rect.center = self.rect.center

    # Oprește ghidajul și scurtează combustibilul la finalul evenimentului.
    def disable_tracking(self):
        if not self.tracking_enabled:
            return

        self.tracking_enabled = False
        self.fuel = min(self.fuel, 95)
        self.speed *= 1.18

    # Aplică damage și pornește flash-ul de impact.
    def take_damage(self):
        self.health -= 1
        self.hit_flash_timer = 8
        return self.health <= 0

    # Returnează True când racheta poate produce coliziuni.
    def is_dangerous(self):
        return self.arming_timer <= 0

    # Returnează True dacă s-a terminat combustibilul.
    def is_expired(self):
        return self.expired

    # Elimină rachetele care au ieșit după ce au intrat în arenă.
    def is_off_screen(self, screen_width, screen_height):
        if not self.has_entered_screen:
            return False

        margin = 100
        return (
            self.x < -margin
            or self.x > screen_width + margin
            or self.y < -margin
            or self.y > screen_height + margin
        )

    # Desenează traseul, linia de lock-on, racheta și viața grea.
    def draw(self, screen, player_rect):
        for trail_point in self.trail_points:
            life_ratio = trail_point[2] / 18
            trail_color = (
                int(self.color[0] * life_ratio * 0.75),
                int(self.color[1] * life_ratio * 0.45),
                int(self.color[2] * life_ratio * 0.75),
            )
            pygame.draw.circle(
                screen,
                trail_color,
                (
                    int(trail_point[0]),
                    int(trail_point[1]),
                ),
                max(1, int(5 * life_ratio)),
            )

            # Miezul luminos face evacuarea motorului mai clară pe fundal.
            core_color = (
                min(255, int(self.color[0] * life_ratio + 65)),
                min(255, int(self.color[1] * life_ratio + 45)),
                min(255, int(self.color[2] * life_ratio + 55)),
            )
            pygame.draw.circle(
                screen,
                core_color,
                (
                    int(trail_point[0]),
                    int(trail_point[1]),
                ),
                max(1, int(2 * life_ratio)),
            )

        if self.arming_timer > 0:
            if self.arming_timer // 6 % 2 == 0:
                pygame.draw.line(
                    screen,
                    (170, 35, 70),
                    self.rect.center,
                    player_rect.center,
                    1,
                )
            pygame.draw.circle(
                screen,
                (255, 55, 95),
                player_rect.center,
                24 + self.arming_timer // 3,
                2,
            )

        screen.blit(self.image, self.rect)

        if self.maximum_health <= 1:
            return

        bar_width = 54
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.bottom + 4
        pygame.draw.rect(
            screen,
            (45, 25, 35),
            (bar_x, bar_y, bar_width, 5),
            border_radius=2,
        )
        pygame.draw.rect(
            screen,
            self.color,
            (
                bar_x,
                bar_y,
                int(
                    bar_width
                    * self.health
                    / self.maximum_health
                ),
                5,
            ),
            border_radius=2,
        )
