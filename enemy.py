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
        difficulty_stage=1,
    ):
        self.x = float(x)
        self.y = float(y)
        self.enemy_type = enemy_type
        self.difficulty_wave = max(1, int(difficulty_wave))
        self.difficulty_stage = max(1, int(difficulty_stage))
        self.shield_radius = 0
        self.shield_hit_timer = 0
        self.shield_impact_position = None
        self.shield_label_font = None
        self.phase_state = "visible"
        self.phase_cooldown = 0
        self.phase_timer = 0
        self.phase_charge_duration = 48
        self.phase_hidden_duration = 32
        self.phase_materialize_duration = 24
        self.phase_attack_pending = False
        self.phase_label_font = None

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

        elif self.enemy_type == "shield_carrier":
            image_path = (
                enemies_folder
                / "enemy_alien_shield_carrier.png"
            )
            image_size = (230, 238)
            self.entry_speed = 1.85
            self.patrol_speed = 1.30
            self.health = 14
            self.points = 400
            self.decision_range = (145, 230)
            self.shield_radius = 245
            self.shield_label_font = pygame.font.Font(None, 17)

        elif self.enemy_type == "phase_hunter":
            image_path = (
                enemies_folder
                / "enemy_alien_phase_hunter.png"
            )
            image_size = (178, 190)
            self.entry_speed = 3.15
            self.patrol_speed = 2.75
            self.health = 6
            self.points = 300
            self.decision_range = (75, 135)
            self.phase_cooldown = random.randint(180, 270)
            self.phase_label_font = pygame.font.Font(None, 17)

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
            elif self.enemy_type == "shield_carrier":
                self.health += min(6, wave_progress // 2)
            elif self.enemy_type == "phase_hunter":
                self.health += min(4, wave_progress // 3)
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

        # Stage 2+ accelerează clar aceleași nave înainte să introducem noile
        # clase de inamici. Limitările păstrează tiparele încă evitabile.
        stage_progress = self.difficulty_stage - 1
        movement_multiplier *= min(
            2.0,
            1.0 + stage_progress * 0.25,
        )
        self.attack_cooldown_scale = max(
            0.46,
            self.attack_cooldown_scale
            / (1.0 + stage_progress * 0.35),
        )
        self.projectile_speed_multiplier = min(
            1.75,
            self.projectile_speed_multiplier
            * (1.0 + stage_progress * 0.15),
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
            if self.enemy_type in (
                "elite",
                "shield_carrier",
                "phase_hunter",
            )
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

        if self.enemy_type == "shield_carrier":
            return random.randint(55, 125)

        if self.enemy_type == "phase_hunter":
            return random.randint(85, 220)

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
        if self.shield_hit_timer > 0:
            self.shield_hit_timer -= 1
            if self.shield_hit_timer == 0:
                self.shield_impact_position = None
        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1

        if (
            self.enemy_type == "phase_hunter"
            and self.movement_state == "patrolling"
        ):
            self._update_phase_cycle(
                screen_width,
                screen_height,
            )

        if self.movement_state == "departing":
            self._update_departure()
        elif self.movement_state == "entering":
            self._update_entry(
                screen_width,
                screen_height,
            )
        elif self.phase_state not in (
            "phased",
            "materializing",
        ):
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

    # Phase Hunter-ul avertizează, dispare, schimbă poziția și reapare.
    def _update_phase_cycle(self, screen_width, screen_height):
        if self.phase_state == "visible":
            self.phase_cooldown -= 1
            if self.phase_cooldown <= 0:
                self.phase_state = "charging"
                self.phase_timer = self.phase_charge_duration
            return

        self.phase_timer -= 1

        if self.phase_state == "charging" and self.phase_timer <= 0:
            self.phase_state = "phased"
            self.phase_timer = self.phase_hidden_duration
            self._choose_phase_destination(
                screen_width,
                screen_height,
            )
            return

        if self.phase_state == "phased" and self.phase_timer <= 0:
            self.phase_state = "materializing"
            self.phase_timer = self.phase_materialize_duration
            return

        if self.phase_state == "materializing" and self.phase_timer <= 0:
            self.phase_state = "visible"
            self.phase_attack_pending = True
            self.phase_cooldown = self.get_attack_delay(260, 360)
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self._choose_new_target(screen_width, screen_height)

    # Preferă un salt suficient de lung ca teleportarea să fie recognoscibilă.
    def _choose_phase_destination(self, screen_width, screen_height):
        margin_x = 55
        maximum_x = max(
            margin_x,
            screen_width - self.image.get_width() - margin_x,
        )
        minimum_y = 70
        maximum_y = max(
            minimum_y,
            min(
                340,
                screen_height - self.image.get_height() - 145,
            ),
        )
        old_center = self.rect.center
        destination = (self.x, self.y)

        for _ in range(8):
            candidate_x = random.randint(margin_x, int(maximum_x))
            candidate_y = random.randint(minimum_y, int(maximum_y))
            candidate_center = (
                candidate_x + self.image.get_width() // 2,
                candidate_y + self.image.get_height() // 2,
            )
            destination = (float(candidate_x), float(candidate_y))
            if math.dist(old_center, candidate_center) >= 240:
                break

        self.x, self.y = destination
        self.target_x = self.x
        self.target_y = self.y
        self.rect.topleft = (int(self.x), int(self.y))

    def consume_phase_attack(self):
        attack_is_ready = self.phase_attack_pending
        self.phase_attack_pending = False
        return attack_is_ready

    def can_be_hit(self):
        return not (
            self.enemy_type == "phase_hunter"
            and self.phase_state == "phased"
        )

    # Dupa al doilea atac, nava normala paraseste arena prin partea de sus.
    def start_departure(self):
        if (
            self.enemy_type in (
                "elite",
                "shield_carrier",
                "phase_hunter",
            )
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
        elif self.enemy_type in (
            "tank",
            "shield_carrier",
        ):
            minimum_y = 45
            maximum_y = min(
                210,
                screen_height
                - self.image.get_height()
                - 180,
            )
        elif self.enemy_type == "phase_hunter":
            minimum_y = 60
            maximum_y = min(
                310,
                screen_height
                - self.image.get_height()
                - 145,
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
        create_particle = not (
            self.enemy_type == "phase_hunter"
            and self.phase_state == "phased"
        )
        if create_particle and random.randint(1, 3) == 1:
            if self.enemy_type == "elite":
                engine_color = (185, 65, 255)
            elif self.enemy_type == "shield_carrier":
                engine_color = (45, 225, 255)
            elif self.enemy_type == "phase_hunter":
                engine_color = random.choice(
                    ((255, 40, 205), (65, 235, 225))
                )
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
        if not self.can_be_hit():
            return False

        self.health -= 1
        self.hit_flash = 10
        self.health_bar_timer = 75
        return True

    # Câmpul este activ numai după ce nava a intrat suficient în arenă.
    def shield_is_active(self):
        return (
            self.enemy_type == "shield_carrier"
            and self.health > 0
            and self.movement_state != "departing"
            and self.rect.bottom >= 55
        )

    # Memorează ultimul impact pentru pulsația vizuală a câmpului.
    def register_shield_hit(self, impact_position):
        if not self.shield_is_active():
            return

        self.shield_hit_timer = 14
        self.shield_impact_position = (
            int(impact_position[0]),
            int(impact_position[1]),
        )

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

        if self.enemy_type == "phase_hunter":
            self._draw_phase_effects(screen)

        if not self.can_be_hit():
            return

        display_image = self.image
        phase_alpha = self._get_phase_alpha()
        if phase_alpha < 255:
            display_image = self.image.copy()
            display_image.set_alpha(phase_alpha)

        if self.hit_flash > 0:
            flash_image = display_image.copy()
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
                display_image,
                (
                    int(self.x),
                    int(self.y),
                ),
            )

        if self.enemy_type == "elite":
            self._draw_elite_status(screen)
        elif self.enemy_type == "shield_carrier":
            self._draw_shield_carrier_status(screen)
        elif self.enemy_type == "phase_hunter":
            self._draw_phase_hunter_status(screen)
        elif self.health_bar_timer > 0 and self.max_health > 1:
            self._draw_normal_health(screen)

    def _get_phase_alpha(self):
        if self.enemy_type != "phase_hunter":
            return 255
        if self.phase_state == "charging":
            flicker = (math.sin(self.movement_age * 0.72) + 1.0) / 2.0
            return int(125 + flicker * 120)
        if self.phase_state == "materializing":
            progress = 1.0 - self.phase_timer / self.phase_materialize_duration
            return max(35, min(255, int(255 * progress)))
        if self.phase_state == "phased":
            return 0
        return 255

    # Inelele indică separat încărcarea, destinația și rematerializarea.
    def _draw_phase_effects(self, screen):
        center = self.rect.center
        phase_layer = pygame.Surface(
            screen.get_size(),
            pygame.SRCALPHA,
        )

        if self.phase_state == "charging":
            progress = 1.0 - self.phase_timer / self.phase_charge_duration
            radius = int(75 - progress * 38)
            rotation = self.movement_age * 0.17
            color = (255, 45, 210, int(110 + progress * 125))
            for segment in range(6):
                start = rotation + segment * math.tau / 6
                arc_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
                arc_rect.center = center
                pygame.draw.arc(
                    phase_layer,
                    color,
                    arc_rect,
                    start,
                    start + 0.48,
                    4,
                )
            pygame.draw.circle(
                phase_layer,
                (65, 235, 225, int(55 + progress * 90)),
                center,
                max(14, radius - 12),
                2,
            )

        elif self.phase_state in ("phased", "materializing"):
            if self.phase_state == "phased":
                progress = 0.15
                alpha = 80
            else:
                progress = 1.0 - (
                    self.phase_timer / self.phase_materialize_duration
                )
                alpha = int(90 + progress * 150)

            outer_radius = int(70 - progress * 35)
            pygame.draw.circle(
                phase_layer,
                (15, 5, 32, min(165, alpha)),
                center,
                max(12, outer_radius - 9),
            )
            for ring_index, ring_color in enumerate(
                ((65, 240, 225), (255, 45, 210))
            ):
                radius = max(12, outer_radius - ring_index * 13)
                pygame.draw.circle(
                    phase_layer,
                    (*ring_color, alpha),
                    center,
                    radius,
                    3,
                )
            pygame.draw.line(
                phase_layer,
                (220, 255, 255, alpha),
                (center[0], center[1] - outer_radius),
                (center[0], center[1] + outer_radius),
                2,
            )

        screen.blit(phase_layer, (0, 0))

    def _draw_phase_hunter_status(self, screen):
        if self.phase_state == "phased":
            return

        bar_width = 96
        bar_height = 6
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = max(9, self.rect.top + 12)
        health_ratio = max(0.0, min(1.0, self.health / self.max_health))
        label = self.phase_label_font.render(
            "PHASE HUNTER",
            True,
            (255, 115, 225),
        )
        screen.blit(
            label,
            (self.rect.centerx - label.get_width() // 2, bar_y - 15),
        )
        pygame.draw.rect(
            screen,
            (35, 5, 48),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (240, 45, 195),
            (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (90, 240, 225),
            (bar_x, bar_y, bar_width, bar_height),
            1,
            border_radius=3,
        )

    # Shield Carrier-ul rămâne identificabil chiar înainte de primul impact.
    def _draw_shield_carrier_status(self, screen):
        bar_width = 118
        bar_height = 7
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = max(9, self.rect.top + 17)
        health_ratio = max(
            0.0,
            min(1.0, self.health / self.max_health),
        )

        label = self.shield_label_font.render(
            "SHIELD CARRIER",
            True,
            (130, 235, 255),
        )
        screen.blit(
            label,
            (
                self.rect.centerx - label.get_width() // 2,
                bar_y - 16,
            ),
        )
        pygame.draw.rect(
            screen,
            (7, 25, 45),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (45, 215, 255),
            (
                bar_x,
                bar_y,
                int(bar_width * health_ratio),
                bar_height,
            ),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (195, 250, 255),
            (bar_x, bar_y, bar_width, bar_height),
            1,
            border_radius=3,
        )

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
