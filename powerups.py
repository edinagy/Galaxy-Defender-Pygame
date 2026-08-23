import math
import random
from pathlib import Path

import pygame


# Culorile sunt folosite atât de obiect, cât și de efectul de colectare.
POWERUP_COLORS = {
    "weapon_upgrade": (150, 70, 255),
    "double_shot": (150, 70, 255),
    "shield": (45, 195, 255),
    "life": (255, 65, 55),
}


class PowerUp:
    # Sprite-urile se încarcă o singură dată, nu pentru fiecare obiect nou.
    _sprite_cache = {}

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 36
        self.height = 36
        self.speed = 3

        # Faza diferită împiedică obiectele să pulseze toate simultan.
        self.animation_time = random.uniform(0.0, math.tau)
        self.rotation_angle = random.uniform(0.0, 360.0)
        self.rotation_speed = random.choice((-0.85, 0.85))

        # Alege tipul power-up-ului cu rarități diferite.
        # Upgrade-ul de armă este intenționat rar, fiind cel mai puternic.
        roll = random.randint(1, 100)
        if roll <= 3:
            self.powerup_type = "weapon_upgrade"
        elif roll <= 10:
            self.powerup_type = "shield"
        elif roll <= 12:
            self.powerup_type = "life"
        else:
            self.powerup_type = None

        # Coliziunea rămâne exact 36x36, ca în versiunea anterioară.
        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )

    # Coboară obiectul și adaugă o plutire laterală discretă.
    def move(self):
        self.animation_time += 0.075
        self.rotation_angle = (
            self.rotation_angle + self.rotation_speed
        ) % 360.0
        self.y += self.speed

        sway = math.sin(self.animation_time) * 4.5
        self.rect.topleft = (
            int(self.x + sway),
            int(self.y),
        )

    # Returnează sprite-ul potrivit chiar dacă tipul a fost schimbat ulterior
    # de recompensa garantată a inamicului elită.
    @classmethod
    def _get_sprite(cls, powerup_type):
        if powerup_type == "double_shot":
            powerup_type = "weapon_upgrade"

        if powerup_type in cls._sprite_cache:
            return cls._sprite_cache[powerup_type]

        filename_by_type = {
            "weapon_upgrade": "powerup_weapon_upgrade_v2.png",
            "shield": "powerup_shield_v2.png",
            "life": "powerup_life_v2.png",
        }
        filename = filename_by_type.get(powerup_type)
        if filename is None:
            return None

        image_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "images"
            / "powerups"
            / filename
        )
        if not image_path.exists():
            cls._sprite_cache[powerup_type] = None
            return None

        loaded_image = pygame.image.load(
            str(image_path)
        ).convert_alpha()
        visible_bounds = loaded_image.get_bounding_rect(min_alpha=8)
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            loaded_image = loaded_image.subsurface(
                visible_bounds
            ).copy()

        # Toate obiectele intră într-o zonă vizuală de 54x54 fără
        # să fie deformate; dreptunghiul de coliziune rămâne separat.
        target_size = 54
        scale = min(
            target_size / loaded_image.get_width(),
            target_size / loaded_image.get_height(),
        )
        scaled_size = (
            max(1, int(loaded_image.get_width() * scale)),
            max(1, int(loaded_image.get_height() * scale)),
        )
        cls._sprite_cache[powerup_type] = pygame.transform.smoothscale(
            loaded_image,
            scaled_size,
        )
        return cls._sprite_cache[powerup_type]

    def draw(self, screen):
        if self.powerup_type is None:
            return

        center = self.rect.center
        color = POWERUP_COLORS.get(
            self.powerup_type,
            (110, 210, 255),
        )
        pulse = 0.5 + 0.5 * math.sin(self.animation_time * 2.2)

        self._draw_glow(
            screen,
            center,
            color,
            int(29 + pulse * 7),
        )

        # Trei particule mici orbitează obiectul și accentuează rotația.
        for mote_index in range(3):
            angle = (
                self.animation_time * 1.7
                + mote_index * math.tau / 3
            )
            radius = 28 + mote_index * 2
            mote_position = (
                int(center[0] + math.cos(angle) * radius),
                int(center[1] + math.sin(angle) * radius * 0.58),
            )
            pygame.draw.circle(
                screen,
                color,
                mote_position,
                2 if mote_index else 3,
            )

        sprite = self._get_sprite(self.powerup_type)
        if sprite is None:
            self._draw_fallback(screen, center, color)
            return

        display_scale = 0.96 + pulse * 0.07
        animated_sprite = pygame.transform.rotozoom(
            sprite,
            self.rotation_angle,
            display_scale,
        )
        screen.blit(
            animated_sprite,
            animated_sprite.get_rect(center=center),
        )

    # Glow-ul este o lumină, nu forma obiectului, de aceea rămâne rotund.
    @staticmethod
    def _draw_glow(screen, center, color, radius):
        glow_radius = radius * 2
        glow_surface = pygame.Surface(
            (glow_radius * 2 + 2, glow_radius * 2 + 2),
            pygame.SRCALPHA,
        )
        glow_center = glow_surface.get_rect().center
        for radius_scale, intensity in (
            (1.0, 0.045),
            (0.72, 0.075),
            (0.46, 0.13),
        ):
            pygame.draw.circle(
                glow_surface,
                (
                    int(color[0] * intensity),
                    int(color[1] * intensity),
                    int(color[2] * intensity),
                ),
                glow_center,
                max(1, int(glow_radius * radius_scale)),
            )

        screen.blit(
            glow_surface,
            (
                center[0] - glow_center[0],
                center[1] - glow_center[1],
            ),
            special_flags=pygame.BLEND_RGB_ADD,
        )

    # Rezervă vizuală simplă dacă un sprite nu a fost copiat.
    def _draw_fallback(self, screen, center, color):
        if self.powerup_type == "shield":
            points = [
                (center[0], center[1] - 18),
                (center[0] + 16, center[1] - 8),
                (center[0] + 13, center[1] + 12),
                (center[0], center[1] + 20),
                (center[0] - 13, center[1] + 12),
                (center[0] - 16, center[1] - 8),
            ]
            pygame.draw.polygon(screen, color, points, 4)
        elif self.powerup_type == "life":
            pygame.draw.line(
                screen, color,
                (center[0] - 15, center[1]),
                (center[0] + 15, center[1]),
                7,
            )
            pygame.draw.line(
                screen, color,
                (center[0], center[1] - 15),
                (center[0], center[1] + 15),
                7,
            )
        else:
            points = [
                (center[0], center[1] - 20),
                (center[0] + 18, center[1]),
                (center[0], center[1] + 20),
                (center[0] - 18, center[1]),
            ]
            pygame.draw.polygon(screen, color, points, 4)


# Efectul apare în locul obiectului colectat și se strânge rapid în navă.
class PowerUpCollectEffect:

    def __init__(self, x, y, powerup_type):
        self.x = float(x)
        self.y = float(y)
        self.powerup_type = powerup_type
        self.color = POWERUP_COLORS.get(
            powerup_type,
            (110, 210, 255),
        )
        self.age = 0
        self.duration = 28
        self.finished = False
        self.motes = []

        for mote_index in range(14):
            self.motes.append(
                {
                    "angle": mote_index * math.tau / 14,
                    "radius": random.uniform(30.0, 54.0),
                    "spin": random.uniform(0.12, 0.22),
                    "size": random.randint(2, 4),
                }
            )

    def update(self):
        self.age += 1
        if self.age >= self.duration:
            self.finished = True

    def draw(self, screen):
        progress = min(1.0, self.age / self.duration)
        remaining = 1.0 - progress

        # Inelul se contractă spre centrul navei.
        ring_radius = max(2, int(48 * remaining))
        ring_color = (
            int(self.color[0] * remaining),
            int(self.color[1] * remaining),
            int(self.color[2] * remaining),
        )
        pygame.draw.circle(
            screen,
            ring_color,
            (int(self.x), int(self.y)),
            ring_radius,
            max(1, int(3 * remaining)),
        )

        for mote in self.motes:
            angle = mote["angle"] + self.age * mote["spin"]
            radius = mote["radius"] * remaining
            position = (
                int(self.x + math.cos(angle) * radius),
                int(self.y + math.sin(angle) * radius),
            )
            pygame.draw.circle(
                screen,
                ring_color,
                position,
                max(1, int(mote["size"] * remaining)),
            )

        # Ultimele frame-uri produc un flash mic în centrul navei.
        if progress > 0.58:
            flash = (progress - 0.58) / 0.42
            pygame.draw.circle(
                screen,
                self.color,
                (int(self.x), int(self.y)),
                max(2, int(10 * flash)),
                2,
            )
