import math
import random

import pygame


# Proiectil special lansat de turelele Crossfire Protocol.
class CrossfireBullet:

    # Creează proiectilul cu direcție, viteză și culoare proprie.
    def __init__(
        self,
        start_x,
        start_y,
        speed_x,
        speed_y,
        color,
        radius=6,
    ):
        self.x = float(start_x)
        self.y = float(start_y)
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)
        self.color = color
        self.radius = radius
        self.rect = pygame.Rect(
            int(self.x - radius),
            int(self.y - radius),
            radius * 2,
            radius * 2,
        )

    # Deplasează proiectilul și actualizează hitbox-ul.
    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.center = (
            int(self.x),
            int(self.y),
        )

    # Returnează True după ieșirea completă din arenă.
    def is_off_screen(self, screen_width, screen_height):
        margin = 35
        return (
            self.x < -margin
            or self.x > screen_width + margin
            or self.y < -margin
            or self.y > screen_height + margin
        )

    # Desenează proiectilul cu glow și miez luminos.
    def draw(self, screen):
        pygame.draw.circle(
            screen,
            (
                max(0, self.color[0] // 3),
                max(0, self.color[1] // 3),
                max(0, self.color[2] // 3),
            ),
            self.rect.center,
            self.radius + 6,
        )
        pygame.draw.circle(
            screen,
            self.color,
            self.rect.center,
            self.radius,
        )
        pygame.draw.circle(
            screen,
            (255, 245, 255),
            self.rect.center,
            max(2, self.radius // 2),
        )


# Navă-turelă care patrulează, trage și poate fi distrusă.
class CrossfireTurret:

    # Sprite-ul este incarcat o singura data si reutilizat de toate cele 4 drone.
    _shared_base_image = None

    # Configurează poziția, indicativul și decalajul atacurilor.
    def __init__(
        self,
        target_center_x,
        target_y,
        screen_width,
        callsign,
        turret_index,
    ):
        self.width = 132
        self.height = 132
        self.home_x = float(
            target_center_x - self.width // 2
        )
        self.home_y = float(target_y)
        self.x = self.home_x
        self.y = float(-self.height - 45)
        self.screen_width = screen_width
        self.callsign = callsign
        self.turret_index = turret_index
        self.health = 8
        self.maximum_health = 8
        self.state = "entering"
        self.age = turret_index * 55
        self.patrol_phase = turret_index * 1.35
        self.fire_timer = 45 + turret_index * 18
        self.hit_flash_timer = 0
        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )
        self.image = self._load_drone_image()

    # Inlocuieste vechile forme geometrice cu o nava Crossfire adevarata.
    def _load_drone_image(self):
        if CrossfireTurret._shared_base_image is None:
            loaded_image = pygame.image.load(
                "assets/images/enemies/"
                "crossfire_assault_drone.png"
            ).convert_alpha()
            CrossfireTurret._shared_base_image = (
                pygame.transform.smoothscale(
                    loaded_image,
                    (self.width, self.height),
                )
            )

        return CrossfireTurret._shared_base_image

    # Actualizează intrarea, patrularea sau retragerea turelei.
    def update(self):
        self.age += 1

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.state == "entering":
            self.y += (
                self.home_y - self.y
            ) * 0.072

            if abs(self.home_y - self.y) < 3:
                self.y = self.home_y
                self.state = "fighting"

        elif self.state == "fighting":
            horizontal_range = (
                36 if self.turret_index in (0, 3) else 48
            )
            self.x = (
                self.home_x
                + math.sin(
                    self.age * 0.018
                    + self.patrol_phase
                )
                * horizontal_range
            )
            self.y = (
                self.home_y
                + math.sin(
                    self.age * 0.026
                    + self.patrol_phase
                )
                * 16
            )

        elif self.state == "departing":
            self.y -= 7.5

        self.x = max(
            5.0,
            min(
                self.screen_width - self.width - 5,
                self.x,
            ),
        )
        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    # Selectează atacul corespunzător fazei curente.
    def try_shoot(self, player_rect, phase):
        if self.state != "fighting":
            return []

        self.fire_timer -= 1

        if self.fire_timer > 0:
            return []

        if phase == 1:
            bullets = self._create_aimed_fan(
                player_rect,
                bullet_count=3,
                spread=0.16,
                speed=4.5,
            )
            self.fire_timer = 92 + self.turret_index * 7

        elif phase == 2:
            bullets = self._create_pincer_burst(
                player_rect
            )
            self.fire_timer = 65 + self.turret_index * 5

        else:
            bullets = self._create_downward_arc(
                bullet_count=5,
                speed=5.0,
            )
            self.fire_timer = 82 + self.turret_index * 4

        return bullets

    # Creează o rafală în evantai orientată spre jucător.
    def _create_aimed_fan(
        self,
        player_rect,
        bullet_count,
        spread,
        speed,
    ):
        base_angle = math.atan2(
            player_rect.centery - self.rect.bottom,
            player_rect.centerx - self.rect.centerx,
        )
        bullets = []
        middle_index = (bullet_count - 1) / 2

        for bullet_index in range(bullet_count):
            bullet_angle = (
                base_angle
                + (bullet_index - middle_index) * spread
            )
            bullets.append(
                CrossfireBullet(
                    self.rect.centerx,
                    self.rect.bottom,
                    math.cos(bullet_angle) * speed,
                    math.sin(bullet_angle) * speed,
                    (255, 70, 145),
                )
            )

        return bullets

    # Creează două proiectile directe și unul care anticipează mișcarea.
    def _create_pincer_burst(self, player_rect):
        target_offsets = (-55, 0, 55)
        bullets = []

        for target_offset in target_offsets:
            distance_x = (
                player_rect.centerx
                + target_offset
                - self.rect.centerx
            )
            distance_y = (
                player_rect.centery
                - self.rect.bottom
            )
            distance = max(
                1.0,
                math.hypot(distance_x, distance_y),
            )
            bullets.append(
                CrossfireBullet(
                    self.rect.centerx,
                    self.rect.bottom,
                    distance_x / distance * 5.15,
                    distance_y / distance * 5.15,
                    (255, 120, 65),
                    radius=5,
                )
            )

        return bullets

    # Creează un arc descendent pentru faza finală.
    def _create_downward_arc(self, bullet_count, speed):
        bullets = []
        middle_index = (bullet_count - 1) / 2

        for bullet_index in range(bullet_count):
            horizontal_factor = (
                bullet_index - middle_index
            ) * 0.34
            vertical_factor = math.sqrt(
                max(0.20, 1.0 - horizontal_factor ** 2)
            )
            bullets.append(
                CrossfireBullet(
                    self.rect.centerx,
                    self.rect.bottom,
                    horizontal_factor * speed,
                    vertical_factor * speed,
                    (205, 80, 255),
                    radius=6,
                )
            )

        return bullets

    # Salva de final combină un evantai lat cu un arc rapid.
    def create_final_salvo(self, player_rect):
        if self.state not in (
            "fighting",
            "entering",
        ):
            return []

        bullets = self._create_aimed_fan(
            player_rect,
            bullet_count=5,
            spread=0.22,
            speed=5.5,
        )
        bullets.extend(
            self._create_downward_arc(
                bullet_count=7,
                speed=5.25,
            )
        )
        return bullets

    # Pornește retragerea prin partea superioară.
    def start_departure(self):
        if self.state != "destroyed":
            self.state = "departing"

    # Scade viața și pornește flash-ul vizual.
    def take_damage(self):
        self.health -= 1
        self.hit_flash_timer = 9

        if self.health <= 0:
            self.state = "destroyed"

    # Returnează True dacă turela nu mai are viață.
    def is_destroyed(self):
        return self.state == "destroyed"

    # Returnează True după ieșirea completă din ecran.
    def has_departed(self):
        return (
            self.state == "departing"
            and self.y < -self.height - 25
        )

    # Deseneaza drona de asalt, nucleul armei si bara sa de viata.
    def draw(self, screen, small_font):
        if self.state == "destroyed":
            return

        draw_image = self.image.copy()
        if self.hit_flash_timer > 0:
            draw_image.fill(
                (135, 95, 135, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

        screen.blit(
            draw_image,
            (int(self.x), int(self.y)),
        )

        # Pulsul de sub tun confirma vizual momentul in care drona este activa.
        if self.state == "fighting":
            pulse_radius = 4 + int(
                2 * abs(math.sin(self.age * 0.10))
            )
            pygame.draw.circle(
                screen,
                (255, 65, 155),
                (self.rect.centerx, self.rect.bottom - 8),
                pulse_radius,
            )
            pygame.draw.circle(
                screen,
                (255, 225, 245),
                (self.rect.centerx, self.rect.bottom - 8),
                2,
            )

        health_ratio = max(
            0.0,
            self.health / self.maximum_health,
        )
        bar_width = 96
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.bottom + 5
        pygame.draw.rect(
            screen,
            (35, 20, 45),
            (bar_x, bar_y, bar_width, 6),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (235, 70, 160),
            (
                bar_x,
                bar_y,
                int(bar_width * health_ratio),
                6,
            ),
            border_radius=3,
        )
        callsign_surface = small_font.render(
            self.callsign,
            True,
            (235, 185, 230),
        )
        screen.blit(
            callsign_surface,
            (
                self.rect.centerx
                - callsign_surface.get_width() // 2,
                bar_y + 10,
            ),
        )
