import math
import random
from pathlib import Path

import pygame


# Duratele sunt exprimate în cadre, deoarece gameplay-ul rulează la 60 FPS.
INITIAL_EVENT_DELAY = 900
EVENT_COOLDOWN = 1050
WARNING_DURATION = 180
ACTIVE_DURATION = 660
RECOVERY_DURATION = 120
PULSE_DURATION = 110
PULSE_WARNING_END = 48
PULSE_BLAST_END = 98
TOTAL_PULSES = 6

# Duratele folosite de evenimentul Gravity Wave.
GRAVITY_WARNING_DURATION = 150
GRAVITY_ACTIVE_DURATION = 540
GRAVITY_RECOVERY_DURATION = 100
GRAVITY_DIRECTION_DURATION = 120

# Duratele evenimentului în care sosesc navele aliate.
REINFORCEMENT_WARNING_DURATION = 150
REINFORCEMENT_ACTIVE_DURATION = 720
REINFORCEMENT_RECOVERY_DURATION = 120

# Duratele și numărul atacurilor din evenimentul Drone Swarm.
DRONE_WARNING_DURATION = 150
DRONE_ACTIVE_DURATION = 720
DRONE_RECOVERY_DURATION = 120
DRONE_SQUAD_INTERVAL = 180
DRONE_TOTAL_SQUADS = 3

# Duratele și limita de expunere ale norului radioactiv.
RADIATION_WARNING_DURATION = 150
RADIATION_ACTIVE_DURATION = 780
RADIATION_RECOVERY_DURATION = 120
MAX_RADIATION_EXPOSURE = 100.0

# Duratele și fazele evenimentului Black Hole Pulse.
BLACK_HOLE_WARNING_DURATION = 180
BLACK_HOLE_ACTIVE_DURATION = 720
BLACK_HOLE_RECOVERY_DURATION = 150
BLACK_HOLE_PULSE_DURATION = 240
BLACK_HOLE_TOTAL_PULSES = 3

# Duratele și structura celor trei valuri de asteroizi.
ASTEROID_WARNING_DURATION = 150
ASTEROID_ACTIVE_DURATION = 900
ASTEROID_RECOVERY_DURATION = 120
ASTEROID_WAVE_DURATION = 300
ASTEROID_TELEGRAPH_DURATION = 60
ASTEROID_TOTAL_WAVES = 3

# Duratele celor trei faze Crossfire Protocol.
CROSSFIRE_WARNING_DURATION = 150
CROSSFIRE_ACTIVE_DURATION = 1080
CROSSFIRE_RECOVERY_DURATION = 150
CROSSFIRE_PHASE_DURATION = 360
CROSSFIRE_TOTAL_PHASES = 3

# Duratele și structura celor trei salve de rachete ghidate.
MISSILE_WARNING_DURATION = 150
MISSILE_ACTIVE_DURATION = 900
MISSILE_RECOVERY_DURATION = 150
MISSILE_SALVO_DURATION = 300
MISSILE_LOCK_DURATION = 75
MISSILE_TOTAL_SALVOS = 3


# Controlează furtuna solară produsă de steaua moartă.
class SolarStormEvent:

    # Creează fonturile și valorile de bază ale evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )

        self.reset()

    # Readuce evenimentul în starea de așteptare.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.pulse_timer = 0
        self.pulse_number = 0
        self.energy_columns = []
        self.player_hit_during_pulse = False

    # Pornește evenimentul atunci când este selectat de manager.
    def start(self):
        self._start_warning()

    # Actualizează starea furtunii și returnează True la impact.
    def update(self, player_hitbox, wave):
        if self.state == "idle":
            return False

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self._start_active_phase(
                    wave,
                    player_hitbox,
                )

            return False

        if self.state == "active":
            return self._update_active_phase(
                player_hitbox,
                wave,
            )

        if self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self._finish_event()

        return False

    # Pornește alarma care oferă jucătorului timp de pregătire.
    def _start_warning(self):
        self.state = "warning"
        self.warning_timer = WARNING_DURATION
        self.energy_columns = []

    # Pornește atacul și pregătește primul impuls.
    def _start_active_phase(
        self,
        wave,
        player_hitbox,
    ):
        self.state = "active"
        self.active_timer = ACTIVE_DURATION
        self.pulse_number = 0
        self._prepare_new_pulse(
            wave,
            player_hitbox,
        )

    # Actualizează impulsurile și verifică impactul cu jucătorul.
    def _update_active_phase(
        self,
        player_hitbox,
        wave,
    ):
        self.active_timer -= 1
        self.pulse_timer -= 1

        pulse_elapsed = (
            PULSE_DURATION - self.pulse_timer
        )
        blast_active = (
            PULSE_WARNING_END
            <= pulse_elapsed
            < PULSE_BLAST_END
        )

        player_was_hit = False

        if (
            blast_active
            and not self.player_hit_during_pulse
        ):
            for column_rect in self.energy_columns:
                if player_hitbox.colliderect(
                    column_rect
                ):
                    player_was_hit = True
                    self.player_hit_during_pulse = True
                    break

        if self.pulse_timer <= 0:
            self._prepare_new_pulse(
                wave,
                player_hitbox,
            )

        if self.active_timer <= 0:
            self.state = "recovery"
            self.recovery_timer = RECOVERY_DURATION
            self.energy_columns = []

        return player_was_hit

    # Alege coloane diferite, lăsând întotdeauna spații de evitare.
    def _prepare_new_pulse(
        self,
        wave,
        player_hitbox,
    ):
        self.pulse_timer = PULSE_DURATION
        self.pulse_number += 1
        self.player_hit_during_pulse = False

        slot_count = 9
        slot_width = (
            self.screen_width / slot_count
        )
        column_width = 94

        # Numărul coloanelor crește până când rămân doar
        # două culoare sigure în valurile avansate.
        column_count = min(
            7,
            5
            + max(
                0,
                int(wave) - 1,
            )
            // 2,
        )

        # Garantăm un culoar sigur apropiat, dar diferit de poziția navei.
        player_slot = max(
            0,
            min(
                slot_count - 1,
                int(
                    player_hitbox.centerx
                    / slot_width
                ),
            ),
        )
        nearby_safe_slots = [
            slot_index
            for slot_index in range(
                player_slot - 2,
                player_slot + 3,
            )
            if (
                0 <= slot_index < slot_count
                and slot_index != player_slot
            )
        ]
        guaranteed_safe_slot = random.choice(
            nearby_safe_slots
        )

        available_column_slots = [
            slot_index
            for slot_index in range(slot_count)
            if slot_index != guaranteed_safe_slot
        ]
        chosen_slots = random.sample(
            available_column_slots,
            column_count,
        )

        self.energy_columns = []

        for slot_index in chosen_slots:
            column_center = int(
                slot_index * slot_width
                + slot_width / 2
            )
            self.energy_columns.append(
                pygame.Rect(
                    column_center
                    - column_width // 2,
                    0,
                    column_width,
                    self.screen_height,
                )
            )

    # Marchează evenimentul drept terminat pentru manager.
    def _finish_event(self):
        self.state = "finished"
        self.energy_columns = []

    # Desenează alarma, zonele marcate și impulsurile active.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_environment_tint(screen)

        if self.state == "warning":
            self._draw_global_warning(screen)

        elif self.state == "active":
            self._draw_energy_columns(screen)
            self._draw_active_status(screen)

        elif self.state == "recovery":
            self._draw_recovery_status(screen)

    # Adaugă o tentă roșie peste arenă în timpul evenimentului.
    def _draw_environment_tint(self, screen):
        tint_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        if self.state == "warning":
            pulse = (
                pygame.time.get_ticks() // 180
            ) % 2
            tint_alpha = 24 if pulse else 10
        elif self.state == "active":
            tint_alpha = 34
        else:
            tint_alpha = 14

        tint_surface.fill(
            (150, 20, 5, tint_alpha)
        )
        screen.blit(tint_surface, (0, 0))

    # Afișează alarma globală și numărătoarea inversă.
    def _draw_global_warning(self, screen):
        seconds_remaining = max(
            1,
            (self.warning_timer + 59) // 60,
        )
        self._draw_status_banner(
            screen,
            "SOLAR STORM INCOMING",
            (
                "ENERGY SURGE IN "
                f"{seconds_remaining}"
            ),
            (255, 105, 70),
        )

        border_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            border_surface,
            (255, 65, 35, 120),
            border_surface.get_rect(),
            7,
        )
        screen.blit(border_surface, (0, 0))

    # Desenează marcajele coloanelor și energia din timpul atacului.
    def _draw_energy_columns(self, screen):
        pulse_elapsed = (
            PULSE_DURATION - self.pulse_timer
        )
        blast_active = (
            PULSE_WARNING_END
            <= pulse_elapsed
            < PULSE_BLAST_END
        )

        column_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        for column_rect in self.energy_columns:
            if blast_active:
                self._draw_active_column(
                    column_surface,
                    column_rect,
                )
            else:
                self._draw_column_warning(
                    column_surface,
                    column_rect,
                )

        screen.blit(column_surface, (0, 0))

    # Desenează zona transparentă ce anunță următorul impuls.
    @staticmethod
    def _draw_column_warning(
        surface,
        column_rect,
    ):
        pygame.draw.rect(
            surface,
            (255, 80, 35, 38),
            column_rect,
        )
        pygame.draw.rect(
            surface,
            (255, 155, 75, 155),
            column_rect,
            3,
        )

        center_x = column_rect.centerx
        pygame.draw.line(
            surface,
            (255, 225, 170, 180),
            (center_x, 0),
            (center_x, column_rect.height),
            2,
        )

    # Desenează impulsul solar cu margine, energie și miez luminos.
    @staticmethod
    def _draw_active_column(
        surface,
        column_rect,
    ):
        pygame.draw.rect(
            surface,
            (255, 45, 15, 115),
            column_rect,
        )

        middle_rect = column_rect.inflate(
            -26,
            0,
        )
        pygame.draw.rect(
            surface,
            (255, 155, 45, 195),
            middle_rect,
        )

        core_rect = column_rect.inflate(
            -56,
            0,
        )
        pygame.draw.rect(
            surface,
            (255, 250, 215, 235),
            core_rect,
        )

    # Afișează starea impulsului solar activ.
    def _draw_active_status(self, screen):
        pulse_elapsed = (
            PULSE_DURATION - self.pulse_timer
        )

        if pulse_elapsed < PULSE_WARNING_END:
            subtitle = "MOVE OUT OF MARKED COLUMNS"
            color = (255, 180, 85)
        elif pulse_elapsed < PULSE_BLAST_END:
            subtitle = "ENERGY IMPACT"
            color = (255, 245, 205)
        else:
            subtitle = "NEXT PULSE DETECTED"
            color = (255, 135, 70)

        self._draw_status_banner(
            screen,
            (
                "SOLAR PULSE "
                f"{min(self.pulse_number, TOTAL_PULSES)}"
                f"/{TOTAL_PULSES}"
            ),
            subtitle,
            color,
        )

    # Afișează mesajul de final al furtunii.
    def _draw_recovery_status(self, screen):
        self._draw_status_banner(
            screen,
            "SOLAR STORM CLEAR",
            "ENERGY LEVELS STABILIZING",
            (120, 225, 255),
        )

    # Desenează un panou comun pentru toate stările evenimentului.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (560, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (7, 5, 14, 205),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 165),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (220, 230, 240),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Deformează arena și schimbă direcția gravitației periodic.
class GravityWaveEvent:

    # Creează fonturile și valorile de bază ale evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.reset()

    # Readuce evenimentul în starea inactivă.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.direction_timer = 0
        self.direction_flash_timer = 0
        self.direction = 1
        self.force_strength = 0.0
        self.animation_timer = 0
        self.flow_particles = []
        self._seed_flow_particles()

    # Creează particulele care arată direcția curentului gravitațional.
    def _seed_flow_particles(self):
        self.flow_particles = []

        for _ in range(104):
            self.flow_particles.append(
                [
                    random.uniform(0, self.screen_width),
                    random.uniform(115, self.screen_height - 25),
                    random.uniform(0.35, 1.0),
                    random.uniform(16, 48),
                    random.uniform(0, math.tau),
                ]
            )

    # Pornește alarma și calculează puterea în funcție de wave.
    def start(self, wave):
        self.state = "warning"
        self.warning_timer = (
            GRAVITY_WARNING_DURATION
        )
        self.force_strength = min(
            4.6,
            2.25 + max(1, int(wave)) * 0.28,
        )
        self.direction = random.choice(
            (-1, 1)
        )
        self.animation_timer = 0
        self._seed_flow_particles()

    # Actualizează avertizarea, forța activă sau revenirea.
    def update(self, player_hitbox, wave):
        del player_hitbox
        del wave
        self.animation_timer += 1
        self._update_visual_particles()

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = (
                    GRAVITY_ACTIVE_DURATION
                )
                self.direction_timer = (
                    GRAVITY_DIRECTION_DURATION
                )
                self.direction_flash_timer = 35

        elif self.state == "active":
            self._update_active_phase()

        elif self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Deplasează fluxurile luminoase fără să influențeze mecanica evenimentului.
    def _update_visual_particles(self):
        if self.state == "active":
            visual_speed = 7.0 + self.force_strength * 0.7
        elif self.state == "warning":
            visual_speed = 3.0
        else:
            visual_speed = 2.0

        if self.direction_flash_timer > 20:
            visual_speed *= 0.45

        margin = 90

        for particle in self.flow_particles:
            particle[0] += (
                self.direction
                * visual_speed
                * particle[2]
            )
            particle[1] += (
                math.sin(
                    self.animation_timer * 0.045
                    + particle[4]
                )
                * 0.22
                * particle[2]
            )

            if (
                self.direction > 0
                and particle[0] > self.screen_width + margin
            ):
                particle[0] = -margin
                particle[1] = random.uniform(
                    115,
                    self.screen_height - 25,
                )
            elif (
                self.direction < 0
                and particle[0] < -margin
            ):
                particle[0] = self.screen_width + margin
                particle[1] = random.uniform(
                    115,
                    self.screen_height - 25,
                )

    # Schimbă direcția atracției la intervale regulate.
    def _update_active_phase(self):
        self.active_timer -= 1
        self.direction_timer -= 1

        if self.direction_flash_timer > 0:
            self.direction_flash_timer -= 1

        if self.direction_timer <= 0:
            self.direction *= -1
            self.direction_timer = (
                GRAVITY_DIRECTION_DURATION
            )
            self.direction_flash_timer = 35

        if self.active_timer <= 0:
            self.state = "recovery"
            self.recovery_timer = (
                GRAVITY_RECOVERY_DURATION
            )

    # Returnează deplasarea aplicată navei în cadrul curent.
    def get_player_force(self):
        if self.state != "active":
            return 0.0

        if self.direction_flash_timer > 20:
            force_multiplier = 0.45
        else:
            force_multiplier = 1.0

        return (
            self.direction
            * self.force_strength
            * force_multiplier
        )

    # Returnează deviația orizontală aplicată proiectilelor.
    def get_projectile_curve(self):
        return self.get_player_force() * 0.17

    # Desenează avertizarea și deformarea spațiului.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_space_distortion(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "GRAVITY WAVE DETECTED",
                (
                    "SPATIAL SHIFT IN "
                    f"{seconds_remaining}"
                ),
                (165, 125, 255),
            )

        elif self.state == "active":
            if self.direction < 0:
                subtitle = "<<< GRAVITY PULLING LEFT"
            else:
                subtitle = "GRAVITY PULLING RIGHT >>>"

            if self.direction_flash_timer > 20:
                subtitle = "DIRECTION SHIFT"

            self._draw_status_banner(
                screen,
                "GRAVITY WAVE",
                subtitle,
                (125, 195, 255),
            )

        elif self.state == "recovery":
            self._draw_status_banner(
                screen,
                "GRAVITY STABILIZED",
                "NAVIGATION CONTROL RESTORED",
                (120, 230, 255),
            )

    # Desenează curenți de particule, fronturi de distorsiune și lumină graduală.
    def _draw_space_distortion(self, screen):
        distortion_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        tint_alpha = 30 if self.state == "active" else 15
        distortion_surface.fill(
            (28, 12, 78, tint_alpha),
        )

        # Particulele devin dâre mai lungi și mai luminoase în faza activă.
        activity_multiplier = (
            1.0 if self.state == "active" else 0.55
        )
        for particle in self.flow_particles:
            depth = particle[2]
            trail_length = (
                particle[3]
                * activity_multiplier
            )
            head_x = int(particle[0])
            head_y = int(particle[1])
            tail_x = int(
                particle[0]
                - self.direction * trail_length
            )
            alpha = int(
                (45 + 125 * depth)
                * activity_multiplier
            )
            streak_color = (
                int(105 + 65 * depth),
                int(145 + 75 * depth),
                255,
                alpha,
            )
            pygame.draw.line(
                distortion_surface,
                streak_color,
                (tail_x, head_y),
                (head_x, head_y),
                max(1, int(depth * 3)),
            )
            pygame.draw.circle(
                distortion_surface,
                (205, 230, 255, min(220, alpha + 35)),
                (head_x, head_y),
                max(1, int(depth * 2)),
            )

        # Trei fronturi verticale traversează arena și sugerează deformarea.
        front_speed = 0.010 if self.state == "active" else 0.006
        for front_index in range(3):
            front_progress = (
                self.animation_timer * front_speed
                + front_index / 3
            ) % 1.0
            if self.direction < 0:
                front_progress = 1.0 - front_progress

            front_x = int(front_progress * self.screen_width)
            front_points = []
            for y_position in range(95, self.screen_height + 25, 20):
                curve_offset = math.sin(
                    y_position * 0.012
                    + self.animation_timer * 0.025
                    + front_index
                ) * 24
                front_points.append(
                    (
                        int(front_x + curve_offset),
                        y_position,
                    )
                )

            front_alpha = 34 if self.state == "active" else 18
            pygame.draw.lines(
                distortion_surface,
                (115, 150, 255, front_alpha),
                False,
                front_points,
                2 if self.state == "active" else 1,
            )
            pygame.draw.lines(
                distortion_surface,
                (205, 225, 255, front_alpha + 12),
                False,
                front_points,
                1,
            )

        # Atracția este accentuată gradual la marginea spre care curge arena.
        if self.state == "active":
            strip_width = 18
            for strip_index in range(9):
                if self.direction < 0:
                    strip_x = strip_index * strip_width
                else:
                    strip_x = (
                        self.screen_width
                        - (strip_index + 1) * strip_width
                    )
                pygame.draw.rect(
                    distortion_surface,
                    (
                        90,
                        135,
                        255,
                        max(5, 48 - strip_index * 5),
                    ),
                    (
                        strip_x,
                        0,
                        strip_width,
                        self.screen_height,
                    ),
                )

        # Schimbarea direcției produce un flash scurt și lizibil.
        if self.direction_flash_timer > 20:
            flash_alpha = int(
                (self.direction_flash_timer - 20)
                / 15
                * 55
            )
            flash_surface = pygame.Surface(
                (self.screen_width, self.screen_height),
                pygame.SRCALPHA,
            )
            flash_surface.fill(
                (115, 135, 255, flash_alpha)
            )
            distortion_surface.blit(flash_surface, (0, 0))

        screen.blit(
            distortion_surface,
            (0, 0),
        )

    # Desenează panoul comun al evenimentului Gravity Wave.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (600, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (5, 6, 20, 210),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 165),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (220, 232, 245),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Coordonează sosirea și retragerea navelor aliate.
class ReinforcementEvent:

    # Creează fonturile și valorile folosite de mesajele evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.reset()

    # Readuce evenimentul în starea de așteptare.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.animation_timer = 0
        self.deployment_requested = False

    # Pornește recepționarea semnalului aliat.
    def start(self):
        self.state = "warning"
        self.warning_timer = (
            REINFORCEMENT_WARNING_DURATION
        )
        self.animation_timer = 0
        self.deployment_requested = False

    # Actualizează semnalul, timpul de suport și retragerea.
    def update(self, player_hitbox, wave):
        del player_hitbox
        del wave
        self.animation_timer += 1

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = (
                    REINFORCEMENT_ACTIVE_DURATION
                )
                self.deployment_requested = True

        elif self.state == "active":
            self.active_timer -= 1

            if self.active_timer <= 0:
                self.state = "recovery"
                self.recovery_timer = (
                    REINFORCEMENT_RECOVERY_DURATION
                )

        elif self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Returnează o singură comandă de creare a navelor aliate.
    def consume_deployment_request(self):
        if not self.deployment_requested:
            return False

        self.deployment_requested = False
        return True

    # Desenează semnalul radar și mesajele evenimentului.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_radar_effect(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "ALLIED SIGNAL DETECTED",
                (
                    "REINFORCEMENTS ARRIVING IN "
                    f"{seconds_remaining}"
                ),
                (80, 220, 255),
            )

        elif self.state == "active":
            seconds_remaining = max(
                1,
                (self.active_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "ALLIED SUPPORT ACTIVE",
                (
                    "FORMATION COVER: "
                    f"{seconds_remaining}s"
                ),
                (95, 235, 255),
            )

        elif self.state == "recovery":
            self._draw_status_banner(
                screen,
                "REINFORCEMENTS DEPARTING",
                "ALLIED FORMATION WITHDRAWING",
                (145, 205, 255),
            )

    # Adaugă linii radar discrete pentru a anunța comunicația aliată.
    def _draw_radar_effect(self, screen):
        radar_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        scan_y = int(
            (
                self.animation_timer * 5
            ) % self.screen_height
        )
        pygame.draw.line(
            radar_surface,
            (55, 205, 255, 70),
            (0, scan_y),
            (self.screen_width, scan_y),
            2,
        )

        for circle_index in range(3):
            radius = int(
                (
                    self.animation_timer * 3
                    + circle_index * 95
                ) % 290
            )
            pygame.draw.circle(
                radar_surface,
                (55, 180, 255, 42),
                (
                    self.screen_width // 2,
                    self.screen_height,
                ),
                radius,
                2,
            )

        screen.blit(radar_surface, (0, 0))

    # Desenează panoul comun al evenimentului de suport.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (610, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (4, 12, 22, 215),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 175),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (220, 240, 250),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Coordonează cele trei grupuri ale roiului de drone.
class DroneSwarmEvent:

    # Creează fonturile și valorile de bază ale evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.reset()

    # Readuce roiul în starea inactivă.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.squad_timer = 0
        self.squads_deployed = 0
        self.pending_squads = 0
        self.drones_per_squad = 3
        self.animation_timer = 0

    # Pornește avertizarea și adaptează mărimea grupurilor la wave.
    def start(self, wave):
        self.state = "warning"
        self.warning_timer = DRONE_WARNING_DURATION
        self.animation_timer = 0
        self.drones_per_squad = min(
            6,
            3 + max(0, int(wave) - 1) // 2,
        )

    # Actualizează avertizarea, lansarea grupurilor și retragerea.
    def update(self, player_hitbox, wave):
        del player_hitbox
        del wave
        self.animation_timer += 1

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = DRONE_ACTIVE_DURATION
                self.squad_timer = DRONE_SQUAD_INTERVAL
                self.squads_deployed = 1
                self.pending_squads = 1

        elif self.state == "active":
            self.active_timer -= 1
            self.squad_timer -= 1

            if (
                self.squad_timer <= 0
                and self.squads_deployed
                < DRONE_TOTAL_SQUADS
            ):
                self.squads_deployed += 1
                self.pending_squads += 1
                self.squad_timer = DRONE_SQUAD_INTERVAL

            if self.active_timer <= 0:
                self.state = "recovery"
                self.recovery_timer = DRONE_RECOVERY_DURATION

        elif self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Returnează numărul de drone din următorul grup o singură dată.
    def consume_squad_request(self):
        if self.pending_squads <= 0:
            return 0

        self.pending_squads -= 1
        return self.drones_per_squad

    # Desenează alarma, starea roiului și semnalul de retragere.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_swarm_overlay(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "DRONE SWARM INBOUND",
                f"MULTIPLE SIGNALS: ETA {seconds_remaining}",
                (255, 75, 155),
            )

        elif self.state == "active":
            self._draw_status_banner(
                screen,
                "DRONE SWARM",
                (
                    "ATTACK GROUP "
                    f"{self.squads_deployed}"
                    f"/{DRONE_TOTAL_SQUADS}"
                ),
                (225, 80, 255),
            )

        elif self.state == "recovery":
            self._draw_status_banner(
                screen,
                "SWARM SIGNAL LOST",
                "SURVIVING DRONES RETREATING",
                (145, 190, 255),
            )

    # Desenează puncte și linii care sugerează o rețea coordonată.
    def _draw_swarm_overlay(self, screen):
        overlay = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )
        point_positions = []

        for point_index in range(12):
            point_x = int(
                (
                    point_index * 113
                    + self.animation_timer * 2
                ) % self.screen_width
            )
            point_y = int(
                145
                + math.sin(
                    self.animation_timer * 0.045
                    + point_index * 0.8
                )
                * 75
                + point_index * 22
            )
            point_positions.append(
                (point_x, point_y)
            )

        for point_index in range(
            len(point_positions) - 1
        ):
            pygame.draw.line(
                overlay,
                (205, 50, 255, 28),
                point_positions[point_index],
                point_positions[point_index + 1],
                1,
            )

        for point_position in point_positions:
            pygame.draw.circle(
                overlay,
                (255, 70, 155, 85),
                point_position,
                3,
            )

        screen.blit(overlay, (0, 0))

    # Desenează panoul comun al roiului de drone.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (590, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (15, 3, 22, 215),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 175),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (235, 220, 245),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Creează zone radioactive mobile și urmărește expunerea jucătorului.
class RadiationCloudEvent:

    # Creează fonturile și valorile de bază ale evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.exposure_font = pygame.font.Font(
            None,
            24,
        )
        self.cloud_images = self._load_cloud_images()
        self.reset()

    # Încarcă cele trei variante premium și păstrează proporțiile originale.
    def _load_cloud_images(self):
        radiation_folder = (
            Path(__file__).resolve().parent
            / "assets"
            / "images"
            / "effects"
            / "radiation"
        )
        filenames = (
            "radiation_cloud_dense.png",
            "radiation_cloud_wispy.png",
            "radiation_cloud_diffuse.png",
        )
        cloud_images = []

        for filename in filenames:
            image_path = radiation_folder / filename
            if not image_path.exists():
                continue

            try:
                cloud_image = pygame.image.load(
                    str(image_path)
                ).convert_alpha()
                visible_bounds = cloud_image.get_bounding_rect(
                    min_alpha=8
                )
                if (
                    visible_bounds.width > 0
                    and visible_bounds.height > 0
                ):
                    cloud_image = cloud_image.subsurface(
                        visible_bounds
                    ).copy()

                maximum_dimension = max(
                    cloud_image.get_width(),
                    cloud_image.get_height(),
                )
                image_scale = 360 / maximum_dimension
                cloud_image = pygame.transform.smoothscale(
                    cloud_image,
                    (
                        max(1, int(cloud_image.get_width() * image_scale)),
                        max(1, int(cloud_image.get_height() * image_scale)),
                    ),
                )
                cloud_images.append(cloud_image)
            except pygame.error:
                # Norii procedurali vechi rămân variantă de rezervă.
                continue

        return cloud_images

    # Readuce norul și bara de radiație la valorile inițiale.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.animation_timer = 0
        self.exposure = 0.0
        self.player_exposed = False
        self.clouds = []

    # Pornește avertizarea și generează norii potriviți wave-ului.
    def start(self, wave):
        self.state = "warning"
        self.warning_timer = RADIATION_WARNING_DURATION
        self.animation_timer = 0
        self.exposure = 0.0
        self.player_exposed = False
        self._create_clouds(wave)

    # Actualizează norii și returnează True când expunerea produce damage.
    def update(
        self,
        player_hitbox,
        wave,
        player_shielded=False,
    ):
        del wave
        self.animation_timer += 1

        if self.state == "warning":
            self.warning_timer -= 1
            self._move_clouds(speed_multiplier=0.28)

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = RADIATION_ACTIVE_DURATION

            return False

        if self.state == "active":
            self.active_timer -= 1
            self._move_clouds(speed_multiplier=1.0)
            self.player_exposed = (
                self._player_inside_cloud(
                    player_hitbox
                )
            )

            if self.player_exposed:
                # Shield-ul filtrează o mare parte din radiație.
                exposure_increase = (
                    0.20
                    if player_shielded
                    else 0.72
                )
                self.exposure = min(
                    MAX_RADIATION_EXPOSURE,
                    self.exposure + exposure_increase,
                )
            else:
                self.exposure = max(
                    0.0,
                    self.exposure - 0.52,
                )

            player_was_hit = False

            if self.exposure >= MAX_RADIATION_EXPOSURE:
                # Păstrăm puțină expunere pentru a descuraja staționarea.
                self.exposure = 25.0
                player_was_hit = True

            if self.active_timer <= 0:
                self.state = "recovery"
                self.recovery_timer = RADIATION_RECOVERY_DURATION
                self.player_exposed = False

            return player_was_hit

        if self.state == "recovery":
            self.recovery_timer -= 1
            self.player_exposed = False
            self.exposure = max(
                0.0,
                self.exposure - 1.4,
            )

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Creează 4–6 nori, fără să acopere simultan întreaga arenă.
    def _create_clouds(self, wave):
        cloud_count = min(
            6,
            4 + max(0, int(wave) - 1) // 3,
        )
        horizontal_spacing = (
            self.screen_width + 440
        ) / cloud_count
        self.clouds = []

        for cloud_index in range(cloud_count):
            radius = random.randint(112, 148)
            cloud_x = (
                -220
                + cloud_index * horizontal_spacing
                + random.randint(-45, 45)
            )
            cloud_y = random.randint(
                155,
                self.screen_height - 105,
            )
            cloud_sprite = None
            if self.cloud_images:
                base_image = self.cloud_images[
                    cloud_index % len(self.cloud_images)
                ]
                cloud_sprite = pygame.transform.rotozoom(
                    base_image,
                    random.uniform(0, 360),
                    random.uniform(0.92, 1.08),
                )
                sprite_bounds = cloud_sprite.get_bounding_rect(
                    min_alpha=8
                )
                if (
                    sprite_bounds.width > 0
                    and sprite_bounds.height > 0
                ):
                    cloud_sprite = cloud_sprite.subsurface(
                        sprite_bounds
                    ).copy()

            self.clouds.append(
                {
                    "x": float(cloud_x),
                    "y": float(cloud_y),
                    "base_y": float(cloud_y),
                    "radius": radius,
                    "speed": random.uniform(1.05, 1.65),
                    "phase": random.uniform(0, math.tau),
                    "pulse_speed": random.uniform(0.012, 0.022),
                    "visual_scale": random.uniform(0.94, 1.08),
                    "sprite": cloud_sprite,
                }
            )

    # Deplasează norii spre dreapta și îi reciclează după ieșirea din ecran.
    def _move_clouds(self, speed_multiplier):
        for cloud in self.clouds:
            cloud["x"] += (
                cloud["speed"] * speed_multiplier
            )
            cloud["y"] = (
                cloud["base_y"]
                + math.sin(
                    self.animation_timer * 0.018
                    + cloud["phase"]
                )
                * 34
            )

            if (
                cloud["x"] - cloud["radius"]
                > self.screen_width
            ):
                cloud["x"] = float(
                    -cloud["radius"] - 80
                )
                cloud["base_y"] = float(
                    random.randint(
                        155,
                        self.screen_height - 105,
                    )
                )

    # Verifică dacă centrul navei se află în miezul unui nor.
    def _player_inside_cloud(self, player_hitbox):
        for cloud in self.clouds:
            distance = math.hypot(
                player_hitbox.centerx - cloud["x"],
                player_hitbox.centery - cloud["y"],
            )

            if distance <= cloud["radius"] * 0.78:
                return True

        return False

    # Desenează norii, avertizarea și bara de expunere.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_clouds(screen)

        if self.player_exposed and self.state == "active":
            self._draw_contamination_feedback(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "RADIATION CLOUD APPROACHING",
                f"SEALING COCKPIT: {seconds_remaining}",
                (145, 255, 85),
            )

        elif self.state == "active":
            if self.player_exposed:
                subtitle = "EXPOSURE RISING - LEAVE THE CLOUD"
                accent_color = (255, 205, 60)
            else:
                subtitle = "CLEAR AIR - EXPOSURE DECREASING"
                accent_color = (135, 255, 105)

            self._draw_status_banner(
                screen,
                "RADIATION CLOUD",
                subtitle,
                accent_color,
            )
            self._draw_exposure_bar(screen)

        elif self.state == "recovery":
            self._draw_status_banner(
                screen,
                "RADIATION LEVELS FALLING",
                "ATMOSPHERE STABILIZING",
                (125, 230, 175),
            )
            self._draw_exposure_bar(screen)

    # Desenează sprite-urile organice, pulsația și particulele radioactive.
    def _draw_clouds(self, screen):
        cloud_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        if self.state == "warning":
            alpha_multiplier = 0.48
        elif self.state == "recovery":
            alpha_multiplier = max(
                0.12,
                self.recovery_timer
                / RADIATION_RECOVERY_DURATION,
            )
        else:
            alpha_multiplier = 1.0

        cloud_surface.fill(
            (
                25,
                65,
                20,
                int(9 * alpha_multiplier),
            )
        )

        for cloud in self.clouds:
            radius = cloud["radius"]
            pulse = (
                1.0
                + math.sin(
                    self.animation_timer * cloud["pulse_speed"]
                    + cloud["phase"]
                )
                * 0.035
            )
            visual_diameter = int(
                radius
                * 2.18
                * cloud["visual_scale"]
                * pulse
            )
            cloud_sprite = cloud["sprite"]

            if cloud_sprite is not None:
                sprite_scale = (
                    visual_diameter
                    / max(
                        cloud_sprite.get_width(),
                        cloud_sprite.get_height(),
                    )
                )
                draw_width = max(
                    1,
                    int(cloud_sprite.get_width() * sprite_scale),
                )
                draw_height = max(
                    1,
                    int(cloud_sprite.get_height() * sprite_scale),
                )
                draw_image = pygame.transform.smoothscale(
                    cloud_sprite,
                    (draw_width, draw_height),
                )
                draw_image.set_alpha(
                    int(132 * alpha_multiplier)
                )
                cloud_surface.blit(
                    draw_image,
                    draw_image.get_rect(
                        center=(
                            int(cloud["x"]),
                            int(cloud["y"]),
                        )
                    ),
                )
            else:
                # Rezervă simplă dacă niciun PNG nu este disponibil.
                pygame.draw.circle(
                    cloud_surface,
                    (
                        85,
                        150,
                        50,
                        int(42 * alpha_multiplier),
                    ),
                    (int(cloud["x"]), int(cloud["y"])),
                    radius,
                )

            # Motele din interior fac norul să pară activ, fără contur circular.
            for mote_index in range(9):
                mote_angle = (
                    cloud["phase"]
                    + mote_index * math.tau / 9
                    + self.animation_timer * 0.006
                )
                mote_distance = radius * (
                    0.20 + (mote_index % 4) * 0.15
                )
                mote_x = int(
                    cloud["x"]
                    + math.cos(mote_angle) * mote_distance
                )
                mote_y = int(
                    cloud["y"]
                    + math.sin(mote_angle * 1.3)
                    * mote_distance
                    * 0.72
                )
                mote_alpha = int(
                    (55 + (mote_index % 3) * 25)
                    * alpha_multiplier
                )
                pygame.draw.circle(
                    cloud_surface,
                    (175, 255, 80, mote_alpha),
                    (mote_x, mote_y),
                    1 + mote_index % 2,
                )

        screen.blit(cloud_surface, (0, 0))

    # Semnalizează contaminarea prin vignette și interferențe discrete.
    def _draw_contamination_feedback(self, screen):
        feedback_surface = pygame.Surface(
            (self.screen_width, self.screen_height),
            pygame.SRCALPHA,
        )
        exposure_ratio = min(
            1.0,
            self.exposure / MAX_RADIATION_EXPOSURE,
        )

        # Straturile de la margine formează o vignette, nu un chenar solid.
        for layer_index in range(10):
            layer_alpha = int(
                (18 + exposure_ratio * 32)
                * (1.0 - layer_index / 10) ** 2
            )
            inset = layer_index * 9
            pygame.draw.rect(
                feedback_surface,
                (90, 230, 55, layer_alpha),
                (
                    inset,
                    inset,
                    self.screen_width - inset * 2,
                    self.screen_height - inset * 2,
                ),
                10,
            )

        # Linii fine, deplasate în timp, sugerează interferența senzorilor.
        scan_offset = self.animation_timer % 22
        scan_alpha = int(7 + exposure_ratio * 12)
        for scan_y in range(
            scan_offset,
            self.screen_height,
            22,
        ):
            pygame.draw.line(
                feedback_surface,
                (160, 255, 105, scan_alpha),
                (0, scan_y),
                (self.screen_width, scan_y),
                1,
            )

        # Fragmentele scurte apar doar în expunere și nu ascund proiectilele.
        for fragment_index in range(12):
            fragment_x = (
                fragment_index * 109
                + self.animation_timer * 3
            ) % self.screen_width
            fragment_y = (
                fragment_index * 71
                + self.animation_timer
            ) % self.screen_height
            pygame.draw.line(
                feedback_surface,
                (190, 255, 120, int(20 + exposure_ratio * 35)),
                (fragment_x, fragment_y),
                (fragment_x + 8 + fragment_index % 9, fragment_y),
                1,
            )

        screen.blit(feedback_surface, (0, 0))

    # Afișează numeric și vizual expunerea acumulată.
    def _draw_exposure_bar(self, screen):
        bar_width = 420
        bar_height = 20
        bar_x = self.screen_width // 2 - bar_width // 2
        # Bara stă sub panoul evenimentului, fără să acopere nava.
        bar_y = 156
        exposure_ratio = min(
            1.0,
            self.exposure / MAX_RADIATION_EXPOSURE,
        )

        if exposure_ratio < 0.5:
            bar_color = (115, 235, 75)
        elif exposure_ratio < 0.8:
            bar_color = (255, 205, 55)
        else:
            bar_color = (255, 70, 65)

        label_surface = self.exposure_font.render(
            (
                "RADIATION EXPOSURE  "
                f"{int(self.exposure)}%"
            ),
            True,
            (225, 245, 220),
        )
        screen.blit(
            label_surface,
            (
                self.screen_width // 2
                - label_surface.get_width() // 2,
                bar_y - 25,
            ),
        )
        pygame.draw.rect(
            screen,
            (15, 25, 20),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=7,
        )
        pygame.draw.rect(
            screen,
            bar_color,
            (
                bar_x,
                bar_y,
                int(bar_width * exposure_ratio),
                bar_height,
            ),
            border_radius=7,
        )
        pygame.draw.rect(
            screen,
            (190, 245, 175),
            (bar_x, bar_y, bar_width, bar_height),
            2,
            border_radius=7,
        )

    # Desenează panoul comun al evenimentului radioactiv.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (650, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (7, 17, 8, 215),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 175),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (225, 240, 220),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Simulează o singularitate care atrage radial obiectele din arenă.
class BlackHolePulseEvent:

    # Creează fonturile și valorile vizuale ale evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.singularity_image = (
            self._load_singularity_image()
        )
        self.reset()

    # Încarcă singularitatea premium și elimină marginile transparente.
    def _load_singularity_image(self):
        image_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "images"
            / "effects"
            / "black_hole_singularity.png"
        )

        if not image_path.exists():
            return None

        try:
            singularity_image = pygame.image.load(
                str(image_path)
            ).convert_alpha()
            visible_bounds = singularity_image.get_bounding_rect(
                min_alpha=8
            )
            if (
                visible_bounds.width > 0
                and visible_bounds.height > 0
            ):
                singularity_image = singularity_image.subsurface(
                    visible_bounds
                ).copy()

            # Redimensionarea se face o singură dată, nu în fiecare cadru.
            return pygame.transform.smoothscale(
                singularity_image,
                (360, 360),
            )
        except pygame.error:
            # Evenimentul rămâne funcțional și dacă imaginea lipsește.
            return None

    # Readuce singularitatea în starea inactivă.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.animation_timer = 0
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 3
        self.base_strength = 0.0
        self.current_strength = 0.0
        self.pulse_number = 1
        self.pulse_elapsed = 0
        self.damage_cooldown = 0
        self.horizon_radius = 68
        self.absorption_radius = 50

    # Alege o poziție sigură și calculează puterea după wave.
    def start(self, wave):
        self.state = "warning"
        self.warning_timer = BLACK_HOLE_WARNING_DURATION
        self.animation_timer = 0
        self.center_x = random.randint(
            270,
            self.screen_width - 270,
        )
        self.center_y = random.randint(
            185,
            min(365, self.screen_height - 260),
        )
        self.base_strength = min(
            3.15,
            1.65 + max(1, int(wave)) * 0.13,
        )
        self.current_strength = 0.0
        self.pulse_number = 1
        self.pulse_elapsed = 0
        self.damage_cooldown = 0

    # Actualizează avertizarea, cele trei impulsuri și contracția.
    def update(self, player_hitbox, wave):
        del wave
        self.animation_timer += 1

        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = BLACK_HOLE_ACTIVE_DURATION

            return False

        if self.state == "active":
            self.active_timer -= 1
            self._update_pulse_strength()
            player_was_hit = False
            player_distance = math.hypot(
                player_hitbox.centerx - self.center_x,
                player_hitbox.centery - self.center_y,
            )

            if (
                player_distance <= self.horizon_radius
                and self.damage_cooldown <= 0
            ):
                player_was_hit = True
                self.damage_cooldown = 90

            if self.active_timer <= 0:
                self.state = "recovery"
                self.recovery_timer = (
                    BLACK_HOLE_RECOVERY_DURATION
                )
                self.current_strength = 0.0

            return player_was_hit

        if self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Calculează intensitatea fazei curente din fiecare impuls.
    def _update_pulse_strength(self):
        elapsed = (
            BLACK_HOLE_ACTIVE_DURATION
            - self.active_timer
        )
        self.pulse_number = min(
            BLACK_HOLE_TOTAL_PULSES,
            elapsed // BLACK_HOLE_PULSE_DURATION + 1,
        )
        self.pulse_elapsed = (
            elapsed % BLACK_HOLE_PULSE_DURATION
        )
        pulse_bonus = (
            1.0 + (self.pulse_number - 1) * 0.18
        )

        if self.pulse_elapsed < 70:
            charge_progress = self.pulse_elapsed / 70
            phase_multiplier = (
                0.32 + charge_progress * 0.42
            )
        elif self.pulse_elapsed < 185:
            surge_progress = (
                self.pulse_elapsed - 70
            ) / 115
            phase_multiplier = (
                1.0
                + math.sin(surge_progress * math.pi)
                * 0.28
            )
        else:
            phase_multiplier = 0.36

        self.current_strength = (
            self.base_strength
            * pulse_bonus
            * phase_multiplier
        )

    # Returnează datele necesare fizicii din gameplay.
    def get_gravity_data(self):
        if self.state != "active":
            return None

        return (
            float(self.center_x),
            float(self.center_y),
            self.current_strength,
            self.horizon_radius,
            self.absorption_radius,
        )

    # Desenează singularitatea, impulsurile și mesajele de avertizare.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_space_tint(screen)
        self._draw_singularity(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "GRAVITATIONAL COLLAPSE DETECTED",
                f"SINGULARITY FORMING IN {seconds_remaining}",
                (205, 115, 255),
            )

        elif self.state == "active":
            if self.pulse_elapsed < 70:
                subtitle = "GRAVITY SURGE CHARGING"
                accent_color = (175, 120, 255)
            elif self.pulse_elapsed < 185:
                subtitle = "ESCAPE THE EVENT HORIZON"
                accent_color = (255, 95, 220)
            else:
                subtitle = "GRAVITY TEMPORARILY WEAKENED"
                accent_color = (125, 190, 255)

            self._draw_status_banner(
                screen,
                (
                    "BLACK HOLE PULSE "
                    f"{self.pulse_number}"
                    f"/{BLACK_HOLE_TOTAL_PULSES}"
                ),
                subtitle,
                accent_color,
            )

        elif self.state == "recovery":
            self._draw_status_banner(
                screen,
                "SINGULARITY COLLAPSING",
                "GRAVITY FIELD DISSIPATING",
                (130, 195, 255),
            )

    # Întunecă discret marginile ecranului în jurul singularității.
    def _draw_space_tint(self, screen):
        tint_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        if self.state == "active":
            tint_alpha = 34
        elif self.state == "warning":
            tint_alpha = 18
        else:
            tint_alpha = 12

        tint_surface.fill(
            (32, 5, 55, tint_alpha)
        )
        screen.blit(tint_surface, (0, 0))

    # Desenează sprite-ul rotativ, lensing-ul, particulele și impulsurile.
    def _draw_singularity(self, screen):
        effect_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        if self.state == "warning":
            size_multiplier = (
                1.0
                - self.warning_timer
                / BLACK_HOLE_WARNING_DURATION
            )
            size_multiplier = max(
                0.18,
                size_multiplier,
            )
        elif self.state == "recovery":
            size_multiplier = max(
                0.12,
                self.recovery_timer
                / BLACK_HOLE_RECOVERY_DURATION,
            )
        else:
            size_multiplier = 1.0

        pulse_scale = 1.0
        if self.state == "active":
            pulse_scale += math.sin(
                self.pulse_elapsed
                / BLACK_HOLE_PULSE_DURATION
                * math.tau
            ) * 0.035

        visual_scale = size_multiplier * pulse_scale
        glow_radius = max(8, int(184 * visual_scale))

        # Halourile discrete integrează sprite-ul în fundalul arenei.
        pygame.draw.circle(
            effect_surface,
            (72, 35, 175, 28),
            (self.center_x, self.center_y),
            glow_radius,
        )
        pygame.draw.circle(
            effect_surface,
            (110, 70, 235, 34),
            (self.center_x, self.center_y),
            max(5, int(glow_radius * 0.76)),
            max(1, int(7 * visual_scale)),
        )

        if self.singularity_image is not None:
            rotation_angle = -(
                self.animation_timer * 0.22
            )
            rotated_image = pygame.transform.rotozoom(
                self.singularity_image,
                rotation_angle,
                visual_scale,
            )

            if self.state == "warning":
                formation_progress = (
                    1.0
                    - self.warning_timer
                    / BLACK_HOLE_WARNING_DURATION
                )
                rotated_image.set_alpha(
                    int(95 + formation_progress * 160)
                )
            elif self.state == "recovery":
                rotated_image.set_alpha(
                    int(255 * size_multiplier)
                )

            effect_surface.blit(
                rotated_image,
                rotated_image.get_rect(
                    center=(self.center_x, self.center_y)
                ),
            )
        else:
            # Variantă simplă de rezervă dacă PNG-ul nu poate fi încărcat.
            pygame.draw.circle(
                effect_surface,
                (85, 45, 205, 175),
                (self.center_x, self.center_y),
                max(8, int(145 * visual_scale)),
                max(2, int(16 * visual_scale)),
            )

        # Resturi luminoase orbitează în sensuri diferite spre centru.
        for particle_index in range(18):
            orbit_direction = 1 if particle_index % 2 == 0 else -1
            angle = (
                particle_index * math.tau / 18
                + self.animation_timer
                * 0.014
                * orbit_direction
            )
            orbit_radius = (
                126 + (particle_index % 4) * 15
            ) * visual_scale
            particle_x = int(
                self.center_x
                + math.cos(angle) * orbit_radius
            )
            particle_y = int(
                self.center_y
                + math.sin(angle) * orbit_radius
            )
            particle_color = (
                (255, 120, 235, 175)
                if particle_index % 3 == 0
                else (125, 185, 255, 155)
            )
            pygame.draw.circle(
                effect_surface,
                particle_color,
                (particle_x, particle_y),
                max(1, int(2.5 * visual_scale)),
            )

        # Centrul vizualizează separat absorbția și zona periculoasă.
        absorption_visual_radius = max(
            4,
            int(self.absorption_radius * size_multiplier),
        )
        horizon_visual_radius = max(
            5,
            int(self.horizon_radius * size_multiplier),
        )
        pygame.draw.circle(
            effect_surface,
            (0, 0, 4, 255),
            (self.center_x, self.center_y),
            absorption_visual_radius,
        )
        pygame.draw.circle(
            effect_surface,
            (210, 105, 255, 205),
            (self.center_x, self.center_y),
            horizon_visual_radius,
            max(1, int(2 * size_multiplier)),
        )

        # În faza puternică, un inel se extinde pentru fiecare impuls.
        if (
            self.state == "active"
            and 70 <= self.pulse_elapsed < 185
        ):
            surge_progress = (
                self.pulse_elapsed - 70
            ) / 115
            pulse_ring_radius = int(
                85 + surge_progress * 245
            )
            pulse_alpha = int(
                180 * (1.0 - surge_progress)
            )
            pygame.draw.circle(
                effect_surface,
                (210, 100, 255, pulse_alpha),
                (self.center_x, self.center_y),
                pulse_ring_radius,
                3,
            )
            second_ring_radius = int(
                125 + surge_progress * 205
            )
            pygame.draw.circle(
                effect_surface,
                (105, 175, 255, int(pulse_alpha * 0.62)),
                (self.center_x, self.center_y),
                second_ring_radius,
                2,
            )

        screen.blit(effect_surface, (0, 0))

    # Desenează panoul comun al evenimentului Black Hole Pulse.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (670, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (8, 2, 18, 220),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 180),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (230, 220, 245),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Coordonează trei valuri direcționale de asteroizi.
class AsteroidStormEvent:

    # Creează fonturile și valorile de bază ale evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.reset()

    # Readuce furtuna în starea inactivă.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.animation_timer = 0
        self.current_wave = 1
        self.wave_elapsed = 0
        self.spawn_timer = 0
        self.spawn_sequence = 0
        self.difficulty_wave = 1
        self.pending_spawn_requests = []

    # Pornește avertizarea și salvează wave-ul pentru dificultate.
    def start(self, wave):
        self.state = "warning"
        self.warning_timer = ASTEROID_WARNING_DURATION
        self.animation_timer = 0
        self.current_wave = 1
        self.wave_elapsed = 0
        self.spawn_timer = 1
        self.spawn_sequence = 0
        self.difficulty_wave = max(1, int(wave))
        self.pending_spawn_requests = []

    # Actualizează avertizarea, valurile și retragerea resturilor.
    def update(self, player_hitbox, wave):
        del player_hitbox
        del wave
        self.animation_timer += 1

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = ASTEROID_ACTIVE_DURATION
                self._begin_wave(1)

            return False

        if self.state == "active":
            self.active_timer -= 1
            elapsed = (
                ASTEROID_ACTIVE_DURATION
                - self.active_timer
            )
            calculated_wave = min(
                ASTEROID_TOTAL_WAVES,
                elapsed // ASTEROID_WAVE_DURATION + 1,
            )

            if calculated_wave != self.current_wave:
                self._begin_wave(calculated_wave)

            self.wave_elapsed = (
                elapsed % ASTEROID_WAVE_DURATION
            )
            self._update_spawning()

            if self.active_timer <= 0:
                self.state = "recovery"
                self.recovery_timer = ASTEROID_RECOVERY_DURATION
                self.pending_spawn_requests = []

        elif self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Pregătește o perioadă scurtă de avertizare pentru noua direcție.
    def _begin_wave(self, wave_number):
        self.current_wave = wave_number
        self.wave_elapsed = 0
        self.spawn_timer = 1
        self.spawn_sequence = 0

    # Creează cereri de spawn după terminarea avertizării direcționale.
    def _update_spawning(self):
        if self.wave_elapsed < ASTEROID_TELEGRAPH_DURATION:
            return

        # Ultimele cadre permit asteroizilor să iasă înainte de alt val.
        if self.wave_elapsed >= ASTEROID_WAVE_DURATION - 25:
            return

        self.spawn_timer -= 1

        if self.spawn_timer > 0:
            return

        self.spawn_sequence += 1

        if self.current_wave == 1:
            self.pending_spawn_requests.extend(
                [
                    ("small", "top"),
                    ("small", "top"),
                ]
            )
            self.spawn_timer = 20

        elif self.current_wave == 2:
            entry_direction = (
                "left"
                if self.spawn_sequence % 2 == 0
                else "right"
            )
            size_type = (
                "large"
                if self.spawn_sequence % 4 == 0
                else "medium"
            )
            self.pending_spawn_requests.append(
                (size_type, entry_direction)
            )
            self.spawn_timer = 25

        else:
            first_direction = (
                "diagonal_left"
                if self.spawn_sequence % 2 == 0
                else "diagonal_right"
            )
            second_direction = (
                "diagonal_right"
                if first_direction == "diagonal_left"
                else "diagonal_left"
            )
            size_cycle = (
                "large"
                if self.spawn_sequence % 5 == 0
                else "medium"
            )
            self.pending_spawn_requests.extend(
                [
                    (size_cycle, first_direction),
                    ("small", second_direction),
                ]
            )
            self.spawn_timer = 19

    # Returnează cererile curente o singură dată către gameplay.
    def consume_spawn_requests(self):
        requests = self.pending_spawn_requests[:]
        self.pending_spawn_requests.clear()
        return requests

    # Returnează wave-ul gameplay-ului pentru viteza asteroizilor.
    def get_difficulty_wave(self):
        return self.difficulty_wave

    # Desenează avertizarea direcțională și starea furtunii.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_motion_streaks(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "ASTEROID STORM INBOUND",
                f"IMPACT VECTORS IN {seconds_remaining}",
                (255, 155, 85),
            )

        elif self.state == "active":
            direction_label = self._get_direction_label()

            if self.wave_elapsed < ASTEROID_TELEGRAPH_DURATION:
                subtitle = (
                    "VECTOR LOCKED: "
                    f"{direction_label}"
                )
                accent_color = (255, 205, 105)
            else:
                subtitle = (
                    "IMPACT DIRECTION: "
                    f"{direction_label}"
                )
                accent_color = (225, 145, 255)

            self._draw_status_banner(
                screen,
                (
                    "ASTEROID WAVE "
                    f"{self.current_wave}"
                    f"/{ASTEROID_TOTAL_WAVES}"
                ),
                subtitle,
                accent_color,
            )

        elif self.state == "recovery":
            self._draw_status_banner(
                screen,
                "ASTEROID STORM CLEAR",
                "DEBRIS LEAVING COMBAT ZONE",
                (130, 210, 255),
            )

    # Returnează numele direcției curente pentru interfață.
    def _get_direction_label(self):
        if self.current_wave == 1:
            return "ABOVE"

        if self.current_wave == 2:
            return "LEFT + RIGHT"

        return "CROSSING DIAGONALS"

    # Desenează urme care indică vizual vectorul atacului curent.
    def _draw_motion_streaks(self, screen):
        streak_surface = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )

        if self.state == "warning":
            streak_alpha = 30
        elif self.state == "active":
            streak_alpha = 55
        else:
            streak_alpha = 20

        for streak_index in range(16):
            offset = (
                streak_index * 97
                + self.animation_timer * 7
            )

            if self.current_wave == 1:
                streak_x = offset % self.screen_width
                streak_y = (
                    streak_index * 53
                    + self.animation_timer * 8
                ) % self.screen_height
                start_position = (streak_x, streak_y)
                end_position = (streak_x, streak_y + 55)
            elif self.current_wave == 2:
                streak_x = offset % self.screen_width
                streak_y = (
                    120 + streak_index * 37
                ) % self.screen_height
                start_position = (streak_x, streak_y)
                end_position = (streak_x + 65, streak_y)
            else:
                streak_x = offset % self.screen_width
                streak_y = (
                    streak_index * 61
                    + self.animation_timer * 5
                ) % self.screen_height
                diagonal_direction = (
                    1 if streak_index % 2 == 0 else -1
                )
                start_position = (streak_x, streak_y)
                end_position = (
                    streak_x + 55 * diagonal_direction,
                    streak_y + 55,
                )

            pygame.draw.line(
                streak_surface,
                (210, 145, 255, streak_alpha),
                start_position,
                end_position,
                2,
            )

        screen.blit(streak_surface, (0, 0))

    # Desenează panoul comun al evenimentului Asteroid Storm.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (620, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (16, 7, 18, 218),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 180),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (240, 225, 245),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Coordonează intrarea, fazele și retragerea turelelor Crossfire.
class CrossfireProtocolEvent:

    # Creează fonturile și valorile folosite de interfață.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.reset()

    # Readuce evenimentul în starea inactivă.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.animation_timer = 0
        self.current_phase = 1
        self.deployment_requested = False
        self.final_salvo_requested = False
        self.completed_early = False

    # Pornește avertizarea formației de blocadă.
    def start(self):
        self.state = "warning"
        self.warning_timer = CROSSFIRE_WARNING_DURATION
        self.animation_timer = 0
        self.current_phase = 1
        self.deployment_requested = False
        self.final_salvo_requested = False
        self.completed_early = False

    # Actualizează avertizarea, fazele de atac și finalul.
    def update(self, player_hitbox, wave):
        del player_hitbox
        del wave
        self.animation_timer += 1

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = CROSSFIRE_ACTIVE_DURATION
                self.current_phase = 1
                self.deployment_requested = True

        elif self.state == "active":
            self.active_timer -= 1
            elapsed = (
                CROSSFIRE_ACTIVE_DURATION
                - self.active_timer
            )
            self.current_phase = min(
                CROSSFIRE_TOTAL_PHASES,
                elapsed // CROSSFIRE_PHASE_DURATION + 1,
            )

            if self.active_timer <= 0:
                self.state = "recovery"
                self.recovery_timer = CROSSFIRE_RECOVERY_DURATION
                self.final_salvo_requested = True

        elif self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Returnează o singură comandă pentru crearea celor patru turele.
    def consume_deployment_request(self):
        if not self.deployment_requested:
            return False

        self.deployment_requested = False
        return True

    # Returnează o singură comandă pentru salva finală simultană.
    def consume_final_salvo_request(self):
        if not self.final_salvo_requested:
            return False

        self.final_salvo_requested = False
        return True

    # Încheie atacul anticipat după distrugerea tuturor turelelor.
    def notify_all_turrets_destroyed(self):
        if self.state != "active":
            return False

        self.completed_early = True
        self.state = "recovery"
        self.recovery_timer = CROSSFIRE_RECOVERY_DURATION
        self.final_salvo_requested = False
        return True

    # Desenează avertizarea, faza și mesajul de final.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_targeting_overlay(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "CROSSFIRE PROTOCOL DETECTED",
                f"HOSTILE BLOCKADE IN {seconds_remaining}",
                (255, 75, 155),
            )

        elif self.state == "active":
            if self.current_phase == 1:
                subtitle = "TARGETED FAN BARRAGE"
                accent_color = (255, 105, 165)
            elif self.current_phase == 2:
                subtitle = "PINCER CROSSFIRE"
                accent_color = (255, 145, 80)
            else:
                subtitle = "SATURATION FIRE"
                accent_color = (205, 105, 255)

            self._draw_status_banner(
                screen,
                (
                    "CROSSFIRE PHASE "
                    f"{self.current_phase}"
                    f"/{CROSSFIRE_TOTAL_PHASES}"
                ),
                subtitle,
                accent_color,
            )

        elif self.state == "recovery":
            if self.completed_early:
                title = "BLOCKADE DESTROYED"
                subtitle = "TACTICAL BONUS AWARDED"
                accent_color = (105, 245, 255)
            else:
                title = "BLOCKADE WITHDRAWING"
                subtitle = "FINAL SALVO DETECTED"
                accent_color = (255, 145, 90)

            self._draw_status_banner(
                screen,
                title,
                subtitle,
                accent_color,
            )

    # Desenează marcaje tactice în colțurile arenei.
    def _draw_targeting_overlay(self, screen):
        overlay = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )
        bracket_color = (
            255,
            55,
            145,
            75 if self.state == "active" else 45,
        )
        bracket_size = 75
        margin = 18
        corner_data = [
            (margin, margin, 1, 1),
            (self.screen_width - margin, margin, -1, 1),
            (margin, self.screen_height - margin, 1, -1),
            (
                self.screen_width - margin,
                self.screen_height - margin,
                -1,
                -1,
            ),
        ]

        for corner_x, corner_y, direction_x, direction_y in corner_data:
            pygame.draw.line(
                overlay,
                bracket_color,
                (corner_x, corner_y),
                (
                    corner_x + bracket_size * direction_x,
                    corner_y,
                ),
                3,
            )
            pygame.draw.line(
                overlay,
                bracket_color,
                (corner_x, corner_y),
                (
                    corner_x,
                    corner_y + bracket_size * direction_y,
                ),
                3,
            )

        screen.blit(overlay, (0, 0))

    # Desenează panoul comun al evenimentului Crossfire Protocol.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (660, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (17, 3, 15, 220),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 180),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (240, 225, 240),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Coordonează cele trei salve ale atacului cu rachete ghidate.
class MissileBarrageEvent:

    # Creează fonturile și valorile interfeței evenimentului.
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title_font = pygame.font.Font(
            None,
            48,
        )
        self.small_font = pygame.font.Font(
            None,
            27,
        )
        self.reset()

    # Readuce toate salvele în starea inactivă.
    def reset(self):
        self.state = "idle"
        self.warning_timer = 0
        self.active_timer = 0
        self.recovery_timer = 0
        self.animation_timer = 0
        self.current_salvo = 1
        self.salvo_elapsed = 0
        self.salvo_launched = False
        self.difficulty_wave = 1
        self.pending_launch_requests = []

    # Pornește alarma și salvează wave-ul pentru dificultate.
    def start(self, wave):
        self.state = "warning"
        self.warning_timer = MISSILE_WARNING_DURATION
        self.animation_timer = 0
        self.current_salvo = 1
        self.salvo_elapsed = 0
        self.salvo_launched = False
        self.difficulty_wave = max(1, int(wave))
        self.pending_launch_requests = []

    # Actualizează avertizarea, lock-on-ul și lansarea fiecărei salve.
    def update(self, player_hitbox, wave):
        del player_hitbox
        del wave
        self.animation_timer += 1

        if self.state == "warning":
            self.warning_timer -= 1

            if self.warning_timer <= 0:
                self.state = "active"
                self.active_timer = MISSILE_ACTIVE_DURATION
                self._begin_salvo(1)

            return False

        if self.state == "active":
            self.active_timer -= 1
            elapsed = (
                MISSILE_ACTIVE_DURATION
                - self.active_timer
            )
            calculated_salvo = min(
                MISSILE_TOTAL_SALVOS,
                elapsed // MISSILE_SALVO_DURATION + 1,
            )

            if calculated_salvo != self.current_salvo:
                self._begin_salvo(calculated_salvo)

            self.salvo_elapsed = (
                elapsed % MISSILE_SALVO_DURATION
            )

            if (
                self.salvo_elapsed >= MISSILE_LOCK_DURATION
                and not self.salvo_launched
            ):
                self._queue_current_salvo()
                self.salvo_launched = True

            if self.active_timer <= 0:
                self.state = "recovery"
                self.recovery_timer = MISSILE_RECOVERY_DURATION
                self.pending_launch_requests = []

        elif self.state == "recovery":
            self.recovery_timer -= 1

            if self.recovery_timer <= 0:
                self.state = "finished"

        return False

    # Resetează timerul de lock-on pentru noua salvă.
    def _begin_salvo(self, salvo_number):
        self.current_salvo = salvo_number
        self.salvo_elapsed = 0
        self.salvo_launched = False

    # Adaugă tipurile și direcțiile salvate în coada gameplay-ului.
    def _queue_current_salvo(self):
        if self.current_salvo == 1:
            self.pending_launch_requests.extend(
                [
                    ("hunter", "top"),
                    ("hunter", "top"),
                    ("hunter", "top"),
                    ("hunter", "top"),
                ]
            )
        elif self.current_salvo == 2:
            self.pending_launch_requests.extend(
                [
                    ("hunter", "left"),
                    ("hunter", "right"),
                    ("heavy", "left"),
                    ("heavy", "right"),
                    ("hunter", "top"),
                ]
            )
        else:
            self.pending_launch_requests.extend(
                [
                    ("hunter", "top"),
                    ("hunter", "left"),
                    ("hunter", "right"),
                    ("interceptor", "left"),
                    ("interceptor", "right"),
                    ("heavy", "top"),
                    ("heavy", "top"),
                ]
            )

    # Returnează cererile de lansare o singură dată.
    def consume_launch_requests(self):
        launch_requests = self.pending_launch_requests[:]
        self.pending_launch_requests.clear()
        return launch_requests

    # Desenează alarma, numărul salvei și retragerea semnalelor.
    def draw(self, screen):
        if self.state in (
            "idle",
            "finished",
        ):
            return

        self._draw_lock_overlay(screen)

        if self.state == "warning":
            seconds_remaining = max(
                1,
                (self.warning_timer + 59) // 60,
            )
            self._draw_status_banner(
                screen,
                "MISSILE LOCK DETECTED",
                f"HOSTILE LAUNCH IN {seconds_remaining}",
                (255, 70, 120),
            )

        elif self.state == "active":
            if self.salvo_elapsed < MISSILE_LOCK_DURATION:
                seconds_to_launch = max(
                    1,
                    (
                        MISSILE_LOCK_DURATION
                        - self.salvo_elapsed
                        + 59
                    ) // 60,
                )
                subtitle = (
                    "TARGET LOCK: LAUNCH IN "
                    f"{seconds_to_launch}"
                )
                accent_color = (255, 105, 95)
            else:
                subtitle = "BREAK THE LOCK OR DESTROY MISSILES"
                accent_color = (255, 175, 75)

            self._draw_status_banner(
                screen,
                (
                    "MISSILE SALVO "
                    f"{self.current_salvo}"
                    f"/{MISSILE_TOTAL_SALVOS}"
                ),
                subtitle,
                accent_color,
            )

        elif self.state == "recovery":
            self._draw_status_banner(
                screen,
                "MISSILE NETWORK OFFLINE",
                "GUIDANCE SIGNAL TERMINATED",
                (115, 220, 255),
            )

    # Desenează marcaje de lock-on și semnale în jurul arenei.
    def _draw_lock_overlay(self, screen):
        overlay = pygame.Surface(
            (
                self.screen_width,
                self.screen_height,
            ),
            pygame.SRCALPHA,
        )
        pulse = (
            1.0
            + math.sin(self.animation_timer * 0.12)
            * 0.18
        )
        center = (
            self.screen_width // 2,
            self.screen_height // 2,
        )
        pygame.draw.circle(
            overlay,
            (255, 55, 105, 45),
            center,
            int(115 * pulse),
            2,
        )
        pygame.draw.circle(
            overlay,
            (255, 130, 75, 32),
            center,
            int(180 * pulse),
            2,
        )

        for signal_index in range(8):
            signal_angle = (
                signal_index * math.tau / 8
                + self.animation_timer * 0.018
            )
            signal_x = int(
                center[0] + math.cos(signal_angle) * 250
            )
            signal_y = int(
                center[1] + math.sin(signal_angle) * 145
            )
            pygame.draw.circle(
                overlay,
                (255, 70, 125, 75),
                (signal_x, signal_y),
                4,
            )

        screen.blit(overlay, (0, 0))

    # Desenează panoul comun al evenimentului Missile Barrage.
    def _draw_status_banner(
        self,
        screen,
        title,
        subtitle,
        accent_color,
    ):
        banner = pygame.Surface(
            (650, 104),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            banner,
            (19, 4, 12, 220),
            banner.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            banner,
            (*accent_color, 180),
            banner.get_rect(),
            2,
            border_radius=10,
        )

        title_surface = self.title_font.render(
            title,
            True,
            accent_color,
        )
        subtitle_surface = self.small_font.render(
            subtitle,
            True,
            (245, 228, 225),
        )
        banner.blit(
            title_surface,
            (
                banner.get_width() // 2
                - title_surface.get_width() // 2,
                12,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner.get_width() // 2
                - subtitle_surface.get_width()
                // 2,
                68,
            ),
        )
        screen.blit(
            banner,
            (
                self.screen_width // 2
                - banner.get_width() // 2,
                22,
            ),
        )


# Managerul oferă gameplay-ului un singur punct de acces la evenimente.
class SpaceEventManager:

    # Creează toate evenimentele disponibile în zona Dead Star.
    def __init__(self, screen_width, screen_height):
        self.solar_storm = SolarStormEvent(
            screen_width,
            screen_height,
        )

        self.gravity_wave = GravityWaveEvent(
            screen_width,
            screen_height,
        )

        self.reinforcements = ReinforcementEvent(
            screen_width,
            screen_height,
        )

        self.drone_swarm = DroneSwarmEvent(
            screen_width,
            screen_height,
        )

        self.radiation_cloud = RadiationCloudEvent(
            screen_width,
            screen_height,
        )

        self.black_hole_pulse = BlackHolePulseEvent(
            screen_width,
            screen_height,
        )

        self.asteroid_storm = AsteroidStormEvent(
            screen_width,
            screen_height,
        )

        self.crossfire_protocol = CrossfireProtocolEvent(
            screen_width,
            screen_height,
        )

        self.missile_barrage = MissileBarrageEvent(
            screen_width,
            screen_height,
        )

        # Lista permite adaugarea usoara a altor evenimente mai tarziu.
        self.events = [
            self.solar_storm,
            self.gravity_wave,
            self.reinforcements,
            self.drone_swarm,
            self.radiation_cloud,
            self.black_hole_pulse,
            self.asteroid_storm,
            self.crossfire_protocol,
            self.missile_barrage,
        ]

        self.reset()

    # Resetează toate evenimentele când începe o rundă nouă.
    def reset(self):
        for event in self.events:
            event.reset()

        self.current_event = None
        self.next_event_index = 0
        self.event_cooldown = INITIAL_EVENT_DELAY
        # Devine True numai dupa terminarea celui de-al noualea eveniment.
        # Gameplay-ul foloseste semnalul pentru a porni bossul final.
        self.all_events_completed = False

    # Actualizează evenimentul activ și returnează impactul produs.
    def update(
        self,
        player_hitbox,
        wave,
        player_shielded=False,
    ):
        # Cat timp nu exista un eveniment activ, numaram pana la urmatorul.
        if self.current_event is None:
            if self.all_events_completed:
                return False

            self.event_cooldown -= 1

            if self.event_cooldown <= 0:
                self._start_next_event(wave)

            return False

        if self.current_event is self.radiation_cloud:
            player_was_hit = (
                self.radiation_cloud.update(
                    player_hitbox,
                    wave,
                    player_shielded,
                )
            )
        else:
            player_was_hit = self.current_event.update(
                player_hitbox,
                wave,
            )

        # Evenimentul terminat este resetat, apoi incepe o pauza.
        if self.current_event.state == "finished":
            finished_final_event = (
                self.current_event is self.events[-1]
            )
            self.current_event.reset()
            self.current_event = None

            if finished_final_event:
                self.all_events_completed = True
                self.event_cooldown = 0
            else:
                self.event_cooldown = EVENT_COOLDOWN

        return player_was_hit

    # Pornește evenimentele în ordinea stabilită în lista self.events.
    def _start_next_event(self, wave):
        if self.next_event_index >= len(self.events):
            self.all_events_completed = True
            return

        self.current_event = self.events[
            self.next_event_index
        ]
        self.next_event_index += 1

        if self.current_event is self.gravity_wave:
            self.gravity_wave.start(wave)
        elif self.current_event is self.reinforcements:
            self.reinforcements.start()
        elif self.current_event is self.drone_swarm:
            self.drone_swarm.start(wave)
        elif self.current_event is self.radiation_cloud:
            self.radiation_cloud.start(wave)
        elif self.current_event is self.black_hole_pulse:
            self.black_hole_pulse.start(wave)
        elif self.current_event is self.asteroid_storm:
            self.asteroid_storm.start(wave)
        elif self.current_event is self.crossfire_protocol:
            self.crossfire_protocol.start()
        elif self.current_event is self.missile_barrage:
            self.missile_barrage.start(wave)
        else:
            self.solar_storm.start()

    # Desenează toate efectele evenimentului activ.
    def draw(self, screen):
        if self.current_event is not None:
            self.current_event.draw(screen)

    # Returnează True cât timp furtuna nu este în cooldown.
    def event_is_running(self):
        return self.current_event is not None

    # Anunta gameplay-ul ca toate cele noua challenge-uri s-au terminat.
    def final_boss_is_ready(self):
        return (
            self.all_events_completed
            and self.current_event is None
        )

    # Evenimentele care aduc propriile pericole opresc inamicii obișnuiți.
    # Gravity Wave și Radiation Cloud păstrează lupta normală activă.
    def blocks_enemy_spawns(self):
        return self.current_event in (
            self.solar_storm,
            self.drone_swarm,
            self.asteroid_storm,
            self.crossfire_protocol,
            self.missile_barrage,
        )

    # Ajuta gameplay-ul sa reduca, nu sa opreasca, lupta in Gravity Wave.
    def gravity_wave_is_running(self):
        return self.current_event is self.gravity_wave

    # Indică faza în care navele aliate luptă efectiv în arenă.
    def reinforcements_are_active(self):
        return (
            self.current_event is self.reinforcements
            and self.reinforcements.state == "active"
        )

    # Indică momentul în care navele aliate trebuie să se retragă.
    def reinforcements_are_departing(self):
        return (
            self.current_event is self.reinforcements
            and self.reinforcements.state == "recovery"
        )

    # Transmite gameplay-ului o singură comandă de creare a formației.
    def consume_reinforcement_deployment(self):
        if self.current_event is not self.reinforcements:
            return False

        return (
            self.reinforcements
            .consume_deployment_request()
        )

    # Returnează numărul de drone cerut de următorul grup de atac.
    def consume_drone_squad_deployment(self):
        if self.current_event is not self.drone_swarm:
            return 0

        return self.drone_swarm.consume_squad_request()

    # Indică retragerea tuturor dronelor rămase în viață.
    def drone_swarm_is_departing(self):
        return (
            self.current_event is self.drone_swarm
            and self.drone_swarm.state == "recovery"
        )

    # Indică faza activă pentru reducerea ritmului inamicilor normali.
    def radiation_cloud_is_active(self):
        return (
            self.current_event is self.radiation_cloud
            and self.radiation_cloud.state == "active"
        )

    # Indică faza activă pentru reducerea spawn-urilor obișnuite.
    def black_hole_is_active(self):
        return (
            self.current_event is self.black_hole_pulse
            and self.black_hole_pulse.state == "active"
        )

    # Oferă gameplay-ului centrul, forța și razele singularității.
    def get_black_hole_gravity_data(self):
        if self.current_event is not self.black_hole_pulse:
            return None

        return self.black_hole_pulse.get_gravity_data()

    # Transmite gameplay-ului asteroizii ceruți în cadrul curent.
    def consume_asteroid_spawn_requests(self):
        if self.current_event is not self.asteroid_storm:
            return []

        return self.asteroid_storm.consume_spawn_requests()

    # Returnează wave-ul folosit pentru viteza și rezistența asteroizilor.
    def get_asteroid_difficulty_wave(self):
        if self.current_event is not self.asteroid_storm:
            return 1

        return self.asteroid_storm.get_difficulty_wave()

    # Indică momentul în care toate resturile trebuie să iasă din arenă.
    def asteroid_storm_is_departing(self):
        return (
            self.current_event is self.asteroid_storm
            and self.asteroid_storm.state == "recovery"
        )

    # Returnează o singură comandă pentru crearea turelelor Crossfire.
    def consume_crossfire_deployment(self):
        if self.current_event is not self.crossfire_protocol:
            return False

        return (
            self.crossfire_protocol
            .consume_deployment_request()
        )

    # Returnează faza de atac folosită de turele.
    def get_crossfire_phase(self):
        if self.current_event is not self.crossfire_protocol:
            return 0

        if self.crossfire_protocol.state != "active":
            return 0

        return self.crossfire_protocol.current_phase

    # Returnează o singură comandă pentru ultima salvă simultană.
    def consume_crossfire_final_salvo(self):
        if self.current_event is not self.crossfire_protocol:
            return False

        return (
            self.crossfire_protocol
            .consume_final_salvo_request()
        )

    # Încheie evenimentul anticipat după distrugerea formației.
    def notify_crossfire_destroyed(self):
        if self.current_event is not self.crossfire_protocol:
            return False

        return (
            self.crossfire_protocol
            .notify_all_turrets_destroyed()
        )

    # Indică momentul în care turelele rămase trebuie să se retragă.
    def crossfire_is_departing(self):
        return (
            self.current_event is self.crossfire_protocol
            and self.crossfire_protocol.state == "recovery"
        )

    # Returneaza toate rachetele pe care gameplay-ul trebuie sa le creeze.
    def consume_missile_launch_requests(self):
        if self.current_event is not self.missile_barrage:
            return []

        return (
            self.missile_barrage
            .consume_launch_requests()
        )

    # Returneaza wave-ul folosit pentru reglarea vitezei rachetelor.
    def get_missile_difficulty_wave(self):
        if self.current_event is not self.missile_barrage:
            return 1

        return self.missile_barrage.difficulty_wave

    # In recovery, rachetele ramase pierd tinta si parasesc arena.
    def missile_barrage_is_departing(self):
        return (
            self.current_event is self.missile_barrage
            and self.missile_barrage.state == "recovery"
        )

    # Returneaza forta orizontala produsa asupra navei.
    def get_player_force(self):
        if self.current_event is self.gravity_wave:
            return self.gravity_wave.get_player_force()

        return 0.0

    # Returneaza deviatia aplicata tuturor proiectilelor.
    def get_projectile_curve(self):
        if self.current_event is self.gravity_wave:
            return self.gravity_wave.get_projectile_curve()

        return 0.0
