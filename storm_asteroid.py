import math
import random
from pathlib import Path

import pygame


# Asteroid folosit exclusiv de evenimentul Asteroid Storm.
class StormAsteroid:

    # Imaginile originale sunt încărcate o singură dată și apoi refolosite.
    # Astfel, jocul nu citește din nou fișierele pentru fiecare asteroid creat.
    _source_images = {}

    _image_files = {
        "small": "asteroid_realistic_small.png",
        "medium": "asteroid_realistic_medium.png",
        "large": "asteroid_realistic_large.png",
    }

    # Configurează mărimea, direcția, viteza și rezistența asteroidului.
    def __init__(
        self,
        screen_width,
        screen_height,
        size_type,
        entry_direction,
        wave,
    ):
        self.size_type = size_type
        self.entry_direction = entry_direction

        if size_type == "small":
            self.radius = random.randint(19, 27)
            self.health = 1
            self.points = 18
            base_speed = random.uniform(6.2, 7.8)
        elif size_type == "large":
            self.radius = random.randint(48, 61)
            self.health = 4
            self.points = 65
            base_speed = random.uniform(3.1, 4.0)
        else:
            self.radius = random.randint(32, 43)
            self.health = 2
            self.points = 35
            base_speed = random.uniform(4.4, 5.5)

        self.maximum_health = self.health
        speed_bonus = min(
            1.3,
            max(1, int(wave)) * 0.07,
        )
        self.speed = base_speed + speed_bonus
        self.x = 0.0
        self.y = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self._configure_entry(
            screen_width,
            screen_height,
        )

        # Rotația lentă face roca să pară grea, nu ca un obiect care se învârte
        # artificial. Evităm și vitezele foarte apropiate de zero.
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-1.15, 1.15)
        if -0.25 < self.rotation_speed < 0.25:
            self.rotation_speed = random.choice((-0.25, 0.25))

        self.hit_flash_timer = 0
        self.departing = False

        self.base_image = self._create_image()
        self.image = self.base_image
        self.rect = self.image.get_rect(
            center=(int(self.x), int(self.y))
        )

        # Coliziunea este mai mică decât imaginea. Jucătorul nu este lovit
        # dacă atinge doar un colț exterior al asteroidului.
        self.collision_rect = pygame.Rect(
            0,
            0,
            int(self.radius * 1.45),
            int(self.radius * 1.45),
        )
        self.collision_rect.center = self.rect.center

    # Așază asteroidul în afara ecranului și îi setează vectorul de zbor.
    def _configure_entry(
        self,
        screen_width,
        screen_height,
    ):
        margin = self.radius * 2 + 12

        if self.entry_direction == "left":
            self.x = float(-margin)
            self.y = float(
                random.randint(120, screen_height - 105)
            )
            self.velocity_x = self.speed
            self.velocity_y = random.uniform(-0.7, 1.15)

        elif self.entry_direction == "right":
            self.x = float(screen_width + margin)
            self.y = float(
                random.randint(120, screen_height - 105)
            )
            self.velocity_x = -self.speed
            self.velocity_y = random.uniform(-0.7, 1.15)

        elif self.entry_direction == "diagonal_left":
            self.x = float(
                random.randint(-margin, screen_width // 3)
            )
            self.y = float(-margin)
            self.velocity_x = self.speed * 0.72
            self.velocity_y = self.speed

        elif self.entry_direction == "diagonal_right":
            self.x = float(
                random.randint(
                    screen_width * 2 // 3,
                    screen_width + margin,
                )
            )
            self.y = float(-margin)
            self.velocity_x = -self.speed * 0.72
            self.velocity_y = self.speed

        else:
            self.x = float(
                random.randint(20, screen_width - 20)
            )
            self.y = float(-margin)
            self.velocity_x = random.uniform(-1.1, 1.1)
            self.velocity_y = self.speed

    # Încarcă imaginea realistă corespunzătoare mărimii asteroidului.
    @classmethod
    def _load_source_image(cls, size_type):
        image_key = (
            size_type
            if size_type in cls._image_files
            else "medium"
        )

        if image_key in cls._source_images:
            return cls._source_images[image_key]

        image_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "images"
            / "asteroids"
            / cls._image_files[image_key]
        )

        source_image = pygame.image.load(
            str(image_path)
        ).convert_alpha()

        # Elimină spațiul transparent mare din jurul imaginii generate.
        # Astfel, dimensiunea setată mai jos reprezintă roca propriu-zisă.
        visible_bounds = source_image.get_bounding_rect(
            min_alpha=8
        )
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            source_image = source_image.subsurface(
                visible_bounds
            ).copy()

        cls._source_images[image_key] = source_image
        return source_image

    # Pregătește sprite-ul realist la dimensiunea asteroidului curent.
    # Dacă imaginile lipsesc, jocul folosește automat desenul simplu de rezervă.
    def _create_image(self):
        try:
            source_image = self._load_source_image(
                self.size_type
            )

            visual_size = self.radius * 2 + 6
            source_width = source_image.get_width()
            source_height = source_image.get_height()
            scale = visual_size / max(
                source_width,
                source_height,
            )
            target_size = (
                max(1, int(source_width * scale)),
                max(1, int(source_height * scale)),
            )

            return pygame.transform.smoothscale(
                source_image,
                target_size,
            )
        except (FileNotFoundError, pygame.error):
            return self._create_fallback_image()

    # Desen simplu de rezervă, folosit numai dacă un PNG nu a fost copiat.
    def _create_fallback_image(self):
        surface_size = self.radius * 2 + 18
        asteroid_surface = pygame.Surface(
            (surface_size, surface_size),
            pygame.SRCALPHA,
        )
        center = surface_size // 2
        asteroid_points = []
        point_count = random.randint(9, 13)

        for point_index in range(point_count):
            point_angle = (
                point_index / point_count
            ) * math.tau
            point_radius = self.radius * random.uniform(
                0.72,
                1.0,
            )
            asteroid_points.append(
                (
                    center
                    + math.cos(point_angle) * point_radius,
                    center
                    + math.sin(point_angle) * point_radius,
                )
            )

        pygame.draw.polygon(
            asteroid_surface,
            (72, 66, 82),
            asteroid_points,
        )
        pygame.draw.polygon(
            asteroid_surface,
            (150, 135, 125),
            asteroid_points,
            3,
        )

        for _ in range(random.randint(3, 6)):
            crater_radius = random.randint(
                max(3, self.radius // 10),
                max(5, self.radius // 4),
            )
            crater_center = (
                center
                + random.randint(
                    -self.radius // 2,
                    self.radius // 2,
                ),
                center
                + random.randint(
                    -self.radius // 2,
                    self.radius // 2,
                ),
            )
            pygame.draw.circle(
                asteroid_surface,
                (38, 36, 40),
                crater_center,
                crater_radius,
            )

        return asteroid_surface

    # Deplasează, rotește și actualizează dreptunghiurile asteroidului.
    def update(self):
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        self.x += self.velocity_x
        self.y += self.velocity_y
        self.angle = (
            self.angle + self.rotation_speed
        ) % 360
        self.image = pygame.transform.rotate(
            self.base_image,
            self.angle,
        )
        self.rect = self.image.get_rect(
            center=(int(self.x), int(self.y))
        )
        self.collision_rect.center = self.rect.center

    # Accelerează asteroidul o singură dată la finalul evenimentului.
    def start_departure(self):
        if self.departing:
            return

        self.departing = True
        self.velocity_x *= 1.8
        self.velocity_y *= 1.8

    # Scade rezistența și pornește flash-ul de impact.
    def take_damage(self):
        self.health -= 1
        self.hit_flash_timer = 8
        self.velocity_x += random.uniform(-0.35, 0.35)
        self.velocity_y += random.uniform(-0.2, 0.2)
        return self.health <= 0

    # Returnează True după ce asteroidul a ieșit complet din arenă.
    def is_off_screen(self, screen_width, screen_height):
        margin = self.radius * 3 + 40
        return (
            self.x < -margin
            or self.x > screen_width + margin
            or self.y < -margin
            or self.y > screen_height + margin
        )

    # Desenează asteroidul și marcajele rezistenței sale.
    def draw(self, screen):
        if self.hit_flash_timer > 0:
            asteroid_image = self.image.copy()
            asteroid_image.fill(
                (105, 75, 40, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
        else:
            asteroid_image = self.image

        screen.blit(asteroid_image, self.rect)

        if self.maximum_health <= 1:
            return

        pip_width = 8
        total_width = (
            self.maximum_health * pip_width
            + (self.maximum_health - 1) * 3
        )
        pip_x = self.rect.centerx - total_width // 2
        pip_y = self.rect.bottom + 4

        for pip_index in range(self.maximum_health):
            pip_color = (
                (235, 165, 85)
                if pip_index < self.health
                else (55, 48, 45)
            )
            pygame.draw.rect(
                screen,
                pip_color,
                (
                    pip_x + pip_index * 11,
                    pip_y,
                    pip_width,
                    3,
                ),
            )
