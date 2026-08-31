import math
import random

import pygame


# Proiectil special folosit exclusiv de bossul final.
class BossProjectile:

    # Configureaza pozitia, directia si comportamentul proiectilului.
    def __init__(self, x, y, angle, speed, projectile_type="plasma"):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.speed = float(speed)
        self.projectile_type = projectile_type
        self.age = 0
        self.trail = []
        self.visual_rotation = random.uniform(0, math.tau)
        self.spin_direction = random.choice((-1, 1))

        if projectile_type == "heavy":
            self.radius = 13
            self.color = (255, 80, 45)
            self.damage = 1
        elif projectile_type == "seeker":
            self.radius = 9
            self.color = (235, 65, 255)
            self.damage = 1
        elif projectile_type == "core":
            self.radius = 8
            self.color = (255, 45, 110)
            self.damage = 1
        elif projectile_type == "phase":
            self.radius = 8
            self.color = (65, 235, 225)
            self.damage = 1
        else:
            self.radius = 7
            self.color = (255, 120, 80)
            self.damage = 1

        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.rect.center = (int(self.x), int(self.y))

    # Deplaseaza proiectilul si curbeaza usor proiectilele de urmarire.
    def update(self, player_rect):
        self.age += 1

        # Rachetele de urmarire corecteaza traiectoria numai pentru o perioada
        # scurta. Dupa aceea continua drept, iar jucatorul le poate depasi.
        if self.projectile_type == "seeker" and self.age <= 90:
            desired_angle = math.atan2(
                player_rect.centery - self.y,
                player_rect.centerx - self.x,
            )
            difference = (
                desired_angle - self.angle + math.pi
            ) % math.tau - math.pi
            maximum_turn = 0.018
            self.angle += max(
                -maximum_turn,
                min(maximum_turn, difference),
            )

        # Proiectilele nucleului au o traiectorie usor curbata.
        if self.projectile_type == "core":
            curve_direction = -1 if self.age % 240 < 120 else 1
            self.angle += 0.0025 * curve_direction

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.rect.center = (int(self.x), int(self.y))

        if self.age % 2 == 0:
            trail_lifetime = {
                "heavy": 20,
                "seeker": 18,
                "core": 16,
                "phase": 20,
                "plasma": 14,
            }.get(self.projectile_type, 14)
            self.trail.append(
                [self.x, self.y, trail_lifetime, trail_lifetime]
            )

        for trail_point in self.trail[:]:
            trail_point[2] -= 1
            if trail_point[2] <= 0:
                self.trail.remove(trail_point)

    # Elimina proiectilul dupa ce paraseste complet arena.
    def is_off_screen(self, screen_width, screen_height):
        margin = 80
        return (
            self.x < -margin
            or self.x > screen_width + margin
            or self.y < -margin
            or self.y > screen_height + margin
        )

    # Returnează axele proiectilului pentru un desen orientat după traiectorie.
    def _direction_axes(self):
        direction = (math.cos(self.angle), math.sin(self.angle))
        perpendicular = (-direction[1], direction[0])
        return direction, perpendicular

    @staticmethod
    def _point(center, direction, perpendicular, forward, side=0):
        return (
            int(center[0] + direction[0] * forward + perpendicular[0] * side),
            int(center[1] + direction[1] * forward + perpendicular[1] * side),
        )

    # Desenează o coadă graduală care nu modifică hitbox-ul proiectilului.
    def _draw_trail(self, screen, trail_color, maximum_radius):
        for trail_x, trail_y, trail_life, trail_maximum in self.trail:
            life_ratio = trail_life / trail_maximum
            color = tuple(
                max(2, int(channel * life_ratio * 0.48))
                for channel in trail_color
            )
            pygame.draw.circle(
                screen,
                color,
                (int(trail_x), int(trail_y)),
                max(1, int(maximum_radius * life_ratio)),
            )

    # Desenează semnătura vizuală proprie fiecărui atac al bossului.
    def draw(self, screen):
        center = self.rect.center
        direction, perpendicular = self._direction_axes()

        if self.projectile_type == "heavy":
            self._draw_heavy(screen, center, direction, perpendicular)
        elif self.projectile_type == "seeker":
            self._draw_seeker(screen, center, direction, perpendicular)
        elif self.projectile_type == "core":
            self._draw_core_shard(screen, center, direction, perpendicular)
        elif self.projectile_type == "phase":
            self._draw_phase_shard(screen, center, direction, perpendicular)
        else:
            self._draw_plasma(screen, center, direction, perpendicular)

    # Proiectil standard: bolt crimson cu vârf și aripioare energetice.
    def _draw_plasma(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (255, 65, 85), 6)
        tip = self._point(center, direction, perpendicular, 13)
        tail = self._point(center, direction, perpendicular, -10)
        left = self._point(center, direction, perpendicular, -2, 7)
        right = self._point(center, direction, perpendicular, -2, -7)

        pygame.draw.line(screen, (65, 3, 22), tail, tip, 13)
        pygame.draw.polygon(screen, (185, 20, 55), [tip, left, tail, right])
        pygame.draw.line(screen, (255, 75, 100), tail, tip, 6)
        pygame.draw.line(screen, (255, 235, 240), center, tip, 2)
        pygame.draw.circle(screen, (255, 250, 250), center, 3)

    # Salva grea: torpilă încinsă, înconjurată de plăci rotative.
    def _draw_heavy(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (255, 90, 25), 10)
        pulse = 1 + int((math.sin(self.age * 0.22) + 1) * 1.5)
        pygame.draw.circle(screen, (70, 12, 4), center, 17 + pulse)
        pygame.draw.circle(screen, (185, 35, 12), center, 13 + pulse)
        pygame.draw.circle(screen, (255, 105, 25), center, 9)
        pygame.draw.circle(screen, (255, 238, 170), center, 4)

        rotation = self.visual_rotation + self.age * 0.13 * self.spin_direction
        for plate_index in range(4):
            angle = rotation + plate_index * math.pi / 2
            plate_center = (
                int(center[0] + math.cos(angle) * 17),
                int(center[1] + math.sin(angle) * 17),
            )
            tangent = (-math.sin(angle), math.cos(angle))
            pygame.draw.line(
                screen,
                (255, 155, 45),
                (
                    int(plate_center[0] - tangent[0] * 5),
                    int(plate_center[1] - tangent[1] * 5),
                ),
                (
                    int(plate_center[0] + tangent[0] * 5),
                    int(plate_center[1] + tangent[1] * 5),
                ),
                3,
            )

    # Seeker: ochi violet cu reticul rotativ și coadă curbată vizibilă.
    def _draw_seeker(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (210, 55, 255), 7)
        pygame.draw.circle(screen, (35, 5, 70), center, 14)
        pygame.draw.circle(screen, (105, 20, 175), center, 11)

        rotation = self.visual_rotation + self.age * 0.16 * self.spin_direction
        orbit_rect = pygame.Rect(0, 0, 30, 30)
        orbit_rect.center = center
        pygame.draw.arc(
            screen, (220, 85, 255), orbit_rect, rotation, rotation + 2.1, 2
        )
        pygame.draw.arc(
            screen,
            (95, 70, 255),
            orbit_rect,
            rotation + math.pi,
            rotation + math.pi + 2.1,
            2,
        )

        pupil = self._point(center, direction, perpendicular, 4)
        pygame.draw.circle(screen, (245, 165, 255), center, 7)
        pygame.draw.circle(screen, (255, 250, 255), pupil, 3)

        for side in (-1, 1):
            fin_start = self._point(center, direction, perpendicular, -3, side * 8)
            fin_end = self._point(center, direction, perpendicular, -10, side * 13)
            pygame.draw.line(screen, (175, 65, 255), fin_start, fin_end, 3)

    # Faza finală: fragment instabil din nucleul Dead Star.
    def _draw_core_shard(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (255, 30, 130), 7)
        tip = self._point(center, direction, perpendicular, 14)
        tail = self._point(center, direction, perpendicular, -12)
        left = self._point(center, direction, perpendicular, -2, 8)
        right = self._point(center, direction, perpendicular, -2, -8)

        pygame.draw.circle(screen, (65, 3, 38), center, 13)
        pygame.draw.polygon(screen, (170, 15, 95), [tip, left, tail, right])
        pygame.draw.polygon(
            screen,
            (255, 55, 145),
            [
                tip,
                self._point(center, direction, perpendicular, 0, 4),
                tail,
                self._point(center, direction, perpendicular, 0, -4),
            ],
        )
        pygame.draw.line(screen, (255, 230, 245), center, tip, 3)

        spark_angle = self.visual_rotation + self.age * 0.21
        for spark_index in range(3):
            angle = spark_angle + spark_index * math.tau / 3
            spark = (
                int(center[0] + math.cos(angle) * 15),
                int(center[1] + math.sin(angle) * 15),
            )
            pygame.draw.circle(screen, (255, 145, 205), spark, 2)

    # Proiectilul Phase alternează cyan și magenta ca o ruptură dimensională.
    def _draw_phase_shard(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (255, 45, 205), 8)
        tip = self._point(center, direction, perpendicular, 15)
        tail = self._point(center, direction, perpendicular, -13)
        left = self._point(center, direction, perpendicular, -2, 9)
        right = self._point(center, direction, perpendicular, -2, -9)

        pygame.draw.circle(screen, (35, 3, 60), center, 14)
        pygame.draw.polygon(
            screen,
            (225, 35, 190),
            [tip, left, tail, right],
        )
        pygame.draw.line(screen, (55, 235, 225), tail, tip, 6)
        pygame.draw.line(screen, (240, 255, 255), center, tip, 2)

        echo_distance = 11 + int(
            3 * abs(math.sin(self.age * 0.24))
        )
        for side in (-1, 1):
            echo_center = self._point(
                center,
                direction,
                perpendicular,
                -3,
                side * echo_distance,
            )
            pygame.draw.circle(
                screen,
                (55, 175, 180),
                echo_center,
                3,
                1,
            )


# Raza verticala are mai intai o avertizare, apoi devine periculoasa.
class BossLaser:

    def __init__(
        self,
        center_x,
        screen_height,
        width=62,
        warning_duration=70,
        active_duration=42,
    ):
        self.center_x = int(center_x)
        self.screen_height = screen_height
        self.width = int(width)
        # Aproximativ o secundă de avertizare: suficient pentru reacție,
        # dar nu atât de lung încât laserul să devină o pauză gratuită.
        self.warning_timer = int(warning_duration)
        self.active_timer = int(active_duration)
        self.warning_duration = int(warning_duration)
        self.active_duration = int(active_duration)
        self.finished = False
        self.animation_timer = 0
        self.rect = pygame.Rect(
            self.center_x - self.width // 2,
            0,
            self.width,
            self.screen_height,
        )

    # Numara separat avertizarea si timpul in care laserul produce damage.
    def update(self):
        self.animation_timer += 1

        if self.warning_timer > 0:
            self.warning_timer -= 1
        elif self.active_timer > 0:
            self.active_timer -= 1
        else:
            self.finished = True

    def is_dangerous(self):
        return self.warning_timer <= 0 and self.active_timer > 0

    # Desenează culoarul de avertizare sau coloana energetică activă.
    def draw(self, screen):
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()),
            pygame.SRCALPHA,
        )

        if self.warning_timer > 0:
            warning_progress = 1.0 - (
                self.warning_timer / max(1, self.warning_duration)
            )
            pulse = 42 + int(
                65 * abs(math.sin(self.animation_timer * 0.22))
            )

            # Culoarul transparent arată exact zona periculoasă.
            pygame.draw.rect(
                overlay,
                (255, 25, 70, 18 + int(28 * warning_progress)),
                self.rect,
            )
            pygame.draw.rect(
                overlay,
                (255, 70, 105, 75 + int(70 * warning_progress)),
                self.rect,
                2,
            )

            # Linia de scanare pulsează tot mai rapid înainte de activare.
            line_width = 2 + int(warning_progress * 4)
            pygame.draw.line(
                overlay,
                (255, 105, 135, pulse + int(70 * warning_progress)),
                (self.center_x, 0),
                (self.center_x, self.screen_height),
                line_width,
            )

            # Marcajele descendente elimină aspectul unei simple linii Pygame.
            marker_spacing = 74
            marker_offset = (self.animation_timer * 5) % marker_spacing
            half_width = self.width // 2
            for marker_y in range(
                int(marker_offset) - marker_spacing,
                self.screen_height + marker_spacing,
                marker_spacing,
            ):
                for side in (-1, 1):
                    edge_x = self.center_x + side * half_width
                    points = [
                        (edge_x, marker_y),
                        (edge_x - side * 11, marker_y + 9),
                        (edge_x, marker_y + 18),
                    ]
                    pygame.draw.lines(
                        overlay,
                        (255, 125, 145, 130),
                        False,
                        points,
                        2,
                    )

            # Încărcarea din partea de sus sugerează sursa din afara arenei.
            charge_radius = int(10 + warning_progress * self.width * 0.62)
            pygame.draw.circle(
                overlay,
                (255, 35, 95, 38),
                (self.center_x, 0),
                charge_radius,
            )
            pygame.draw.circle(
                overlay,
                (255, 185, 210, 185),
                (self.center_x, 2),
                max(4, int(5 + warning_progress * 8)),
            )
        else:
            active_progress = 1.0 - (
                self.active_timer / max(1, self.active_duration)
            )
            beam_pulse = 0.86 + 0.14 * math.sin(
                self.animation_timer * 0.42
            )

            # Marginea întunecată separă raza de fundal și de boss.
            pygame.draw.rect(
                overlay,
                (50, 0, 25, 190),
                self.rect.inflate(12, 0),
            )
            pygame.draw.rect(
                overlay,
                (255, 15, 70, int(125 * beam_pulse)),
                self.rect,
            )

            middle_rect = self.rect.inflate(-int(self.width * 0.42), 0)
            pygame.draw.rect(
                overlay,
                (255, 95, 145, int(205 * beam_pulse)),
                middle_rect,
            )
            inner_rect = self.rect.inflate(-int(self.width * 0.70), 0)
            pygame.draw.rect(
                overlay,
                (255, 235, 245, 245),
                inner_rect,
            )
            pygame.draw.line(
                overlay,
                (255, 255, 255, 255),
                (self.center_x, 0),
                (self.center_x, self.screen_height),
                max(3, int(self.width * 0.08)),
            )

            # Benzi de energie coboară prin fascicul cât timp acesta este activ.
            band_spacing = 92
            band_offset = (self.animation_timer * 13) % band_spacing
            for band_y in range(
                int(band_offset) - band_spacing,
                self.screen_height + band_spacing,
                band_spacing,
            ):
                band_left = (
                    self.center_x - self.width // 2 + 5,
                    band_y,
                )
                band_center = (self.center_x, band_y + 9)
                band_right = (
                    self.center_x + self.width // 2 - 5,
                    band_y,
                )
                pygame.draw.lines(
                    overlay,
                    (255, 205, 225, 175),
                    False,
                    [band_left, band_center, band_right],
                    3,
                )

            # Sursa de sus se dilată la pornire și rămâne conectată cu raza.
            source_glow = pygame.Surface(
                (self.width * 3, 105),
                pygame.SRCALPHA,
            )
            source_center_x = source_glow.get_width() // 2
            source_scale = 1.22 - active_progress * 0.12
            for glow_index in range(7, 0, -1):
                glow_width = int(
                    (self.width + glow_index * 18) * source_scale
                )
                glow_alpha = max(8, 82 - glow_index * 8)
                pygame.draw.ellipse(
                    source_glow,
                    (255, 65, 120, glow_alpha),
                    (
                        source_center_x - glow_width // 2,
                        -45 + glow_index * 4,
                        glow_width,
                        90,
                    ),
                )
            pygame.draw.circle(
                source_glow,
                (255, 245, 250, 235),
                (source_center_x, 8),
                max(6, self.width // 7),
            )
            overlay.blit(
                source_glow,
                (
                    self.center_x
                    - source_glow.get_width() // 2,
                    0,
                ),
            )

        screen.blit(overlay, (0, 0))


# Nava-fortareata care incheie lupta din sistemul Dead Star.
class Boss:

    def __init__(
        self,
        screen_width=1280,
        screen_height=720,
        difficulty_stage=1,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.difficulty_stage = max(1, int(difficulty_stage))
        stage_progress = self.difficulty_stage - 1
        # Stage 2 introduce deja atacul dimensional, asa ca saltul brut al
        # tuturor statisticilor il facea disproportionat de greu. Il pastram
        # drept primul examen serios, iar curba completa incepe din Stage 3.
        if self.difficulty_stage == 2:
            self.stage_health_multiplier = 1.25
            self.stage_attack_rate = 1.12
            self.stage_projectile_speed = 1.07
            self.stage_movement_speed = 1.07
        else:
            self.stage_health_multiplier = 1.0 + stage_progress * 0.35
            self.stage_attack_rate = min(
                2.0,
                1.0 + stage_progress * 0.20,
            )
            self.stage_projectile_speed = min(
                1.65,
                1.0 + stage_progress * 0.12,
            )
            self.stage_movement_speed = min(
                1.60,
                1.0 + stage_progress * 0.12,
            )
        # Dimensiunile pastreaza proportiile noului sprite lat de final boss.
        self.width = 620
        self.height = 350
        self.x = float(screen_width // 2 - self.width // 2)
        self.y = float(-self.height - 35)
        self.target_y = 20.0
        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )
        self.hitbox = self.rect.copy()

        # Bossul are trei faze egale ca viata.
        # 1200 HP inseamna de sase ori viata vechiului boss, fara ca lupta
        # sa ceara sute de apasari inutile pe SPACE.
        self.max_hp = int(
            round(1200 * self.stage_health_multiplier)
        )
        self.hp = self.max_hp
        self.phase_two_threshold = int(self.max_hp * 2 / 3)
        self.phase_three_threshold = int(self.max_hp / 3)
        self.phase = 1
        self.phase_two = False
        self.phase_three = False
        self.state = "entering"
        self.intro = True
        self.intro_timer = 240
        self.transition_timer = 0
        self.phase_banner_timer = 0
        self.hit_timer = 0
        self.animation_timer = 0
        self.movement_timer = 0
        self.primary_attack_timer = 0
        self.special_attack_timer = 0
        self.laser_attack_timer = 0
        self.phase_attack_timer = 0
        self.phase_attack_active = False
        self.phase_attack_charge_timer = 0
        self.phase_attack_charge_duration = 0
        self.phase_attack_salvos_remaining = 0
        self.phase_attack_total_salvos = 0
        self.phase_attack_salvo_timer = 0
        self.phase_attack_linger_timer = 0
        self.phase_attack_alternate = False
        self.phase_locked_target = (screen_width // 2, screen_height - 120)
        self.phase_exit_portals = []
        self.core_burst_alternate = False

        # In faza a doua, corpul este protejat de doua generatoare.
        self.generator_max_hp = int(
            round(120 * self.stage_health_multiplier)
        )
        self.generator_hp = [0, 0]
        self.generator_rects = [
            pygame.Rect(0, 0, 110, 110),
            pygame.Rect(0, 0, 110, 110),
        ]

        self.lasers = []
        self.engine_particles = []
        self.pending_explosions = []
        self.death_timer = 0

        self.title_font = pygame.font.Font(None, 34)
        self.phase_font = pygame.font.Font(None, 28)
        self.warning_font = pygame.font.Font(None, 66)

        self.base_image = self._load_boss_image()
        self.image = self.base_image
        self._update_rectangles()

    # Foloseste imaginea existenta; creeaza un fallback daca asset-ul lipseste.
    def _load_boss_image(self):
        try:
            image = pygame.image.load(
                "assets/images/bosses/"
                "final_boss_sovereign.png"
            ).convert_alpha()
            return pygame.transform.smoothscale(
                image,
                (self.width, self.height),
            )
        except (pygame.error, FileNotFoundError):
            surface = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
            pygame.draw.polygon(
                surface,
                (40, 25, 58),
                [
                    (15, 125),
                    (120, 55),
                    (260, 25),
                    (400, 55),
                    (505, 125),
                    (390, 205),
                    (260, 230),
                    (130, 205),
                ],
            )
            pygame.draw.circle(surface, (255, 45, 100), (260, 125), 48)
            return surface

    # Actualizeaza toate dreptunghiurile de coliziune dupa miscare.
    def _update_rectangles(self):
        self.rect.topleft = (int(self.x), int(self.y))
        # Hitbox-ul este intentionat generos si ajunge pana la partea de jos.
        # Astfel, gloantele lovesc bossul de la distanta si jucatorul nu este
        # obligat sa intre cu propria nava in imaginea lui.
        self.hitbox = pygame.Rect(
            int(self.x + 8),
            int(self.y + 48),
            self.width - 16,
            self.height - 62,
        )
        generator_y = int(self.y + self.height * 0.445)
        self.generator_rects[0].center = (
            int(self.x + self.width * 0.275),
            generator_y,
        )
        self.generator_rects[1].center = (
            int(self.x + self.width * 0.725),
            generator_y,
        )
        self.core_center = (
            int(self.x + self.width // 2),
            int(self.y + self.height * 0.465),
        )

    # Actualizeaza intrarea, miscarea, atacurile si distrugerea finala.
    def update(self, player_rect):
        self.animation_timer += 1
        self._update_engine_particles()

        if self.hit_timer > 0:
            self.hit_timer -= 1
        if self.phase_banner_timer > 0:
            self.phase_banner_timer -= 1

        for laser in self.lasers[:]:
            laser.update()
            if laser.finished:
                self.lasers.remove(laser)

        if self.state == "dying":
            self._update_destruction()
            return []

        if self.state == "defeated":
            return []

        if self.state == "entering":
            self.y += min(2.1, self.target_y - self.y)
            self.intro_timer -= 1

            if self.intro_timer <= 0:
                self.y = self.target_y
                self.state = "active"
                self.intro = False
                self.phase_banner_timer = 150

            self._update_rectangles()
            return []

        self._move_in_arena()

        if self.transition_timer > 0:
            self.transition_timer -= 1
            self._update_rectangles()
            return []

        self._update_rectangles()
        return self._create_attacks(player_rect)

    # Misca bossul lent, dar mai agresiv in faza finala.
    def _move_in_arena(self):
        self.movement_timer += 1
        center_x = self.screen_width / 2 - self.width / 2
        if self.phase == 1:
            amplitude = 205
            movement_speed = 0.007
            vertical_amplitude = 9
        elif self.phase == 2:
            amplitude = 230
            movement_speed = 0.009
            vertical_amplitude = 12
        else:
            amplitude = 270
            movement_speed = 0.012
            vertical_amplitude = 16

        self.x = center_x + math.sin(
            self.movement_timer
            * movement_speed
            * self.stage_movement_speed
        ) * amplitude
        self.y = self.target_y + math.sin(
            self.movement_timer * 0.018
        ) * vertical_amplitude

    # Creeaza atacurile corespunzatoare fazei curente.
    def _create_attacks(self, player_rect):
        new_projectiles = []

        # Atacul dimensional rulează singur, astfel încât liniile de avertizare
        # să nu fie acoperite de lasere sau de alte salve ale bossului.
        if self.phase_attack_active:
            return self._update_phase_portal_attack()

        # În timpul laserului nu lansăm alte atacuri, însă cronometrele lor
        # avansează lent. Astfel rămâne o rută clară de evitare, fără pauza
        # enormă care exista după dispariția razei.
        if self.lasers:
            if self.animation_timer % 2 == 0:
                self.primary_attack_timer += self.stage_attack_rate
            if self.animation_timer % 3 == 0:
                self.special_attack_timer += self.stage_attack_rate
                if self.difficulty_stage >= 2:
                    self.phase_attack_timer += self.stage_attack_rate * 0.5
            return new_projectiles

        self.primary_attack_timer += self.stage_attack_rate
        self.special_attack_timer += self.stage_attack_rate
        self.laser_attack_timer += self.stage_attack_rate
        if self.difficulty_stage >= 2:
            self.phase_attack_timer += self.stage_attack_rate
        desperation = self.hp <= self.max_hp * 0.10

        phase_attack_delay = {
            1: 345,
            2: 305,
            3: 265,
        }[self.phase]
        if (
            self.difficulty_stage >= 2
            and self.phase_attack_timer >= phase_attack_delay
        ):
            self.primary_attack_timer = 0
            self.special_attack_timer = 0
            self.laser_attack_timer = 0
            self._start_phase_portal_attack(player_rect)
            return new_projectiles

        if self.phase == 1:
            # Prima faza introduce mecanica printr-un singur laser.
            if self.laser_attack_timer >= 300:
                self.laser_attack_timer = 0
                self.primary_attack_timer = 0
                self.special_attack_timer = 0
                self._create_laser_attack(player_rect, laser_count=1)
                return new_projectiles

            if self.primary_attack_timer >= 90:
                self.primary_attack_timer = 0
                new_projectiles.extend(
                    self._create_aimed_fan(player_rect, 5, 4.9)
                )
            if self.special_attack_timer >= 225:
                self.special_attack_timer = 0
                new_projectiles.extend(self._create_pincer_salvo())

        elif self.phase == 2:
            # Laserul are prioritate. La pornirea lui, celelalte cronometre sunt
            # resetate pentru a evita o rafala imediat dupa terminarea razei.
            if self.laser_attack_timer >= 255:
                self.laser_attack_timer = 0
                self.primary_attack_timer = 0
                self.special_attack_timer = 0
                self._create_laser_attack(player_rect, laser_count=2)
                return new_projectiles

            if self.primary_attack_timer >= 76:
                self.primary_attack_timer = 0
                new_projectiles.extend(
                    self._create_aimed_fan(player_rect, 7, 5.2)
                )
            if self.special_attack_timer >= 190:
                self.special_attack_timer = 0
                new_projectiles.extend(self._create_pincer_salvo())

        else:
            primary_delay = 46 if desperation else 56
            laser_delay = 190 if desperation else 220

            if self.laser_attack_timer >= laser_delay:
                self.laser_attack_timer = 0
                self.primary_attack_timer = 0
                self.special_attack_timer = 0
                self._create_laser_attack(
                    player_rect,
                    laser_count=3,
                )
                return new_projectiles

            if self.primary_attack_timer >= primary_delay:
                self.primary_attack_timer = 0
                new_projectiles.extend(self._create_core_burst())
            if self.special_attack_timer >= 165:
                self.special_attack_timer = 0
                new_projectiles.extend(
                    self._create_seekers(
                        player_rect,
                        seeker_count=3 if desperation else 2,
                    )
                )

        return new_projectiles

    # Creeaza un evantai orientat spre pozitia curenta a jucatorului.
    def _create_aimed_fan(self, player_rect, bullet_count, speed):
        origin_x, origin_y = self.core_center
        target_angle = math.atan2(
            player_rect.centery - origin_y,
            player_rect.centerx - origin_x,
        )
        spread = 0.18
        start_offset = -(bullet_count - 1) * spread / 2
        return [
            BossProjectile(
                origin_x,
                origin_y + 22,
                target_angle + start_offset + index * spread,
                speed * self.stage_projectile_speed,
                "plasma",
            )
            for index in range(bullet_count)
        ]

    # Tunurile laterale inchid treptat spatiul din centrul arenei.
    def _create_pincer_salvo(self):
        projectiles = []
        cannon_data = [
            (self.x + 135, 0.48),
            (self.x + self.width - 135, 2.66),
        ]

        for cannon_x, base_angle in cannon_data:
            # Patru proiectile pe fiecare parte închid treptat centrul, dar
            # lasă în continuare culoare vizibile spre marginile arenei.
            for offset in (-0.27, -0.09, 0.09, 0.27):
                projectiles.append(
                    BossProjectile(
                        cannon_x,
                        self.y + 205,
                        base_angle + offset,
                        5.0 * self.stage_projectile_speed,
                        "heavy" if abs(offset) < 0.10 else "plasma",
                    )
                )

        return projectiles

    # Nucleul expus lanseaza un semicerc dens, dar cu spatii evitabile.
    def _create_core_burst(self):
        projectiles = []
        origin_x, origin_y = self.core_center

        # Cele două variante mută spațiile sigure de la o salvă la alta,
        # obligând jucătorul să citească tiparul în loc să campeze într-un loc.
        edge_angle = 0.16 if self.core_burst_alternate else 0.29
        self.core_burst_alternate = not self.core_burst_alternate
        bullet_count = 11

        for index in range(bullet_count):
            angle = (
                edge_angle
                + index
                * (math.pi - edge_angle * 2)
                / (bullet_count - 1)
            )
            projectiles.append(
                BossProjectile(
                    origin_x,
                    origin_y + 25,
                    angle,
                    5.2 * self.stage_projectile_speed,
                    "core",
                )
            )

        return projectiles

    # Doua proiectile mov urmaresc nava pentru o perioada limitata.
    def _create_seekers(self, player_rect, seeker_count=2):
        projectiles = []
        sides = (
            (-1, 0, 1)
            if seeker_count >= 3
            else (-1, 1)
        )
        for side in sides:
            start_x = self.core_center[0] + side * 155
            start_y = self.core_center[1] + 18
            target_angle = math.atan2(
                player_rect.centery - start_y,
                player_rect.centerx - start_x,
            )
            projectiles.append(
                BossProjectile(
                    start_x,
                    start_y,
                    target_angle,
                    4.0 * self.stage_projectile_speed,
                    "seeker",
                )
            )
        return projectiles

    # Blochează poziția jucătorului și deschide una sau două ieșiri laterale.
    def _start_phase_portal_attack(self, player_rect):
        self.phase_attack_active = True
        self.phase_attack_charge_duration = max(
            60,
            int(105 / self.stage_attack_rate),
        )
        self.phase_attack_charge_timer = self.phase_attack_charge_duration
        self.phase_attack_total_salvos = 2 + (1 if self.phase == 3 else 0)
        self.phase_attack_salvos_remaining = self.phase_attack_total_salvos
        self.phase_attack_salvo_timer = 0
        self.phase_attack_linger_timer = 34
        self.phase_locked_target = player_rect.center
        self.phase_attack_alternate = not self.phase_attack_alternate
        self.phase_exit_portals = []

        exit_count = 1 if self.difficulty_stage == 2 else 2
        if exit_count == 1:
            exit_x = (
                88
                if self.phase_attack_alternate
                else self.screen_width - 88
            )
            exit_y = max(
                245,
                min(
                    self.screen_height - 185,
                    player_rect.centery - 145,
                ),
            )
            portal_positions = [(exit_x, exit_y)]
        else:
            vertical_shift = 32 if self.phase_attack_alternate else -32
            portal_positions = [
                (82, 285 + vertical_shift),
                (self.screen_width - 82, 390 - vertical_shift),
            ]

        for portal_x, portal_y in portal_positions:
            aim_angle = math.atan2(
                self.phase_locked_target[1] - portal_y,
                self.phase_locked_target[0] - portal_x,
            )
            self.phase_exit_portals.append(
                {
                    "x": float(portal_x),
                    "y": float(portal_y),
                    "angle": aim_angle,
                }
            )

    # După avertizare, fiecare ieșire lansează salve rare și lizibile.
    def _update_phase_portal_attack(self):
        if self.phase_attack_charge_timer > 0:
            self.phase_attack_charge_timer -= 1
            return []

        if self.phase_attack_salvos_remaining > 0:
            if self.phase_attack_salvo_timer > 0:
                self.phase_attack_salvo_timer -= 1
                return []

            projectiles = self._create_phase_portal_salvo()
            self.phase_attack_salvos_remaining -= 1
            self.phase_attack_salvo_timer = max(
                18,
                int(36 / self.stage_attack_rate),
            )
            if self.phase_attack_salvos_remaining == 0:
                self.phase_attack_linger_timer = 36
            return projectiles

        self.phase_attack_linger_timer -= 1
        if self.phase_attack_linger_timer <= 0:
            self.phase_attack_active = False
            self.phase_attack_timer = 0
            self.phase_exit_portals = []
        return []

    def _create_phase_portal_salvo(self):
        projectiles = []
        fired_salvo_index = (
            self.phase_attack_total_salvos
            - self.phase_attack_salvos_remaining
        )
        alternating_offset = (
            -0.045 if fired_salvo_index % 2 == 0 else 0.045
        )
        angle_offsets = (
            (-0.16, 0, 0.16)
            if len(self.phase_exit_portals) == 1
            else (-0.12, 0.12)
        )

        for portal in self.phase_exit_portals:
            for angle_offset in angle_offsets:
                projectiles.append(
                    BossProjectile(
                        portal["x"],
                        portal["y"],
                        portal["angle"]
                        + alternating_offset
                        + angle_offset,
                        4.7 * self.stage_projectile_speed,
                        "phase",
                    )
                )

        return projectiles

    def _cancel_phase_portal_attack(self):
        self.phase_attack_active = False
        self.phase_attack_timer = 0
        self.phase_attack_charge_timer = 0
        self.phase_attack_salvos_remaining = 0
        self.phase_attack_salvo_timer = 0
        self.phase_attack_linger_timer = 0
        self.phase_exit_portals = []

    # Creeaza 1, 2 sau 3 raze in functie de faza curenta a bossului.
    # Prima raza urmareste pozitia jucatorului in momentul avertizarii.
    # Celelalte sunt distribuite uniform, pastrand culoare de evitare.
    def _create_laser_attack(self, player_rect, laser_count=1):
        target_x = max(
            55,
            min(self.screen_width - 55, player_rect.centerx),
        )

        laser_count = max(1, min(3, int(laser_count)))
        spacing = self.screen_width / laser_count
        laser_width = {
            1: 70,
            2: 64,
            3: 58,
        }[laser_count]
        warning_duration = {
            1: 74,
            2: 68,
            3: 62,
        }[laser_count]
        warning_duration = max(
            44,
            int(warning_duration / self.stage_attack_rate),
        )
        active_duration = {
            1: 38,
            2: 42,
            3: 46,
        }[laser_count]

        for laser_index in range(laser_count):
            laser_x = (
                target_x + laser_index * spacing
            ) % self.screen_width
            laser_x = max(
                55,
                min(self.screen_width - 55, laser_x),
            )
            self.lasers.append(
                BossLaser(
                    int(laser_x),
                    self.screen_height,
                    laser_width,
                    warning_duration,
                    active_duration,
                )
            )

    # Verifica daca glontul loveste un generator, scutul sau corpul.
    def hit_by_player(self, bullet_rect, damage=5):
        if self.phase == 2 and self.generators_are_active():
            hit_generator_index = None

            for generator_index, generator_rect in enumerate(
                self.generator_rects
            ):
                if self.generator_hp[generator_index] <= 0:
                    continue

                # Coloana de tinta coboara pana la marginea corpului.
                # Un glont tras de jos poate astfel ajunge la generator
                # fara sa fie absorbit mai intai de dreptunghiul scutului.
                generator_target = pygame.Rect(
                    generator_rect.left,
                    generator_rect.top,
                    generator_rect.width,
                    max(
                        1,
                        self.hitbox.bottom
                        - generator_rect.top,
                    ),
                )
                if not bullet_rect.colliderect(
                    generator_target
                ):
                    continue

                hit_generator_index = generator_index
                break

            collides_with_body = bullet_rect.colliderect(
                self.hitbox
            )
            if (
                hit_generator_index is None
                and not collides_with_body
            ):
                return "miss"

            if self.state != "active" or self.transition_timer > 0:
                return "blocked"

            if hit_generator_index is not None:
                generator_index = hit_generator_index
                generator_rect = self.generator_rects[
                    generator_index
                ]

                self.generator_hp[generator_index] = max(
                    0,
                    self.generator_hp[generator_index] - damage,
                )
                self.hit_timer = 5

                if self.generator_hp[generator_index] == 0:
                    self.pending_explosions.append(generator_rect.center)
                    return "generator_destroyed"
                return "generator_hit"

            if collides_with_body:
                return "shield"
            return "miss"

        if not bullet_rect.colliderect(self.hitbox):
            return "miss"

        if self.state != "active" or self.transition_timer > 0:
            return "blocked"

        self.hp = max(0, self.hp - damage)
        self.hit_timer = 7

        if self.hp <= 0:
            return "destroyed"

        if self.phase == 1 and self.hp <= self.phase_two_threshold:
            self._start_phase_two()
            return "phase_changed"

        if self.phase == 2 and self.hp <= self.phase_three_threshold:
            self._start_phase_three()
            return "phase_changed"

        return "body_hit"

    # Activeaza scutul si cele doua obiective laterale.
    def _start_phase_two(self):
        self.phase = 2
        self.phase_two = True
        self.generator_hp = [
            self.generator_max_hp,
            self.generator_max_hp,
        ]
        self.transition_timer = 150
        self.phase_banner_timer = 180
        self.primary_attack_timer = 0
        self.special_attack_timer = 0
        self.laser_attack_timer = 0
        self._cancel_phase_portal_attack()

    # Expune nucleul si accelereaza toate sistemele de atac.
    def _start_phase_three(self):
        self.phase = 3
        self.phase_three = True
        self.transition_timer = 150
        self.phase_banner_timer = 180
        self.primary_attack_timer = 0
        self.special_attack_timer = 0
        self.laser_attack_timer = 0
        self.lasers.clear()
        self._cancel_phase_portal_attack()

    def generators_are_active(self):
        return any(generator_hp > 0 for generator_hp in self.generator_hp)

    # Porneste o secventa lunga de explozii in locul disparitiei instantanee.
    def begin_destruction(self):
        if self.state in ("dying", "defeated"):
            return
        self.state = "dying"
        self.death_timer = 240
        self.lasers.clear()
        self._cancel_phase_portal_attack()
        self.pending_explosions.extend(
            [
                (self.rect.centerx - 120, self.rect.centery),
                (self.rect.centerx + 120, self.rect.centery),
                self.rect.center,
            ]
        )

    # Produce explozii succesive, apoi marcheaza lupta drept castigata.
    def _update_destruction(self):
        self.death_timer -= 1

        if self.death_timer % 9 == 0:
            self.pending_explosions.append(
                (
                    random.randint(self.rect.left + 35, self.rect.right - 35),
                    random.randint(self.rect.top + 35, self.rect.bottom - 35),
                )
            )

        if self.death_timer == 1:
            for _ in range(12):
                self.pending_explosions.append(
                    (
                        random.randint(self.rect.left, self.rect.right),
                        random.randint(self.rect.top, self.rect.bottom),
                    )
                )

        if self.death_timer <= 0:
            self.state = "defeated"

    # Gameplay-ul consuma fiecare explozie o singura data.
    def consume_explosion_requests(self):
        requests = self.pending_explosions[:]
        self.pending_explosions.clear()
        return requests

    # Creeaza flacari si scantei in functie de faza curenta.
    def _update_engine_particles(self):
        if self.state == "defeated":
            return

        particle_count = 4 if self.phase == 3 else 2
        for _ in range(particle_count):
            engine_x = random.choice(
                [
                    self.x + 135,
                    self.x + self.width // 2,
                    self.x + self.width - 135,
                ]
            )
            self.engine_particles.append(
                {
                    "x": engine_x + random.randint(-8, 8),
                    "y": self.y + 58,
                    "radius": random.randint(3, 8),
                    "life": random.randint(16, 28),
                }
            )

        for particle in self.engine_particles[:]:
            particle["y"] -= random.uniform(1.8, 3.2)
            particle["life"] -= 1
            if particle["life"] <= 0:
                self.engine_particles.remove(particle)

    def is_dead(self):
        return self.hp <= 0

    def is_defeated(self):
        return self.state == "defeated"

    # Deseneaza toate razele; gameplay-ul le poate pune sub proiectile.
    def draw_lasers(self, screen):
        for laser in self.lasers:
            laser.draw(screen)
        self._draw_phase_portals(screen)

    # Ieșirile și vectorii apar sub proiectile, ca avertizarea să rămână clară.
    def _draw_phase_portals(self, screen):
        if not self.phase_attack_active:
            return

        overlay = pygame.Surface(
            (self.screen_width, self.screen_height),
            pygame.SRCALPHA,
        )
        pulse = (math.sin(self.animation_timer * 0.18) + 1.0) / 2.0
        warning_is_active = self.phase_attack_charge_timer > 0
        warning_progress = 1.0 - (
            self.phase_attack_charge_timer
            / max(1, self.phase_attack_charge_duration)
        )

        for portal_index, portal in enumerate(self.phase_exit_portals):
            center = (int(portal["x"]), int(portal["y"]))
            radius = int(46 + pulse * 7)
            pygame.draw.circle(
                overlay,
                (8, 2, 24, 215),
                center,
                radius - 8,
            )
            rotation = (
                self.animation_timer * 0.15
                * (-1 if portal_index % 2 else 1)
            )
            for segment_index in range(6):
                start_angle = rotation + segment_index * math.tau / 6
                arc_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
                arc_rect.center = center
                pygame.draw.arc(
                    overlay,
                    (255, 45, 205, 235),
                    arc_rect,
                    start_angle,
                    start_angle + 0.48,
                    5,
                )
            pygame.draw.circle(
                overlay,
                (55, 235, 225, 220),
                center,
                radius - 17,
                3,
            )

            if warning_is_active:
                beam_length = max(
                    self.screen_width,
                    self.screen_height,
                ) * 2
                beam_end = (
                    int(
                        portal["x"]
                        + math.cos(portal["angle"]) * beam_length
                    ),
                    int(
                        portal["y"]
                        + math.sin(portal["angle"]) * beam_length
                    ),
                )
                beam_alpha = int(65 + warning_progress * 145)
                pygame.draw.line(
                    overlay,
                    (255, 45, 205, beam_alpha),
                    center,
                    beam_end,
                    4,
                )
                pygame.draw.line(
                    overlay,
                    (95, 245, 235, min(235, beam_alpha + 25)),
                    center,
                    beam_end,
                    1,
                )

        if warning_is_active:
            target = self.phase_locked_target
            marker_radius = int(19 + pulse * 5)
            pygame.draw.circle(
                overlay,
                (255, 55, 210, 185),
                target,
                marker_radius,
                2,
            )
            pygame.draw.line(
                overlay,
                (75, 235, 225, 190),
                (target[0] - marker_radius - 7, target[1]),
                (target[0] + marker_radius + 7, target[1]),
                2,
            )
            pygame.draw.line(
                overlay,
                (75, 235, 225, 190),
                (target[0], target[1] - marker_radius - 7),
                (target[0], target[1] + marker_radius + 7),
                2,
            )

        screen.blit(overlay, (0, 0))

        if warning_is_active:
            label = self.phase_font.render(
                "PHASE RIFT  //  VECTOR LOCKED",
                True,
                (105, 245, 230),
            )
            label_panel = pygame.Surface(
                (label.get_width() + 30, label.get_height() + 14),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                label_panel,
                (8, 4, 24, 205),
                label_panel.get_rect(),
                border_radius=8,
            )
            pygame.draw.rect(
                label_panel,
                (255, 55, 205, 175),
                label_panel.get_rect(),
                2,
                border_radius=8,
            )
            label_panel.blit(label, (15, 7))
            screen.blit(
                label_panel,
                (
                    self.screen_width // 2
                    - label_panel.get_width() // 2,
                    390,
                ),
            )

    # Deseneaza particulele, bossul, scuturile si interfata luptei.
    def draw(self, screen):
        if self.state == "defeated":
            return

        for particle in self.engine_particles:
            life_ratio = particle["life"] / 28
            particle_color = (
                255,
                int(60 + 100 * life_ratio),
                int(30 + 100 * life_ratio),
            )
            pygame.draw.circle(
                screen,
                particle_color,
                (int(particle["x"]), int(particle["y"])),
                particle["radius"],
            )

        draw_x = int(self.x)
        draw_y = int(self.y)
        if self.state == "dying":
            draw_x += random.randint(-5, 5)
            draw_y += random.randint(-4, 4)

        display_image = self.base_image
        if self.hit_timer > 0 or self.transition_timer > 0:
            display_image = self.base_image.copy()
            flash_strength = 115 if self.hit_timer > 0 else 45
            display_image.fill(
                (flash_strength, 35, 65, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
        screen.blit(display_image, (draw_x, draw_y))

        if self.difficulty_stage >= 2:
            self._draw_phase_sovereign_energy(screen)

        self._draw_core(screen)
        self._draw_generators(screen)
        if self.transition_timer > 0:
            self._draw_phase_transition_energy(screen)
        if self.state == "dying":
            self._draw_destruction_sequence(screen)
        self._draw_health_bar(screen)

        if self.state == "entering":
            self._draw_intro_warning(screen)
        elif self.phase_banner_timer > 0:
            self._draw_phase_banner(screen)

    # Stage 2+ adaugă fisuri cyan și un inel dimensional peste corpul original.
    def _draw_phase_sovereign_energy(self, screen):
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height),
            pygame.SRCALPHA,
        )
        pulse = (math.sin(self.animation_timer * 0.12) + 1.0) / 2.0
        core = self.core_center
        aura_radius = int(58 + pulse * 9)
        pygame.draw.circle(
            overlay,
            (55, 235, 225, int(38 + pulse * 28)),
            core,
            aura_radius,
        )
        pygame.draw.circle(
            overlay,
            (255, 45, 205, int(120 + pulse * 70)),
            core,
            aura_radius,
            3,
        )

        rotation = self.animation_timer * 0.035
        for crack_index in range(8):
            angle = rotation + crack_index * math.tau / 8
            start_radius = 64
            end_radius = 92 + (crack_index % 3) * 14
            midpoint_angle = angle + (0.08 if crack_index % 2 else -0.08)
            start = (
                int(core[0] + math.cos(angle) * start_radius),
                int(core[1] + math.sin(angle) * start_radius),
            )
            midpoint = (
                int(core[0] + math.cos(midpoint_angle) * 78),
                int(core[1] + math.sin(midpoint_angle) * 78),
            )
            end = (
                int(core[0] + math.cos(angle) * end_radius),
                int(core[1] + math.sin(angle) * end_radius),
            )
            crack_color = (
                (55, 235, 225, int(70 + pulse * 55))
                if crack_index % 2 == 0
                else (255, 45, 205, int(65 + pulse * 50))
            )
            pygame.draw.lines(
                overlay,
                crack_color,
                False,
                [start, midpoint, end],
                2,
            )

        if self.phase_attack_active:
            portal_radius = int(42 + pulse * 8)
            for segment_index in range(6):
                start_angle = (
                    -self.animation_timer * 0.16
                    + segment_index * math.tau / 6
                )
                arc_rect = pygame.Rect(
                    core[0] - portal_radius,
                    core[1] - portal_radius,
                    portal_radius * 2,
                    portal_radius * 2,
                )
                pygame.draw.arc(
                    overlay,
                    (105, 245, 235, 235),
                    arc_rect,
                    start_angle,
                    start_angle + 0.48,
                    4,
                )

        screen.blit(overlay, (0, 0))

    # Schimbarea fazei produce o undă vizibilă fără să schimbe gameplay-ul.
    def _draw_phase_transition_energy(self, screen):
        transition_progress = 1.0 - self.transition_timer / 150
        transition_progress = max(0.0, min(1.0, transition_progress))
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height),
            pygame.SRCALPHA,
        )

        if self.phase == 2:
            primary_color = (135, 75, 255)
            secondary_color = (210, 175, 255)
        else:
            primary_color = (255, 30, 105)
            secondary_color = (255, 175, 210)

        pulse = abs(math.sin(self.animation_timer * 0.16))
        for ring_index in range(3):
            ring_progress = (
                transition_progress + ring_index * 0.22
            ) % 1.0
            ring_radius = int(42 + ring_progress * 245)
            ring_alpha = int((1.0 - ring_progress) * (145 + pulse * 45))
            pygame.draw.circle(
                overlay,
                (*primary_color, ring_alpha),
                self.core_center,
                ring_radius,
                max(2, 7 - ring_index * 2),
            )

        rotation = self.animation_timer * 0.035
        for ray_index in range(12):
            angle = rotation + ray_index * math.tau / 12
            inner_radius = 52 + int(pulse * 9)
            outer_radius = 92 + int(transition_progress * 105)
            ray_start = (
                int(self.core_center[0] + math.cos(angle) * inner_radius),
                int(self.core_center[1] + math.sin(angle) * inner_radius),
            )
            ray_end = (
                int(self.core_center[0] + math.cos(angle) * outer_radius),
                int(self.core_center[1] + math.sin(angle) * outer_radius),
            )
            pygame.draw.line(
                overlay,
                (*secondary_color, int(75 + pulse * 85)),
                ray_start,
                ray_end,
                2,
            )

        pygame.draw.circle(
            overlay,
            (*primary_color, int(55 + pulse * 45)),
            self.core_center,
            int(62 + pulse * 18),
        )
        screen.blit(overlay, (0, 0))

    # Înfrângerea dezintegrează progresiv corpul înainte de exploziile finale.
    def _draw_destruction_sequence(self, screen):
        destruction_progress = 1.0 - max(0, self.death_timer) / 240
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height),
            pygame.SRCALPHA,
        )
        pulse = abs(math.sin(self.animation_timer * 0.34))

        # Fisurile pornesc din nucleu și ajung treptat la marginile navei.
        fracture_targets = (
            (-250, -92),
            (-205, 55),
            (-125, 118),
            (-60, -120),
            (55, 128),
            (138, -112),
            (215, 48),
            (270, -72),
        )
        visible_fractures = max(
            1,
            int(len(fracture_targets) * min(1.0, destruction_progress * 1.6)),
        )
        for fracture_index, (offset_x, offset_y) in enumerate(
            fracture_targets[:visible_fractures]
        ):
            target = (
                self.core_center[0] + offset_x,
                self.core_center[1] + offset_y,
            )
            midpoint = (
                int((self.core_center[0] + target[0]) / 2 + offset_y * 0.08),
                int((self.core_center[1] + target[1]) / 2 - offset_x * 0.05),
            )
            pygame.draw.lines(
                overlay,
                (255, 35, 95, int(135 + pulse * 90)),
                False,
                [self.core_center, midpoint, target],
                2 + fracture_index % 2,
            )
            pygame.draw.circle(
                overlay,
                (255, 210, 225, 190),
                midpoint,
                2,
            )

        # Nucleul se comprimă, apoi eliberează inele tot mai mari.
        collapse_radius = max(8, int(58 * (1.0 - destruction_progress * 0.72)))
        pygame.draw.circle(
            overlay,
            (255, 20, 75, int(85 + pulse * 75)),
            self.core_center,
            collapse_radius * 2,
        )
        pygame.draw.circle(
            overlay,
            (255, 245, 248, int(175 + pulse * 70)),
            self.core_center,
            collapse_radius,
        )

        for ring_index in range(3):
            ring_progress = (
                destruction_progress * 2.4 + ring_index * 0.31
            ) % 1.0
            radius = int(45 + ring_progress * 310)
            alpha = int((1.0 - ring_progress) * 150)
            pygame.draw.circle(
                overlay,
                (255, 55, 105, alpha),
                self.core_center,
                radius,
                4,
            )

        # Aproape de final, corpul pâlpâie alb înainte să dispară.
        if destruction_progress > 0.78 and self.animation_timer % 8 < 3:
            flash_alpha = int(
                85 * (destruction_progress - 0.78) / 0.22
            )
            pygame.draw.rect(
                overlay,
                (255, 235, 240, flash_alpha),
                self.rect,
                border_radius=45,
            )

        screen.blit(overlay, (0, 0))

    # Nucleul devine foarte vizibil in ultima faza.
    def _draw_core(self, screen):
        pulse = 1.0 + math.sin(self.animation_timer * 0.12) * 0.16
        base_radius = 46 if self.phase == 3 else 28
        core_radius = int(base_radius * pulse)
        glow_surface = pygame.Surface(
            (core_radius * 4, core_radius * 4),
            pygame.SRCALPHA,
        )
        glow_center = (core_radius * 2, core_radius * 2)
        pygame.draw.circle(
            glow_surface,
            (255, 20, 90, 45 if self.phase < 3 else 95),
            glow_center,
            core_radius * 2,
        )
        pygame.draw.circle(
            glow_surface,
            (255, 45, 115, 210),
            glow_center,
            core_radius,
        )
        pygame.draw.circle(
            glow_surface,
            (255, 225, 245, 230),
            glow_center,
            max(5, core_radius // 3),
        )
        screen.blit(
            glow_surface,
            (
                self.core_center[0] - core_radius * 2,
                self.core_center[1] - core_radius * 2,
            ),
        )

    # Afiseaza generatoarele si viata lor numai in faza a doua.
    def _draw_generators(self, screen):
        if self.phase != 2:
            return

        for generator_index, generator_rect in enumerate(
            self.generator_rects
        ):
            generator_hp = self.generator_hp[generator_index]
            if generator_hp <= 0:
                pygame.draw.circle(
                    screen,
                    (65, 30, 40),
                    generator_rect.center,
                    24,
                    3,
                )
                continue

            pulse_radius = 30 + int(
                5 * abs(math.sin(self.animation_timer * 0.10))
            )
            pygame.draw.circle(
                screen,
                (100, 45, 255),
                generator_rect.center,
                pulse_radius,
                4,
            )
            pygame.draw.circle(
                screen,
                (220, 205, 255),
                generator_rect.center,
                12,
            )
            bar_rect = pygame.Rect(
                generator_rect.centerx - 34,
                generator_rect.bottom + 5,
                68,
                6,
            )
            pygame.draw.rect(screen, (30, 20, 45), bar_rect)
            pygame.draw.rect(
                screen,
                (155, 80, 255),
                (
                    bar_rect.x,
                    bar_rect.y,
                    int(
                        bar_rect.width
                        * generator_hp
                        / self.generator_max_hp
                    ),
                    bar_rect.height,
                ),
            )

        if self.generators_are_active():
            shield_surface = pygame.Surface(
                (self.screen_width, self.screen_height),
                pygame.SRCALPHA,
            )
            pygame.draw.ellipse(
                shield_surface,
                (125, 75, 255, 95),
                self.hitbox.inflate(55, 45),
                4,
            )
            screen.blit(shield_surface, (0, 0))

    # Bara de sus arata numele, faza si procentul de viata.
    def _draw_health_bar(self, screen):
        if self.state == "entering":
            return

        bar_width = min(720, self.screen_width - 220)
        bar_height = 24
        bar_x = self.screen_width // 2 - bar_width // 2
        bar_y = 48
        hp_ratio = max(0.0, self.hp / self.max_hp)

        panel = pygame.Surface(
            (bar_width + 32, 70),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (12, 4, 20, 215),
            panel.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            panel,
            (185, 55, 110, 180),
            panel.get_rect(),
            2,
            border_radius=10,
        )
        screen.blit(panel, (bar_x - 16, 17))

        sovereign_name = (
            "THE DEAD STAR SOVEREIGN"
            if self.difficulty_stage == 1
            else "THE PHASE SOVEREIGN"
        )
        title = self.title_font.render(
            f"{sovereign_name}  //  PHASE {self.phase}",
            True,
            (245, 225, 238),
        )
        screen.blit(
            title,
            (
                self.screen_width // 2 - title.get_width() // 2,
                22,
            ),
        )
        pygame.draw.rect(
            screen,
            (35, 20, 40),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=8,
        )
        hp_color = (
            (210, 45, 95)
            if self.phase < 3
            else (255, 55, 45)
        )
        pygame.draw.rect(
            screen,
            hp_color,
            (
                bar_x,
                bar_y,
                int(bar_width * hp_ratio),
                bar_height,
            ),
            border_radius=8,
        )
        pygame.draw.rect(
            screen,
            (245, 205, 225),
            (bar_x, bar_y, bar_width, bar_height),
            2,
            border_radius=8,
        )

    # Avertizarea precede intrarea bossului si blocheaza atacurile acestuia.
    def _draw_intro_warning(self, screen):
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height),
            pygame.SRCALPHA,
        )
        alpha = 28 + int(
            24 * abs(math.sin(self.animation_timer * 0.10))
        )
        overlay.fill((120, 0, 30, alpha))
        screen.blit(overlay, (0, 0))

        title = self.warning_font.render(
            "FINAL SIGNAL DETECTED",
            True,
            (255, 75, 105),
        )
        boss_warning = (
            "THE DEAD STAR SOVEREIGN APPROACHES"
            if self.difficulty_stage == 1
            else (
                f"SOVEREIGN PROTOCOL {self.difficulty_stage - 1:02d} "
                "ACTIVATED"
            )
        )
        subtitle = self.phase_font.render(
            boss_warning,
            True,
            (240, 220, 230),
        )
        screen.blit(
            title,
            (
                self.screen_width // 2 - title.get_width() // 2,
                self.screen_height // 2 - 45,
            ),
        )
        screen.blit(
            subtitle,
            (
                self.screen_width // 2 - subtitle.get_width() // 2,
                self.screen_height // 2 + 28,
            ),
        )

    # Anunta clar schimbarea mecanicii dintre cele trei faze.
    def _draw_phase_banner(self, screen):
        if self.phase == 1:
            title = "PHASE 1  //  ARMORED ASSAULT"
            subtitle = "BREAK THE OUTER ARMOR"
        elif self.phase == 2:
            title = "PHASE 2  //  DEFENSE NETWORK"
            subtitle = "DESTROY BOTH SHIELD GENERATORS"
        else:
            title = "PHASE 3  //  CORE OVERLOAD"
            subtitle = "THE CORE IS EXPOSED"

        banner = pygame.Surface(
            (650, 94),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (15, 5, 24, 220),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (220, 50, 105, 190),
            banner.get_rect(),
            2,
            border_radius=10,
        )
        title_surface = self.title_font.render(
            title,
            True,
            (255, 100, 135),
        )
        subtitle_surface = self.phase_font.render(
            subtitle,
            True,
            (235, 220, 230),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                13,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width() // 2,
                57,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2 - banner.get_width() // 2,
                self.screen_height // 2 - 70,
            ),
        )
