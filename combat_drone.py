import math
import random

import pygame

from enemy_bullet import EnemyBullet


# Reprezintă o dronă mică, rapidă, care urmărește poziția jucătorului.
class CombatDrone:

    # Toate dronele roiului reutilizeaza acelasi sprite incarcat o singura data.
    _shared_base_image = None

    # Primește poziția de intrare și își configurează mișcarea.
    def __init__(self, start_x, start_y):
        self.x = float(start_x)
        self.y = float(start_y)
        # Sprite-ul este aproape dublu pentru ca textura sa ramana vizibila.
        # Hitbox-ul este putin mai mic decat imaginea, respectand forma navei.
        self.width = 78
        self.height = 68
        self.visual_width = 104
        self.visual_height = 100
        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )

        self.health = 1
        self.points = 12
        self.state = "hunting"
        self.velocity_x = random.uniform(-1.5, 1.5)
        self.velocity_y = random.uniform(1.0, 2.5)
        self.target_x = self.x
        self.target_y = 150.0
        self.target_timer = 0
        self.entry_timer = 50
        self.fire_timer = random.randint(70, 145)
        self.age = random.randint(0, 500)
        self.wobble_phase = random.uniform(
            0,
            math.tau,
        )
        self.hit_flash_timer = 0
        self.image = self._load_drone_image()

    # Incarca nava premium care inlocuieste vechiul poligon procedural.
    def _load_drone_image(self):
        if CombatDrone._shared_base_image is None:
            loaded_image = pygame.image.load(
                "assets/images/enemies/"
                "swarm_hunter_drone.png"
            ).convert_alpha()
            CombatDrone._shared_base_image = (
                pygame.transform.smoothscale(
                    loaded_image,
                    (
                        self.visual_width,
                        self.visual_height,
                    ),
                )
            )

        return CombatDrone._shared_base_image

    # Actualizează urmărirea sau retragerea dronei.
    def update(
        self,
        player_rect,
        screen_width,
        screen_height,
    ):
        self.age += 1

        if self.entry_timer > 0:
            self.entry_timer -= 1

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.state == "departing":
            self.x += self.velocity_x
            self.y -= 8.5
            self.rect.topleft = (
                int(self.x),
                int(self.y),
            )
            return

        self.target_timer -= 1

        if self.target_timer <= 0:
            self._choose_target(
                player_rect,
                screen_width,
                screen_height,
            )

        distance_x = self.target_x - self.x
        distance_y = self.target_y - self.y
        distance = max(
            1.0,
            math.hypot(distance_x, distance_y),
        )
        movement_speed = 4.4
        desired_velocity_x = (
            distance_x / distance
        ) * movement_speed
        desired_velocity_y = (
            distance_y / distance
        ) * movement_speed

        # Steering-ul face virajele line, iar oscilația creează efectul de roi.
        self.velocity_x += (
            desired_velocity_x - self.velocity_x
        ) * 0.11
        self.velocity_y += (
            desired_velocity_y - self.velocity_y
        ) * 0.11
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.x += math.sin(
            self.age * 0.09 + self.wobble_phase
        ) * 0.55

        self._keep_inside_arena(
            screen_width,
            screen_height,
        )
        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    # Alege o poziție nouă în apropierea jucătorului, dar deasupra lui.
    def _choose_target(
        self,
        player_rect,
        screen_width,
        screen_height,
    ):
        desired_x = (
            player_rect.centerx
            + random.randint(-300, 300)
            - self.width // 2
        )
        desired_y = (
            player_rect.centery
            + random.randint(-330, -125)
        )

        self.target_x = float(
            max(
                20,
                min(
                    screen_width - self.width - 20,
                    desired_x,
                ),
            )
        )
        self.target_y = float(
            max(
                65,
                min(
                    screen_height - 235,
                    desired_y,
                ),
            )
        )
        self.target_timer = random.randint(45, 90)

    # Împiedică dronele să iasă din arenă în timpul atacului.
    def _keep_inside_arena(
        self,
        screen_width,
        screen_height,
    ):
        # În primele cadre permitem intrarea naturală din afara ecranului.
        if self.entry_timer > 0:
            return

        maximum_x = screen_width - self.width
        maximum_y = screen_height - 205

        if self.x < 0:
            self.x = 0.0
            self.velocity_x = abs(self.velocity_x)
        elif self.x > maximum_x:
            self.x = float(maximum_x)
            self.velocity_x = -abs(self.velocity_x)

        if self.y < 40:
            self.y = 40.0
            self.velocity_y = abs(self.velocity_y)
        elif self.y > maximum_y:
            self.y = float(maximum_y)
            self.velocity_y = -abs(self.velocity_y)

    # Creează periodic un proiectil orientat spre poziția curentă a navei.
    def try_shoot(self, player_rect):
        if self.state != "hunting":
            return None

        self.fire_timer -= 1

        if (
            self.fire_timer > 0
            or self.rect.centery >= player_rect.centery
        ):
            return None

        distance_x = (
            player_rect.centerx - self.rect.centerx
        )
        distance_y = (
            player_rect.centery - self.rect.bottom
        )
        distance = max(
            1.0,
            math.hypot(distance_x, distance_y),
        )
        projectile_speed = 4.6
        speed_x = (
            distance_x / distance
        ) * projectile_speed
        speed_y = max(
            2.5,
            (distance_y / distance)
            * projectile_speed,
        )
        self.fire_timer = random.randint(105, 170)

        return EnemyBullet(
            self.rect.centerx - 3,
            self.rect.bottom,
            speed_x,
            speed_y,
        )

    # Pornește retragerea dronei spre partea superioară a ecranului.
    def start_departure(self):
        if self.state == "hunting":
            self.state = "departing"
            self.velocity_x = random.uniform(-2.0, 2.0)

    # Aplică o lovitură primită de la jucător.
    def take_damage(self):
        self.health -= 1
        self.hit_flash_timer = 8

    # Returnează True când drona a fost distrusă.
    def is_dead(self):
        return self.health <= 0

    # Returnează True după ce drona retrasă a părăsit ecranul.
    def has_departed(self):
        return (
            self.state == "departing"
            and self.y < -self.height - 20
        )

    # Deseneaza sprite-ul premium si pastreaza efectul energetic al roiului.
    def draw(self, screen):
        center_x = self.rect.centerx
        center_y = self.rect.centery

        glow_surface = pygame.Surface(
            (76, 72),
            pygame.SRCALPHA,
        )
        glow_center = (
            glow_surface.get_width() // 2,
            glow_surface.get_height() // 2,
        )
        pygame.draw.circle(
            glow_surface,
            (75, 155, 255, 38),
            glow_center,
            27,
        )
        screen.blit(
            glow_surface,
            (
                center_x - glow_center[0],
                center_y - glow_center[1],
            ),
        )

        draw_image = self.image.copy()
        if self.hit_flash_timer > 0:
            draw_image.fill(
                (125, 125, 125, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

        screen.blit(
            draw_image,
            (
                int(
                    self.x
                    - (self.visual_width - self.width) / 2
                ),
                int(
                    self.y
                    - (self.visual_height - self.height) / 2
                ),
            ),
        )

        core_radius = 2 + int(
            abs(math.sin(self.age * 0.13)) * 2
        )
        pygame.draw.circle(
            screen,
            (110, 225, 255),
            (center_x, center_y + 6),
            core_radius,
        )
        pygame.draw.circle(
            screen,
            (235, 250, 255),
            (center_x, center_y + 6),
            2,
        )

        # Punctul luminos pastreaza nucleul vizibil chiar intr-un roi numeros.
