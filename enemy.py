import math
import random
from pathlib import Path

import pygame


# Reprezintă un inamic care intră în arenă și apoi patrulează liber.
class Enemy:

    # Încarcă imaginea și configurează comportamentul tipului primit.
    def __init__(
        self,
        x,
        y,
        enemy_type="fighter",
        difficulty_wave=1,
    ):
        self.x = float(x)
        self.y = float(y)
        self.enemy_type = enemy_type
        self.difficulty_wave = max(1, int(difficulty_wave))

        # Construiește căile pornind de la folderul jocului, astfel încât
        # imaginile se încarcă bine indiferent de unde este pornit main.py.
        enemies_folder = (
            Path(__file__).resolve().parent
            / "assets"
            / "images"
            / "enemies"
        )

        if self.enemy_type == "elite":
            image_path = (
                enemies_folder
                / "enemy_alien_elite.png"
            )
            image_size = (250, 250)
            self.entry_speed = 4.8
            self.patrol_speed = 1.65

            # Elita are direct 30 HP chiar de la prima aparitie.
            # Viata nu mai creste treptat in functie de wave.
            self.health = 30
            # Recompensa mare transforma elita intr-o tinta importanta.
            self.points = 1500
            self.decision_range = (110, 180)

        elif self.enemy_type == "scout":
            image_path = self._choose_sprite(
                enemies_folder,
                "enemy_alien_scout_v2.png",
                "enemy_alien_scout.png",
            )
            image_size = (150, 150)
            self.entry_speed = 3.6
            self.patrol_speed = 3.4
            self.health = 1
            self.points = 15
            self.decision_range = (55, 110)

        elif self.enemy_type == "tank":
            image_path = self._choose_sprite(
                enemies_folder,
                "enemy_alien_tank_v2.png",
                "enemy_alien_tank.png",
            )
            image_size = (240, 200)
            self.entry_speed = 1.5
            self.patrol_speed = 1.25
            self.health = 3
            self.points = 50
            self.decision_range = (150, 250)

        else:
            image_path = self._choose_sprite(
                enemies_folder,
                "enemy_alien_fighter_v2.png",
                "enemy_alien_fighter.png",
            )
            image_size = (190, 190)
            self.entry_speed = 2.3
            self.patrol_speed = 2.15
            self.health = 2
            self.points = 25
            self.decision_range = (90, 175)

        # Dificultatea crește gradual cu fiecare wave, dar are limite clare.
        # Elita păstrează permanent cele 30 HP stabilite; numai ritmul și
        # mobilitatea ei evoluează, ca lupta să nu devină un test de răbdare.
        wave_progress = self.difficulty_wave - 1
        self.difficulty_tier = min(
            5,
            1 + wave_progress // 2,
        )
        self.attack_cooldown_scale = max(
            0.76,
            1.0 - wave_progress * 0.025,
        )
        self.projectile_speed_multiplier = min(
            1.18,
            1.0 + wave_progress * 0.018,
        )

        if self.enemy_type == "elite":
            movement_multiplier = min(
                1.15,
                1.0 + wave_progress * 0.015,
            )
        else:
            movement_multiplier = min(
                1.25,
                1.0 + wave_progress * 0.025,
            )

            if self.enemy_type == "scout":
                self.health += min(2, wave_progress // 4)
            elif self.enemy_type == "tank":
                self.health += min(3, self.difficulty_wave // 3)
            else:
                self.health += min(2, wave_progress // 3)

            # Recompensa urcă împreună cu riscul, până la maximum dublu.
            points_multiplier = min(
                2.0,
                1.0 + wave_progress * 0.10,
            )
            self.points = int(
                round(self.points * points_multiplier)
            )

        self.entry_speed *= movement_multiplier
        self.patrol_speed *= movement_multiplier

        loaded_image = pygame.image.load(
            str(image_path)
        ).convert_alpha()

        if self.enemy_type == "elite":
            # Elita nu face parte din această schimbare vizuală.
            self.image = pygame.transform.smoothscale(
                loaded_image,
                image_size,
            )
        else:
            # Elimină spațiul transparent din fișier, păstrează proporțiile
            # navei și o centrează pe o suprafață de aceeași dimensiune.
            # Astfel sprite-ul este clar, iar dreptunghiul de coliziune rămâne
            # identic cu cel folosit înainte de schimbarea imaginilor.
            self.image = self._prepare_standard_sprite(
                loaded_image,
                image_size,
            )

        self.max_health = self.health
        self.counts_toward_wave = self.enemy_type != "elite"

        self.rect = self.image.get_rect(
            topleft=(int(self.x), int(self.y))
        )

        # Inamicul intră mai întâi de sus, apoi începe patrularea.
        self.movement_state = "entering"
        self.entry_target_y = self._choose_entry_y()
        self.target_x = self.x
        self.target_y = self.entry_target_y

        # Vitezele sunt interpolate pentru schimbări line de direcție.
        self.velocity_x = 0.0
        self.velocity_y = self.entry_speed
        self.decision_timer = random.randint(
            *self.decision_range
        )
        self.movement_age = random.randint(
            0,
            500,
        )
        self.wander_phase = random.uniform(
            0,
            math.tau,
        )

        self.engine_particles = []
        self.hit_flash = 0
        self.health_bar_timer = 0

        # Fiecare inamic isi pastreaza propriul cronometru de atac.
        # Scout-ul foloseste in plus doua valori pentru rafala de trei gloante.
        # Primul atac vine repede, chiar in timp ce nava intra in arena.
        # Pauzele mai mari dintre atacurile urmatoare sunt setate in gameplay.
        if self.enemy_type == "elite":
            self.shoot_timer = self.get_attack_delay(120, 180)
        elif self.enemy_type == "scout":
            self.shoot_timer = self.get_attack_delay(75, 120)
        elif self.enemy_type == "tank":
            self.shoot_timer = self.get_attack_delay(105, 155)
        else:
            self.shoot_timer = self.get_attack_delay(90, 140)

        self.burst_shots_remaining = 0
        self.burst_delay = 0

        # Inamicii normali se retrag dupa maximum doua atacuri.
        # Elita ramane obiectivul permanent al wave-ului.
        self.attacks_completed = 0
        self.maximum_attacks = (
            None
            if self.enemy_type == "elite"
            else 2
        )
        self.departure_speed = 0.0
        self.departure_velocity_x = 0.0

        # Elita afiseaza o incarcare vizibila inaintea salvei speciale.
        self.elite_charge_timer = 0
        self.elite_charge_duration = max(
            42,
            55 - self.difficulty_wave,
        )

    # Folosește sprite-ul premium, dar permite revenirea automată la cel vechi
    # dacă imaginea nouă nu a fost încă copiată în folderul proiectului.
    @staticmethod
    def _choose_sprite(folder, premium_name, fallback_name):
        premium_path = folder / premium_name
        if premium_path.exists():
            return premium_path
        return folder / fallback_name

    # Decupează marginile complet transparente fără să deformeze nava.
    @staticmethod
    def _prepare_standard_sprite(loaded_image, canvas_size):
        visible_bounds = loaded_image.get_bounding_rect(
            min_alpha=8,
        )

        if visible_bounds.width > 0 and visible_bounds.height > 0:
            visible_image = loaded_image.subsurface(
                visible_bounds
            ).copy()
        else:
            visible_image = loaded_image

        scale_factor = min(
            canvas_size[0] / visible_image.get_width(),
            canvas_size[1] / visible_image.get_height(),
        )
        scaled_size = (
            max(1, int(visible_image.get_width() * scale_factor)),
            max(1, int(visible_image.get_height() * scale_factor)),
        )
        scaled_image = pygame.transform.smoothscale(
            visible_image,
            scaled_size,
        )

        sprite_canvas = pygame.Surface(
            canvas_size,
            pygame.SRCALPHA,
        )
        sprite_rect = scaled_image.get_rect(
            center=sprite_canvas.get_rect().center,
        )
        sprite_canvas.blit(
            scaled_image,
            sprite_rect,
        )
        return sprite_canvas

    # Scalează pauza dintre atacuri fără să elimine ferestrele de evitare.
    def get_attack_delay(self, minimum_delay, maximum_delay):
        scaled_minimum = max(
            1,
            int(minimum_delay * self.attack_cooldown_scale),
        )
        scaled_maximum = max(
            scaled_minimum,
            int(maximum_delay * self.attack_cooldown_scale),
        )
        return random.randint(
            scaled_minimum,
            scaled_maximum,
        )

    # Alege înălțimea la care inamicul începe lupta.
    def _choose_entry_y(self):
        if self.enemy_type == "elite":
            return random.randint(45, 105)

        if self.enemy_type == "scout":
            return random.randint(80, 260)

        if self.enemy_type == "tank":
            return random.randint(55, 155)

        return random.randint(70, 215)

    # Actualizează intrarea sau patrularea inamicului.
    def move(
        self,
        screen_width=1280,
        screen_height=720,
    ):
        self.movement_age += 1
        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1

        if self.movement_state == "departing":
            self._update_departure()
        elif self.movement_state == "entering":
            self._update_entry(
                screen_width,
                screen_height,
            )
        else:
            self._update_patrol(
                screen_width,
                screen_height,
            )

        if self.movement_state != "departing":
            self._keep_inside_combat_area(
                screen_width,
                screen_height,
            )
        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )
        self.update_engine()

    # Dupa al doilea atac, nava normala paraseste arena prin partea de sus.
    def start_departure(self):
        if (
            self.enemy_type == "elite"
            or self.movement_state == "departing"
        ):
            return

        self.movement_state = "departing"
        self.departure_speed = max(3.8, self.entry_speed + 1.4)
        self.departure_velocity_x = random.uniform(-0.7, 0.7)
        self.velocity_x = 0.0
        self.velocity_y = -self.departure_speed

    # Retragerea accelereaza usor si pastreaza o miscare laterala naturala.
    def _update_departure(self):
        self.departure_speed = min(
            7.0,
            self.departure_speed + 0.045,
        )
        self.x += self.departure_velocity_x
        self.y -= self.departure_speed

    def has_departed(self):
        return (
            self.movement_state == "departing"
            and self.rect.bottom < -20
        )

    # Deplasează inamicul de la marginea de sus spre zona de luptă.
    def _update_entry(
        self,
        screen_width,
        screen_height,
    ):
        if self.enemy_type == "elite":
            # Elita intra rapid, apoi incetineste inainte sa ocupe pozitia.
            # Oscilatia larga produce o intrare cinematica, fara teleportare.
            distance_to_target = max(
                0.0,
                self.entry_target_y - self.y,
            )
            elite_entry_speed = max(
                1.6,
                min(self.entry_speed, distance_to_target * 0.045),
            )
            self.y += elite_entry_speed
            self.x += math.sin(
                self.movement_age * 0.065
                + self.wander_phase
            ) * 1.35
        else:
            self.y += self.entry_speed

        # O mișcare laterală mică face intrarea mai naturală.
        if self.enemy_type != "elite":
            self.x += math.sin(
                self.movement_age * 0.045
                + self.wander_phase
            ) * 0.65

        if self.y < self.entry_target_y:
            return

        self.y = float(self.entry_target_y)
        self.movement_state = "patrolling"
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self._choose_new_target(
            screen_width,
            screen_height,
        )

    # Dirijează lin inamicul spre destinația aleasă.
    def _update_patrol(
        self,
        screen_width,
        screen_height,
    ):
        self.decision_timer -= 1
        distance_x = self.target_x - self.x
        distance_y = self.target_y - self.y
        distance = math.hypot(
            distance_x,
            distance_y,
        )

        if (
            distance < 18
            or self.decision_timer <= 0
        ):
            self._choose_new_target(
                screen_width,
                screen_height,
            )
            distance_x = self.target_x - self.x
            distance_y = self.target_y - self.y
            distance = max(
                1.0,
                math.hypot(
                    distance_x,
                    distance_y,
                ),
            )

        desired_velocity_x = (
            distance_x / distance
        ) * self.patrol_speed
        desired_velocity_y = (
            distance_y / distance
        ) * self.patrol_speed

        # Steering-ul evită schimbările bruște de direcție.
        steering_strength = (
            0.075
            if self.enemy_type == "scout"
            else 0.045
        )
        self.velocity_x += (
            desired_velocity_x - self.velocity_x
        ) * steering_strength
        self.velocity_y += (
            desired_velocity_y - self.velocity_y
        ) * steering_strength

        self.x += self.velocity_x
        self.y += self.velocity_y

        # Oscilația discretă face navele să pară active chiar și la viraj.
        self.x += math.sin(
            self.movement_age * 0.035
            + self.wander_phase
        ) * 0.16

    # Alege o destinație nouă potrivită tipului de inamic.
    def _choose_new_target(
        self,
        screen_width,
        screen_height,
    ):
        horizontal_margin = 28
        maximum_x = max(
            horizontal_margin,
            screen_width
            - self.image.get_width()
            - horizontal_margin,
        )

        if self.enemy_type == "scout":
            minimum_y = 55
            maximum_y = min(
                390,
                screen_height
                - self.image.get_height()
                - 135,
            )
        elif self.enemy_type == "tank":
            minimum_y = 45
            maximum_y = min(
                210,
                screen_height
                - self.image.get_height()
                - 180,
            )
        else:
            minimum_y = 55
            maximum_y = min(
                325,
                screen_height
                - self.image.get_height()
                - 150,
            )

        self.target_x = float(
            random.randint(
                horizontal_margin,
                int(maximum_x),
            )
        )
        self.target_y = float(
            random.randint(
                minimum_y,
                int(maximum_y),
            )
        )
        self.decision_timer = random.randint(
            *self.decision_range
        )

    # Păstrează nava inamică în zona superioară a luptei.
    def _keep_inside_combat_area(
        self,
        screen_width,
        screen_height,
    ):
        maximum_x = (
            screen_width
            - self.image.get_width()
        )
        maximum_y = (
            screen_height
            - self.image.get_height()
            - 105
        )

        if self.x < 0:
            self.x = 0.0
            self.velocity_x = abs(
                self.velocity_x
            )
        elif self.x > maximum_x:
            self.x = float(maximum_x)
            self.velocity_x = -abs(
                self.velocity_x
            )

        if (
            self.movement_state == "patrolling"
            and self.y < 35
        ):
            self.y = 35.0
            self.velocity_y = abs(
                self.velocity_y
            )
        elif (
            self.movement_state == "patrolling"
            and self.y > maximum_y
        ):
            self.y = float(maximum_y)
            self.velocity_y = -abs(
                self.velocity_y
            )

    # Creează și actualizează particulele motoarelor.
    def update_engine(self):
        if random.randint(1, 3) == 1:
            if self.enemy_type == "elite":
                engine_color = (185, 65, 255)
            elif self.enemy_type == "scout":
                engine_color = (255, 40, 40)
            elif self.enemy_type == "tank":
                engine_color = (50, 255, 90)
            else:
                engine_color = (70, 130, 255)

            self.engine_particles.append(
                {
                    "x": (
                        self.x
                        + self.image.get_width()
                        // 2
                    ),
                    "y": self.y - 5,
                    "size": random.randint(3, 7),
                    "life": random.randint(15, 25),
                    "color": engine_color,
                }
            )

        for particle in self.engine_particles[:]:
            particle["y"] -= 3
            particle["life"] -= 1

            if particle["life"] <= 0:
                self.engine_particles.remove(
                    particle
                )

    # Scade viața inamicului și pornește flash-ul de impact.
    def take_damage(self):
        self.health -= 1
        self.hit_flash = 10
        self.health_bar_timer = 75

    # Returnează True dacă inamicul nu mai are viață.
    def is_dead(self):
        return self.health <= 0

    # Desenează particulele motoarelor și imaginea navei.
    def draw(self, screen):
        for particle in self.engine_particles:
            fade = particle["life"] / 25
            glow_color = (
                int(particle["color"][0] * 0.5),
                int(particle["color"][1] * 0.5),
                int(particle["color"][2] * 0.5),
            )
            energy_color = (
                int(particle["color"][0] * fade),
                int(particle["color"][1] * fade),
                int(particle["color"][2] * fade),
            )

            pygame.draw.circle(
                screen,
                glow_color,
                (
                    int(particle["x"]),
                    int(particle["y"]),
                ),
                particle["size"] * 3,
            )
            pygame.draw.circle(
                screen,
                energy_color,
                (
                    int(particle["x"]),
                    int(particle["y"]),
                ),
                particle["size"],
            )

        if self.hit_flash > 0:
            flash_image = self.image.copy()
            flash_image.fill(
                (255, 255, 255, 180),
                special_flags=(
                    pygame.BLEND_RGBA_MULT
                ),
            )
            screen.blit(
                flash_image,
                (
                    int(self.x),
                    int(self.y),
                ),
            )
            self.hit_flash -= 1
        else:
            screen.blit(
                self.image,
                (
                    int(self.x),
                    int(self.y),
                ),
            )

        if self.enemy_type == "elite":
            self._draw_elite_status(screen)
        elif self.health_bar_timer > 0 and self.max_health > 1:
            self._draw_normal_health(screen)

    # Afișează discret rezistența suplimentară numai după ce nava este lovită.
    def _draw_normal_health(self, screen):
        bar_width = min(62, max(34, self.rect.width // 3))
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = max(6, self.rect.top + 18)
        health_ratio = max(
            0.0,
            min(1.0, self.health / self.max_health),
        )

        pygame.draw.rect(
            screen,
            (25, 14, 35),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=2,
        )
        pygame.draw.rect(
            screen,
            (85, 220, 255),
            (
                bar_x,
                bar_y,
                int(bar_width * health_ratio),
                bar_height,
            ),
            border_radius=2,
        )
        pygame.draw.rect(
            screen,
            (205, 240, 255),
            (bar_x, bar_y, bar_width, bar_height),
            1,
            border_radius=2,
        )

    # Afiseaza viata elitei si energia care se strange inaintea atacului.
    def _draw_elite_status(self, screen):
        bar_width = 150
        bar_height = 9
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = max(12, self.rect.top + 24)
        health_ratio = max(0.0, self.health / self.max_health)

        pygame.draw.rect(
            screen,
            (25, 10, 38),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=4,
        )
        pygame.draw.rect(
            screen,
            (180, 55, 245),
            (
                bar_x,
                bar_y,
                int(bar_width * health_ratio),
                bar_height,
            ),
            border_radius=4,
        )
        pygame.draw.rect(
            screen,
            (235, 185, 255),
            (bar_x, bar_y, bar_width, bar_height),
            1,
            border_radius=4,
        )

        if self.elite_charge_timer <= 0:
            return

        charge_progress = 1.0 - (
            self.elite_charge_timer
            / self.elite_charge_duration
        )
        core_position = (
            self.rect.centerx,
            int(self.rect.centery + 10),
        )
        outer_radius = int(14 + charge_progress * 18)
        pygame.draw.circle(
            screen,
            (115, 35, 175),
            core_position,
            outer_radius,
            3,
        )
        pygame.draw.circle(
            screen,
            (245, 210, 255),
            core_position,
            max(4, int(5 + charge_progress * 7)),
        )
