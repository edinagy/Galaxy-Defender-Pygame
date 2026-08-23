import math
import random

import pygame


# Creează exploziile jocului. Parametrul effect_type permite fiecărui
# tip de inamic să aibă propria culoare, intensitate și durată.
class Explosion:

    def __init__(self, x, y, effect_type="default"):
        self.x = float(x)
        self.y = float(y)
        self.effect_type = effect_type
        self.age = 0
        self.finished = False
        self.particles = []
        self.shockwaves = []
        self.flash_pulses = []
        self.secondary_bursts = []
        self._create_effect()

    # Alege aspectul exploziei în funcție de nava distrusă.
    def _create_effect(self):
        if self.effect_type == "scout":
            self._create_scout_explosion()
        elif self.effect_type == "fighter":
            self._create_fighter_explosion()
        elif self.effect_type == "tank":
            self._create_tank_explosion()
        else:
            self._create_default_explosion()

    # Scout: explozie roșie, rapidă și ascuțită.
    def _create_scout_explosion(self):
        colors = [
            (255, 245, 235),
            (255, 145, 70),
            (255, 55, 45),
            (175, 18, 35),
        ]
        self._add_flash(self.x, self.y, (255, 70, 55), 27, 7)
        self._add_particles(
            self.x, self.y, 34, colors,
            (3.4, 8.2), (2, 6), (18, 32),
            drag=0.955,
        )
        self._add_fragments(
            self.x, self.y, 7, (225, 55, 48),
            (4.0, 8.5), (20, 32),
        )

    # Fighter: descărcare albastră, cu două unde energetice.
    def _create_fighter_explosion(self):
        colors = [
            (245, 255, 255),
            (100, 225, 255),
            (45, 135, 255),
            (40, 65, 205),
        ]
        self._add_flash(self.x, self.y, (80, 175, 255), 40, 10)
        self._add_shockwave(
            self.x, self.y, (85, 195, 255),
            9, 3.5, 21, 3,
        )
        self._add_shockwave(
            self.x, self.y, (80, 105, 255),
            4, 2.25, 29, 2,
        )
        self._add_particles(
            self.x, self.y, 48, colors,
            (2.5, 7.0), (3, 8), (27, 46),
            drag=0.963,
        )
        self._add_fragments(
            self.x, self.y, 11, (75, 150, 255),
            (2.8, 6.7), (28, 44),
        )

    # Tank: detonare verde grea, urmată de două explozii secundare.
    def _create_tank_explosion(self):
        colors = [
            (250, 255, 225),
            (185, 255, 75),
            (65, 235, 80),
            (25, 135, 58),
        ]
        self._add_flash(self.x, self.y, (105, 255, 85), 57, 13)
        self._add_shockwave(
            self.x, self.y, (105, 255, 90),
            12, 3.6, 32, 4,
        )
        self._add_particles(
            self.x, self.y, 60, colors,
            (1.8, 5.9), (4, 10), (36, 62),
            drag=0.972, gravity=0.018,
        )
        self._add_fragments(
            self.x, self.y, 17, (90, 225, 75),
            (2.1, 5.5), (40, 62),
        )

        # Detonările pornesc la câteva frame-uri după prima.
        self.secondary_bursts = [
            {
                "delay": 7,
                "x": self.x - 30,
                "y": self.y + 4,
                "colors": colors,
            },
            {
                "delay": 14,
                "x": self.x + 32,
                "y": self.y - 9,
                "colors": colors,
            },
        ]

    # Explozia implicită rămâne pentru asteroizi, rachete și aliați.
    def _create_default_explosion(self):
        colors = [
            (255, 255, 255),
            (255, 220, 50),
            (255, 120, 20),
            (255, 50, 0),
        ]
        self._add_flash(self.x, self.y, (255, 175, 45), 27, 8)
        self._add_particles(
            self.x, self.y, 35, colors,
            (1.2, 6.8), (3, 8), (20, 40),
            drag=0.96,
        )

    # Adaugă particulele luminoase ale unei explozii.
    def _add_particles(
        self,
        x,
        y,
        count,
        colors,
        speed_range,
        size_range,
        life_range,
        drag,
        gravity=0.0,
    ):
        for _ in range(count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(*speed_range)
            life = random.randint(*life_range)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "drag": drag,
                    "gravity": gravity,
                    "size": random.randint(*size_range),
                    "life": life,
                    "maximum_life": life,
                    "color": random.choice(colors),
                    "fragment": False,
                }
            )

    # Fragmentele sunt mai lungi și mai întunecate decât energia.
    def _add_fragments(
        self,
        x,
        y,
        count,
        color,
        speed_range,
        life_range,
    ):
        for _ in range(count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(*speed_range)
            life = random.randint(*life_range)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "drag": 0.975,
                    "gravity": 0.035,
                    "size": random.randint(3, 6),
                    "life": life,
                    "maximum_life": life,
                    "color": color,
                    "fragment": True,
                }
            )

    def _add_flash(self, x, y, color, radius, life):
        self.flash_pulses.append(
            {
                "x": float(x),
                "y": float(y),
                "color": color,
                "radius": radius,
                "life": life,
                "maximum_life": life,
            }
        )

    def _add_shockwave(
        self,
        x,
        y,
        color,
        radius,
        speed,
        life,
        width,
    ):
        self.shockwaves.append(
            {
                "x": float(x),
                "y": float(y),
                "color": color,
                "radius": float(radius),
                "speed": speed,
                "life": life,
                "maximum_life": life,
                "width": width,
            }
        )

    # Pornește una dintre detonările secundare ale tank-ului.
    def _activate_secondary_burst(self, burst):
        self._add_flash(
            burst["x"], burst["y"],
            (135, 255, 95), 31, 8,
        )
        self._add_shockwave(
            burst["x"], burst["y"], (80, 235, 75),
            6, 2.7, 22, 3,
        )
        self._add_particles(
            burst["x"], burst["y"], 23, burst["colors"],
            (1.7, 5.2), (3, 8), (25, 45),
            drag=0.968, gravity=0.02,
        )

    # Actualizează fizica particulelor și durata undelor de șoc.
    def update(self):
        self.age += 1

        for burst in self.secondary_bursts[:]:
            if self.age >= burst["delay"]:
                self._activate_secondary_burst(burst)
                self.secondary_bursts.remove(burst)

        for particle in self.particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["dx"] *= particle["drag"]
            particle["dy"] *= particle["drag"]
            particle["dy"] += particle["gravity"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                self.particles.remove(particle)

        for shockwave in self.shockwaves[:]:
            shockwave["radius"] += shockwave["speed"]
            shockwave["speed"] *= 0.985
            shockwave["life"] -= 1
            if shockwave["life"] <= 0:
                self.shockwaves.remove(shockwave)

        for flash in self.flash_pulses[:]:
            flash["life"] -= 1
            if flash["life"] <= 0:
                self.flash_pulses.remove(flash)

        self.finished = not (
            self.particles
            or self.shockwaves
            or self.flash_pulses
            or self.secondary_bursts
        )

    # Desenează mai întâi undele, apoi particulele și nucleele luminoase.
    def draw(self, screen):
        for shockwave in self.shockwaves:
            fade = shockwave["life"] / shockwave["maximum_life"]
            color = self._fade_color(shockwave["color"], fade)
            position = (
                int(shockwave["x"]),
                int(shockwave["y"]),
            )
            # Conturul exterior întunecat oferă undei mai multă profunzime.
            pygame.draw.circle(
                screen,
                self._fade_color(color, 0.25),
                position,
                max(1, int(shockwave["radius"])),
                shockwave["width"] + 4,
            )
            pygame.draw.circle(
                screen,
                color,
                position,
                max(1, int(shockwave["radius"])),
                shockwave["width"],
            )

        for particle in self.particles:
            fade = particle["life"] / particle["maximum_life"]
            color = self._fade_color(
                particle["color"],
                0.25 + fade * 0.75,
            )
            position = (int(particle["x"]), int(particle["y"]))
            trail_start = (
                int(particle["x"] - particle["dx"] * 2.7),
                int(particle["y"] - particle["dy"] * 2.7),
            )

            if particle["fragment"]:
                pygame.draw.line(
                    screen,
                    self._fade_color(color, 0.28),
                    trail_start,
                    position,
                    max(2, int(particle["size"] * fade) + 3),
                )
                pygame.draw.line(
                    screen,
                    color,
                    trail_start,
                    position,
                    max(1, int(particle["size"] * fade)),
                )
            else:
                spark_width = max(
                    1,
                    int(particle["size"] * fade * 0.55),
                )
                pygame.draw.line(
                    screen,
                    self._fade_color(color, 0.35),
                    trail_start,
                    position,
                    spark_width + 4,
                )
                pygame.draw.line(
                    screen,
                    color,
                    trail_start,
                    position,
                    spark_width,
                )
                pygame.draw.circle(
                    screen,
                    self._fade_color((255, 255, 255), fade),
                    position,
                    max(1, spark_width // 2),
                )

        for flash in self.flash_pulses:
            fade = flash["life"] / flash["maximum_life"]
            radius = max(2, int(flash["radius"] * fade))
            position = (int(flash["x"]), int(flash["y"]))
            self._draw_radial_glow(
                screen,
                position,
                flash["color"],
                radius,
                fade,
            )
            pygame.draw.circle(
                screen,
                self._fade_color(flash["color"], 0.72 * fade),
                position,
                radius,
            )
            pygame.draw.circle(
                screen,
                (255, 255, 245),
                position,
                max(2, int(radius * 0.38)),
            )

    # Construiește un halou luminos din mai multe straturi aditive.
    @classmethod
    def _draw_radial_glow(
        cls,
        screen,
        position,
        color,
        radius,
        fade,
    ):
        glow_radius = max(4, int(radius * 2.15))
        glow_size = glow_radius * 2 + 2
        glow_surface = pygame.Surface(
            (glow_size, glow_size),
            pygame.SRCALPHA,
        )
        center = (glow_size // 2, glow_size // 2)

        glow_layers = [
            (1.00, 0.055),
            (0.76, 0.085),
            (0.54, 0.13),
            (0.34, 0.20),
        ]
        for radius_scale, intensity in glow_layers:
            pygame.draw.circle(
                glow_surface,
                cls._fade_color(color, intensity * fade),
                center,
                max(1, int(glow_radius * radius_scale)),
            )

        screen.blit(
            glow_surface,
            (
                position[0] - center[0],
                position[1] - center[1],
            ),
            special_flags=pygame.BLEND_RGB_ADD,
        )

    @staticmethod
    def _fade_color(color, fade):
        fade = max(0.0, min(1.0, fade))
        return (
            int(color[0] * fade),
            int(color[1] * fade),
            int(color[2] * fade),
        )
