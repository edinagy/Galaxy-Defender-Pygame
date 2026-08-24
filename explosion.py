import math
import random

import pygame


# Creează exploziile jocului. Parametrul effect_type permite fiecărui
# tip de inamic să aibă propria culoare, intensitate și durată.
class Explosion:

    def __init__(self, x, y, effect_type="default", scale=1.0):
        self.x = float(x)
        self.y = float(y)
        self.effect_type = effect_type
        self.scale = max(0.55, min(2.4, float(scale)))
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
        elif self.effect_type == "shield_carrier":
            self._create_shield_carrier_explosion()
        elif self.effect_type == "phase_hunter":
            self._create_phase_hunter_explosion()
        elif self.effect_type == "tank":
            self._create_tank_explosion()
        elif self.effect_type == "asteroid":
            self._create_asteroid_explosion()
        elif self.effect_type == "missile":
            self._create_missile_explosion()
        elif self.effect_type == "drone":
            self._create_drone_explosion()
        elif self.effect_type == "crossfire":
            self._create_crossfire_explosion()
        elif self.effect_type == "ally":
            self._create_ally_explosion()
        elif self.effect_type == "elite":
            self._create_elite_explosion()
        elif self.effect_type == "boss":
            self._create_boss_explosion()
        elif self.effect_type == "singularity":
            self._create_singularity_explosion()
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

    # Shield Carrier: câmpul cyan se prăbușește în trei unde concentrice.
    def _create_shield_carrier_explosion(self):
        colors = [
            (245, 255, 255),
            (75, 235, 255),
            (35, 145, 245),
            (175, 55, 235),
        ]
        self._add_flash(
            self.x,
            self.y,
            (85, 225, 255),
            62,
            13,
        )
        self._add_shockwave(
            self.x, self.y, (95, 235, 255),
            14, 4.8, 34, 5,
        )
        self._add_shockwave(
            self.x, self.y, (70, 150, 255),
            8, 3.5, 42, 3,
        )
        self._add_shockwave(
            self.x, self.y, (195, 75, 255),
            4, 2.5, 50, 2,
        )
        self._add_particles(
            self.x, self.y, 70, colors,
            (2.0, 7.5), (3, 9), (34, 62),
            drag=0.964,
        )
        self._add_fragments(
            self.x, self.y, 18, (65, 175, 215),
            (2.6, 7.2), (36, 60),
        )

    # Phase Hunter: o implozie magenta urmată de două rupturi cyan rapide.
    def _create_phase_hunter_explosion(self):
        colors = [
            (255, 245, 255),
            (255, 55, 205),
            (145, 35, 210),
            (55, 235, 225),
        ]
        self._add_flash(
            self.x, self.y, (245, 55, 205), 48, 11,
        )
        self._add_shockwave(
            self.x, self.y, (255, 55, 210),
            40, -1.15, 22, 4,
        )
        self._add_shockwave(
            self.x, self.y, (55, 235, 225),
            8, 4.2, 30, 3,
        )
        self._add_particles(
            self.x, self.y, 58, colors,
            (2.8, 8.2), (2, 7), (24, 46),
            drag=0.956,
        )
        self._add_fragments(
            self.x, self.y, 12, (215, 45, 190),
            (3.5, 8.0), (24, 43),
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

    # Asteroid: rocă incandescentă, praf și fragmente grele neregulate.
    def _create_asteroid_explosion(self):
        colors = [
            (255, 235, 195),
            (235, 155, 75),
            (155, 92, 55),
            (85, 72, 70),
        ]
        self._add_flash(self.x, self.y, (245, 165, 85), 34, 9)
        self._add_shockwave(
            self.x, self.y, (185, 125, 85),
            8, 3.0, 26, 4,
        )
        self._add_particles(
            self.x, self.y, 44, colors,
            (1.4, 6.2), (3, 9), (28, 52),
            drag=0.968, gravity=0.045,
        )
        self._add_fragments(
            self.x, self.y, 20, (105, 82, 72),
            (2.0, 7.2), (36, 64),
        )

    # Rachetă: detonare compactă, albă în centru și cu șrapnel roșu.
    def _create_missile_explosion(self):
        colors = [
            (255, 255, 245),
            (255, 220, 95),
            (255, 105, 35),
            (210, 35, 30),
        ]
        self._add_flash(self.x, self.y, (255, 175, 55), 43, 10)
        self._add_shockwave(
            self.x, self.y, (255, 115, 45),
            7, 4.5, 23, 4,
        )
        self._add_shockwave(
            self.x, self.y, (255, 215, 145),
            4, 2.7, 17, 2,
        )
        self._add_particles(
            self.x, self.y, 52, colors,
            (3.0, 9.0), (2, 7), (20, 40),
            drag=0.948, gravity=0.025,
        )
        self._add_fragments(
            self.x, self.y, 13, (175, 42, 35),
            (4.0, 9.5), (24, 45),
        )

    # Dronă: descărcare electrică albastră și resturi tehnologice mici.
    def _create_drone_explosion(self):
        colors = [
            (245, 255, 255),
            (85, 225, 255),
            (40, 145, 255),
            (55, 75, 205),
        ]
        self._add_flash(self.x, self.y, (65, 190, 255), 36, 9)
        self._add_shockwave(
            self.x, self.y, (75, 205, 255),
            6, 3.7, 24, 3,
        )
        self._add_particles(
            self.x, self.y, 46, colors,
            (2.7, 7.5), (2, 6), (24, 45),
            drag=0.957,
        )
        self._add_fragments(
            self.x, self.y, 10, (55, 105, 195),
            (3.2, 7.7), (29, 48),
        )

    # Crossfire: energia magenta se prăbușește și reapare în două impulsuri.
    def _create_crossfire_explosion(self):
        colors = [
            (255, 245, 255),
            (255, 105, 215),
            (195, 45, 255),
            (95, 25, 175),
        ]
        self._add_flash(self.x, self.y, (245, 55, 190), 48, 11)
        self._add_shockwave(
            self.x, self.y, (245, 70, 215),
            8, 4.0, 30, 4,
        )
        self._add_shockwave(
            self.x, self.y, (135, 65, 255),
            5, 2.45, 38, 2,
        )
        self._add_particles(
            self.x, self.y, 58, colors,
            (2.2, 7.6), (3, 8), (30, 54),
            drag=0.963,
        )
        self._add_fragments(
            self.x, self.y, 16, (115, 40, 165),
            (2.8, 7.0), (34, 56),
        )
        self.secondary_bursts = [
            {
                "delay": 8,
                "x": self.x - 24,
                "y": self.y + 8,
                "colors": colors,
                "flash_color": (255, 65, 205),
                "shockwave_color": (175, 65, 255),
                "particle_count": 18,
            },
            {
                "delay": 15,
                "x": self.x + 28,
                "y": self.y - 12,
                "colors": colors,
                "flash_color": (185, 70, 255),
                "shockwave_color": (235, 75, 220),
                "particle_count": 16,
            },
        ]

    # Aliat: reactorul cyan se descarcă în inele albe și fragmente albastre.
    def _create_ally_explosion(self):
        colors = [
            (255, 255, 255),
            (145, 245, 255),
            (45, 185, 255),
            (45, 85, 210),
        ]
        self._add_flash(self.x, self.y, (80, 220, 255), 51, 12)
        self._add_shockwave(
            self.x, self.y, (115, 235, 255),
            9, 4.1, 32, 4,
        )
        self._add_shockwave(
            self.x, self.y, (85, 115, 255),
            5, 2.6, 42, 2,
        )
        self._add_particles(
            self.x, self.y, 62, colors,
            (2.0, 7.2), (3, 8), (32, 58),
            drag=0.965, gravity=0.012,
        )
        self._add_fragments(
            self.x, self.y, 18, (55, 115, 195),
            (2.8, 7.0), (38, 62),
        )

    # Elită: explozie violet amplă, pentru formația rară cu viață mare.
    def _create_elite_explosion(self):
        colors = [
            (255, 250, 255),
            (225, 145, 255),
            (165, 55, 245),
            (75, 20, 145),
        ]
        self._add_flash(self.x, self.y, (205, 75, 255), 56, 13)
        self._add_shockwave(
            self.x, self.y, (205, 85, 255),
            10, 4.3, 34, 5,
        )
        self._add_particles(
            self.x, self.y, 72, colors,
            (2.4, 8.3), (3, 9), (34, 64),
            drag=0.966,
        )
        self._add_fragments(
            self.x, self.y, 20, (105, 40, 165),
            (3.0, 8.0), (38, 65),
        )

    # Boss: detonare roșie stratificată, folosită în secvența finală.
    def _create_boss_explosion(self):
        colors = [
            (255, 255, 250),
            (255, 175, 205),
            (255, 55, 115),
            (125, 15, 75),
        ]
        self._add_flash(self.x, self.y, (255, 45, 105), 66, 14)
        self._add_shockwave(
            self.x, self.y, (255, 55, 115),
            12, 5.0, 38, 6,
        )
        self._add_shockwave(
            self.x, self.y, (255, 175, 205),
            5, 3.1, 46, 3,
        )
        self._add_particles(
            self.x, self.y, 78, colors,
            (2.5, 9.0), (3, 10), (38, 72),
            drag=0.967, gravity=0.012,
        )
        self._add_fragments(
            self.x, self.y, 24, (95, 25, 65),
            (3.2, 8.8), (42, 76),
        )

    # Black Hole: implozie violet-albastră pentru obiectele absorbite.
    def _create_singularity_explosion(self):
        colors = [
            (245, 235, 255),
            (170, 105, 255),
            (75, 75, 225),
            (25, 20, 90),
        ]
        self._add_flash(self.x, self.y, (105, 75, 235), 38, 10)
        self._add_shockwave(
            self.x, self.y, (125, 85, 255),
            24, -0.62, 30, 4,
        )
        self._add_shockwave(
            self.x, self.y, (65, 115, 255),
            7, 2.1, 24, 2,
        )
        self._add_particles(
            self.x, self.y, 38, colors,
            (1.2, 5.5), (2, 6), (22, 42),
            drag=0.91,
        )

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
        scaled_count = max(
            1,
            int(count * (0.72 + self.scale * 0.28)),
        )
        speed_scale = self.scale ** 0.68
        minimum_size = max(1, int(size_range[0] * self.scale))
        maximum_size = max(
            minimum_size,
            int(size_range[1] * self.scale),
        )

        for _ in range(scaled_count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(*speed_range) * speed_scale
            life = random.randint(*life_range)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "drag": drag,
                    "gravity": gravity * self.scale,
                    "size": random.randint(minimum_size, maximum_size),
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
        scaled_count = max(
            1,
            int(count * (0.72 + self.scale * 0.28)),
        )
        speed_scale = self.scale ** 0.68
        minimum_size = max(2, int(3 * self.scale))
        maximum_size = max(minimum_size, int(6 * self.scale))

        for _ in range(scaled_count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(*speed_range) * speed_scale
            life = random.randint(*life_range)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "drag": 0.975,
                    "gravity": 0.035 * self.scale,
                    "size": random.randint(minimum_size, maximum_size),
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
                "radius": max(2, int(radius * self.scale)),
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
                "radius": float(radius * self.scale),
                "speed": speed * self.scale,
                "life": life,
                "maximum_life": life,
                "width": max(1, int(width * self.scale)),
            }
        )

    # Pornește detonările secundare configurate de tank sau Crossfire.
    def _activate_secondary_burst(self, burst):
        flash_color = burst.get(
            "flash_color",
            (135, 255, 95),
        )
        shockwave_color = burst.get(
            "shockwave_color",
            (80, 235, 75),
        )
        particle_count = burst.get("particle_count", 23)
        self._add_flash(
            burst["x"], burst["y"],
            flash_color, 31, 8,
        )
        self._add_shockwave(
            burst["x"], burst["y"], shockwave_color,
            6, 2.7, 22, 3,
        )
        self._add_particles(
            burst["x"], burst["y"], particle_count, burst["colors"],
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

        self._draw_effect_signature(screen)

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

            if particle["fragment"] and self.effect_type == "asteroid":
                # Bucățile de asteroid rămân corpuri neregulate, nu lasere.
                velocity_length = max(
                    0.001,
                    math.hypot(particle["dx"], particle["dy"]),
                )
                direction_x = particle["dx"] / velocity_length
                direction_y = particle["dy"] / velocity_length
                perpendicular_x = -direction_y
                perpendicular_y = direction_x
                chunk_length = max(3, int(particle["size"] * fade * 1.8))
                chunk_width = max(2, int(particle["size"] * fade))
                chunk_points = [
                    (
                        int(position[0] + direction_x * chunk_length),
                        int(position[1] + direction_y * chunk_length),
                    ),
                    (
                        int(position[0] + perpendicular_x * chunk_width),
                        int(position[1] + perpendicular_y * chunk_width),
                    ),
                    (
                        int(position[0] - direction_x * chunk_length * 0.75),
                        int(position[1] - direction_y * chunk_length * 0.75),
                    ),
                    (
                        int(position[0] - perpendicular_x * chunk_width),
                        int(position[1] - perpendicular_y * chunk_width),
                    ),
                ]
                pygame.draw.polygon(
                    screen,
                    self._fade_color((45, 35, 35), fade),
                    chunk_points,
                )
                pygame.draw.polygon(screen, color, chunk_points, 2)

            elif particle["fragment"]:
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

    # Fiecare familie primește o formă recognoscibilă, pe lângă paletă.
    def _draw_effect_signature(self, screen):
        position = (int(self.x), int(self.y))
        signature_duration = 62 if self.effect_type == "boss" else 44
        fade = max(0.0, 1.0 - self.age / signature_duration)
        if fade <= 0:
            return

        if self.effect_type == "missile":
            # Racheta produce o stea de șoc ascuțită.
            ray_length = int((28 + self.age * 5.2) * self.scale)
            for ray_index in range(8):
                angle = ray_index * math.tau / 8 + 0.16
                ray_end = (
                    int(self.x + math.cos(angle) * ray_length),
                    int(self.y + math.sin(angle) * ray_length),
                )
                pygame.draw.line(
                    screen,
                    self._fade_color((255, 165, 65), fade),
                    position,
                    ray_end,
                    max(1, int(3 * fade * self.scale)),
                )

        elif self.effect_type in ("drone", "ally"):
            # Arcurile electrice au câte o ruptură la mijloc.
            base_color = (
                (55, 175, 255)
                if self.effect_type == "drone"
                else (115, 235, 255)
            )
            inner_radius = int((12 + self.age * 1.1) * self.scale)
            outer_radius = int((29 + self.age * 2.7) * self.scale)
            for arc_index in range(6):
                angle = (
                    arc_index * math.tau / 6
                    + self.age * 0.045 * (-1 if arc_index % 2 else 1)
                )
                start = (
                    int(self.x + math.cos(angle) * inner_radius),
                    int(self.y + math.sin(angle) * inner_radius),
                )
                midpoint = (
                    int(
                        self.x
                        + math.cos(angle + 0.11) * (inner_radius + outer_radius) / 2
                    ),
                    int(
                        self.y
                        + math.sin(angle + 0.11) * (inner_radius + outer_radius) / 2
                    ),
                )
                end = (
                    int(self.x + math.cos(angle) * outer_radius),
                    int(self.y + math.sin(angle) * outer_radius),
                )
                pygame.draw.lines(
                    screen,
                    self._fade_color(base_color, fade),
                    False,
                    [start, midpoint, end],
                    max(1, int(3 * fade)),
                )

        elif self.effect_type in ("crossfire", "elite", "phase_hunter"):
            # Segmentele violete se rotesc în sensuri opuse.
            if self.effect_type == "phase_hunter":
                base_color = (55, 235, 225)
            elif self.effect_type == "crossfire":
                base_color = (255, 75, 205)
            else:
                base_color = (190, 80, 255)
            radius = max(3, int((18 + self.age * 3.4) * self.scale))
            arc_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            arc_rect.center = position
            rotation = self.age * 0.12
            for segment_index in range(4):
                start_angle = rotation + segment_index * math.pi / 2
                pygame.draw.arc(
                    screen,
                    self._fade_color(base_color, fade),
                    arc_rect,
                    start_angle,
                    start_angle + 0.58,
                    max(1, int(4 * fade)),
                )

        elif self.effect_type == "boss":
            # Detonarea nucleului trimite raze lungi prin corpul fortăreței.
            ray_length = int((35 + self.age * 5.0) * self.scale)
            for ray_index in range(12):
                angle = ray_index * math.tau / 12 + self.age * 0.012
                ray_start = (
                    int(self.x + math.cos(angle) * 10),
                    int(self.y + math.sin(angle) * 10),
                )
                ray_end = (
                    int(self.x + math.cos(angle) * ray_length),
                    int(self.y + math.sin(angle) * ray_length),
                )
                pygame.draw.line(
                    screen,
                    self._fade_color((255, 55, 115), fade),
                    ray_start,
                    ray_end,
                    max(1, int(4 * fade)),
                )

        elif self.effect_type == "singularity":
            # Centrul negru și inelele contractate sugerează o implozie.
            core_radius = max(3, int((24 - self.age * 0.7) * self.scale))
            pygame.draw.circle(screen, (2, 2, 12), position, core_radius)
            pygame.draw.circle(
                screen,
                self._fade_color((145, 95, 255), fade),
                position,
                core_radius + max(2, int(7 * fade)),
                max(1, int(3 * fade)),
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
