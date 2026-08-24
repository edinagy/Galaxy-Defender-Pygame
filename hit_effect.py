import math
import random

import pygame


# Impactul preia culoarea nivelului armei care a produs lovitura.
class HitEffect:

    LEVEL_PALETTES = {
        1: ((20, 125, 255), (65, 225, 255), (245, 255, 255)),
        2: ((15, 165, 165), (40, 255, 210), (245, 255, 255)),
        3: ((115, 40, 230), (215, 85, 255), (255, 235, 255)),
        4: ((230, 75, 10), (255, 195, 40), (255, 255, 220)),
    }

    def __init__(
        self,
        x,
        y,
        weapon_level=1,
        effect_type="weapon",
    ):
        self.x = float(x)
        self.y = float(y)
        self.weapon_level = max(1, min(4, int(weapon_level)))
        self.effect_type = effect_type
        self.age = 0
        self.finished = False
        self.particles = []

        if effect_type == "player_damage":
            self.palette = (
                (150, 20, 35),
                (255, 70, 45),
                (255, 225, 155),
            )
            particle_count = 28
            self.ring_duration = 19
            self.ring_speed = 3.2
        elif effect_type == "ally":
            self.palette = (
                (25, 115, 220),
                (75, 235, 255),
                (245, 255, 255),
            )
            particle_count = 20
            self.ring_duration = 14
            self.ring_speed = 2.5
        else:
            self.palette = self.LEVEL_PALETTES[self.weapon_level]
            particle_count = 13 + self.weapon_level * 5
            self.ring_duration = 11 + self.weapon_level * 2
            self.ring_speed = 2.0 + self.weapon_level * 0.45

        self.ring_life = self.ring_duration
        for particle_index in range(particle_count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(
                2.2,
                4.8 + self.weapon_level * 0.75,
            )
            life = random.randint(14, 24 + self.weapon_level * 3)
            self.particles.append(
                {
                    "x": self.x,
                    "y": self.y,
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "drag": random.uniform(0.91, 0.96),
                    "size": random.randint(2, 4 + self.weapon_level),
                    "life": life,
                    "maximum_life": life,
                    "color": random.choice(self.palette),
                }
            )

    def update(self):
        self.age += 1
        if self.ring_life > 0:
            self.ring_life -= 1

        for particle in self.particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["dx"] *= particle["drag"]
            particle["dy"] *= particle["drag"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                self.particles.remove(particle)

        self.finished = not self.particles and self.ring_life <= 0

    def draw(self, screen):
        if self.ring_life > 0:
            ring_fade = self.ring_life / self.ring_duration
            ring_radius = int(
                5
                + (self.ring_duration - self.ring_life)
                * self.ring_speed
            )
            ring_color = self._fade_color(
                self.palette[1],
                ring_fade,
            )
            pygame.draw.circle(
                screen,
                self._fade_color(ring_color, 0.28),
                (int(self.x), int(self.y)),
                ring_radius,
                6,
            )
            pygame.draw.circle(
                screen,
                ring_color,
                (int(self.x), int(self.y)),
                ring_radius,
                2,
            )

        for particle in self.particles:
            fade = particle["life"] / particle["maximum_life"]
            color = self._fade_color(
                particle["color"],
                0.25 + fade * 0.75,
            )
            position = (int(particle["x"]), int(particle["y"]))
            trail = (
                int(particle["x"] - particle["dx"] * 3.0),
                int(particle["y"] - particle["dy"] * 3.0),
            )
            spark_width = max(1, int(particle["size"] * fade * 0.55))
            pygame.draw.line(
                screen,
                self._fade_color(color, 0.30),
                trail,
                position,
                spark_width + 4,
            )
            pygame.draw.line(
                screen,
                color,
                trail,
                position,
                spark_width,
            )

        # Flash-ul central durează numai primele cadre.
        if self.age < 7:
            flash_fade = 1.0 - self.age / 7
            pygame.draw.circle(
                screen,
                self._fade_color(self.palette[1], 0.65 * flash_fade),
                (int(self.x), int(self.y)),
                max(2, int((13 + self.weapon_level * 3) * flash_fade)),
            )
            pygame.draw.circle(
                screen,
                self.palette[2],
                (int(self.x), int(self.y)),
                max(2, int(5 * flash_fade)),
            )

    @staticmethod
    def _fade_color(color, fade):
        fade = max(0.0, min(1.0, fade))
        return tuple(int(channel * fade) for channel in color)


# Secvența finală a navei: suprasarcină, explozii locale, apoi detonare.
class PlayerDestructionEffect:

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.age = 0
        self.duration = 102
        self.finished = False
        self.particles = []
        self.rings = []
        self.burst_schedule = [
            (7, -27, -22, 0.55),
            (17, 28, 8, 0.65),
            (29, -18, 31, 0.78),
            (42, 18, -34, 0.90),
            (53, 0, 0, 1.65),
        ]

        self._spawn_burst(0, 0, 0.45, electrical=True)

    def _spawn_burst(
        self,
        offset_x,
        offset_y,
        scale,
        electrical=False,
    ):
        center_x = self.x + offset_x
        center_y = self.y + offset_y
        palette = (
            (30, 120, 255),
            (60, 225, 255),
            (255, 165, 45),
            (255, 245, 220),
        )
        particle_count = int((22 if electrical else 35) * scale)
        if scale > 1.0:
            particle_count = 84

        for particle_index in range(particle_count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(2.0, 6.8) * max(0.7, scale)
            life = random.randint(24, int(42 + scale * 15))
            self.particles.append(
                {
                    "x": center_x,
                    "y": center_y,
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "drag": random.uniform(0.94, 0.975),
                    "gravity": random.uniform(0.0, 0.045),
                    "size": random.randint(2, max(3, int(6 * scale))),
                    "life": life,
                    "maximum_life": life,
                    "color": random.choice(palette),
                    "hull": particle_index % 5 == 0,
                }
            )

        self.rings.append(
            {
                "x": center_x,
                "y": center_y,
                "radius": 5.0,
                "speed": 2.4 + scale * 2.1,
                "life": int(16 + scale * 12),
                "maximum_life": int(16 + scale * 12),
                "color": (
                    (75, 210, 255)
                    if electrical
                    else (255, 145, 45)
                ),
            }
        )

    def update(self):
        self.age += 1

        for scheduled_burst in self.burst_schedule[:]:
            burst_age, offset_x, offset_y, scale = scheduled_burst
            if self.age >= burst_age:
                self._spawn_burst(offset_x, offset_y, scale)
                self.burst_schedule.remove(scheduled_burst)

        for particle in self.particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["dx"] *= particle["drag"]
            particle["dy"] *= particle["drag"]
            particle["dy"] += particle["gravity"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                self.particles.remove(particle)

        for ring in self.rings[:]:
            ring["radius"] += ring["speed"]
            ring["speed"] *= 0.985
            ring["life"] -= 1
            if ring["life"] <= 0:
                self.rings.remove(ring)

        self.finished = (
            self.age >= self.duration
            and not self.particles
            and not self.rings
        )

    def draw(self, screen):
        # Arcurile electrice pregătesc vizual detonarea principală.
        if self.age < 54:
            electrical_fade = 1.0 - self.age / 54
            for arc_index in range(6):
                arc_points = [(int(self.x), int(self.y))]
                base_angle = (
                    arc_index * math.tau / 6
                    + self.age * 0.035
                )
                for segment in range(1, 5):
                    distance = segment * (14 + self.age * 0.12)
                    jitter = math.sin(
                        self.age * 0.6 + arc_index * 2.1 + segment
                    ) * 7
                    arc_points.append(
                        (
                            int(
                                self.x
                                + math.cos(base_angle) * distance
                                + math.cos(base_angle + math.pi / 2) * jitter
                            ),
                            int(
                                self.y
                                + math.sin(base_angle) * distance
                                + math.sin(base_angle + math.pi / 2) * jitter
                            ),
                        )
                    )
                pygame.draw.lines(
                    screen,
                    HitEffect._fade_color(
                        (100, 225, 255),
                        electrical_fade,
                    ),
                    False,
                    arc_points,
                    2,
                )

        for ring in self.rings:
            fade = ring["life"] / ring["maximum_life"]
            color = HitEffect._fade_color(ring["color"], fade)
            pygame.draw.circle(
                screen,
                HitEffect._fade_color(color, 0.25),
                (int(ring["x"]), int(ring["y"])),
                max(1, int(ring["radius"])),
                7,
            )
            pygame.draw.circle(
                screen,
                color,
                (int(ring["x"]), int(ring["y"])),
                max(1, int(ring["radius"])),
                2,
            )

        for particle in self.particles:
            fade = particle["life"] / particle["maximum_life"]
            color = HitEffect._fade_color(
                particle["color"],
                0.22 + fade * 0.78,
            )
            position = (int(particle["x"]), int(particle["y"]))
            trail = (
                int(particle["x"] - particle["dx"] * 3.0),
                int(particle["y"] - particle["dy"] * 3.0),
            )
            pygame.draw.line(
                screen,
                HitEffect._fade_color(color, 0.28),
                trail,
                position,
                max(2, particle["size"] + 3),
            )
            pygame.draw.line(
                screen,
                color,
                trail,
                position,
                max(1, particle["size"] if particle["hull"] else 2),
            )

        # Nucleul devine alb exact în momentul detonării finale.
        if 48 <= self.age <= 61:
            distance_from_peak = abs(54 - self.age)
            flash_radius = max(2, 42 - distance_from_peak * 6)
            pygame.draw.circle(
                screen,
                (255, 245, 220),
                (int(self.x), int(self.y)),
                flash_radius,
            )
