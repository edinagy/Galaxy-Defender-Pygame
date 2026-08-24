import math

import pygame


# Proiectilul navei jucătorului. Hitbox-ul, viteza și damage-ul rămân
# independente de efectele vizuale mai late desenate în jurul lui.
class Bullet:

    LEVEL_COLORS = {
        1: ((0, 90, 235), (0, 215, 255), (240, 255, 255)),
        2: ((0, 145, 185), (35, 255, 215), (245, 255, 255)),
        3: ((100, 35, 220), (205, 75, 255), (255, 235, 255)),
        4: ((215, 65, 5), (255, 190, 35), (255, 255, 220)),
    }

    def __init__(
        self,
        center_x,
        y,
        velocity_x=0.0,
        velocity_y=-12.0,
        damage=1,
        weapon_level=1,
        heavy=False,
    ):
        self.weapon_level = max(1, min(4, int(weapon_level)))
        self.damage = max(1, int(damage))
        self.heavy = bool(heavy)

        if self.heavy:
            self.width = 12
            self.height = 34
        elif self.weapon_level >= 3:
            self.width = 7
            self.height = 27
        else:
            self.width = 6
            self.height = 25

        self.x = float(center_x - self.width / 2)
        self.y = float(y)
        self.velocity_x = float(velocity_x)
        self.velocity_y = float(velocity_y)
        self.speed = abs(self.velocity_y)
        self.animation_timer = 0
        self.trail_points = []

        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )

    # Memorează ultimele poziții pentru o coadă luminoasă scurtă.
    def move(self):
        self.animation_timer += 1
        self.trail_points.append(self.rect.center)
        maximum_trail = 8 if self.heavy else 6
        if len(self.trail_points) > maximum_trail:
            self.trail_points.pop(0)

        self.x += self.velocity_x
        self.y += self.velocity_y
        self.rect.topleft = (int(self.x), int(self.y))

    # Desenează un bolt orientat după direcția reală de deplasare.
    def draw(self, screen):
        glow_color, laser_color, core_color = self.LEVEL_COLORS[
            self.weapon_level
        ]
        direction_length = max(
            0.001,
            math.hypot(self.velocity_x, self.velocity_y),
        )
        direction_x = self.velocity_x / direction_length
        direction_y = self.velocity_y / direction_length
        perpendicular_x = -direction_y
        perpendicular_y = direction_x
        center_x, center_y = self.rect.center

        # Segmentele vechi se sting spre capătul cozii.
        if len(self.trail_points) >= 2:
            for point_index in range(1, len(self.trail_points)):
                fade = point_index / len(self.trail_points)
                pygame.draw.line(
                    screen,
                    self._fade_color(glow_color, fade * 0.48),
                    self.trail_points[point_index - 1],
                    self.trail_points[point_index],
                    max(1, int((7 if self.heavy else 4) * fade)),
                )

        half_length = self.height * 0.58
        tip = (
            int(center_x + direction_x * half_length),
            int(center_y + direction_y * half_length),
        )
        tail = (
            int(center_x - direction_x * half_length),
            int(center_y - direction_y * half_length),
        )

        outer_width = 18 if self.heavy else 11
        energy_width = 10 if self.heavy else 6
        core_width = 4 if self.heavy else 2
        pygame.draw.line(
            screen,
            self._fade_color(glow_color, 0.48),
            tail,
            tip,
            outer_width,
        )
        pygame.draw.line(
            screen,
            laser_color,
            tail,
            tip,
            energy_width,
        )
        pygame.draw.line(
            screen,
            core_color,
            tail,
            tip,
            core_width,
        )
        pygame.draw.circle(
            screen,
            core_color,
            tip,
            6 if self.heavy else 3,
        )

        # Lancea de nivel 4 are stabilizatoare energetice laterale.
        if self.heavy:
            wing_distance = 8
            wing_length = 10
            for side in (-1, 1):
                wing_center = (
                    center_x + perpendicular_x * wing_distance * side,
                    center_y + perpendicular_y * wing_distance * side,
                )
                wing_start = (
                    int(wing_center[0] - direction_x * wing_length),
                    int(wing_center[1] - direction_y * wing_length),
                )
                wing_end = (
                    int(wing_center[0] + direction_x * 4),
                    int(wing_center[1] + direction_y * 4),
                )
                pygame.draw.line(
                    screen,
                    laser_color,
                    wing_start,
                    wing_end,
                    3,
                )

        # Primele cadre includ flash-ul de la gura tunului.
        if self.animation_timer < 4:
            flash_fade = 1.0 - self.animation_timer / 4
            flash_radius = int((12 if self.heavy else 8) * flash_fade)
            pygame.draw.circle(
                screen,
                self._fade_color(laser_color, 0.65),
                tail,
                max(2, flash_radius),
                2,
            )
            for side in (-1, 1):
                ray_end = (
                    int(tail[0] + perpendicular_x * flash_radius * side),
                    int(tail[1] + perpendicular_y * flash_radius * side),
                )
                pygame.draw.line(screen, core_color, tail, ray_end, 2)

    @staticmethod
    def _fade_color(color, fade):
        fade = max(0.0, min(1.0, fade))
        return tuple(int(channel * fade) for channel in color)
