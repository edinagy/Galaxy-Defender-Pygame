import math
import random

import pygame


# Jucătorul trebuie să supraviețuiască acest timp în Asteroid Ocean.
SCENE_DURATION = 32.0

# Nava are trei puncte de integritate la începutul checkpoint-ului.
STARTING_HULL = 3


# Reprezintă un proiectil folosit numai în nivelul Asteroid Ocean.
class CampaignBullet:

    # Creează proiectilul în poziția primită.
    def __init__(self, x_position, y_position):
        self.x = float(x_position)
        self.y = float(y_position)
        self.speed = 760
        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            6,
            24,
        )

    # Deplasează proiectilul în sus în funcție de timpul dintre cadre.
    def update(self, delta_time):
        self.y -= self.speed * delta_time
        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    # Returnează True după ce proiectilul a ieșit din ecran.
    def is_off_screen(self):
        return self.y + self.rect.height < 0

    # Desenează proiectilul și o lumină albastră discretă.
    def draw(self, screen):
        glow_rect = pygame.Rect(
            self.rect.x - 3,
            self.rect.y - 3,
            self.rect.width + 6,
            self.rect.height + 6,
        )
        pygame.draw.rect(
            screen,
            (20, 95, 180),
            glow_rect,
            border_radius=4,
        )
        pygame.draw.rect(
            screen,
            (95, 225, 255),
            self.rect,
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (240, 255, 255),
            (
                self.rect.x + 2,
                self.rect.y,
                2,
                self.rect.height,
            ),
            border_radius=2,
        )


# Reprezintă un asteroid activ care poate lovi nava sau proiectilele.
class AsteroidObstacle:

    # Creează un asteroid cu dimensiune, viteză și rotație aleatorii.
    def __init__(self, screen_width, difficulty):
        self.size = random.randint(26, 68)
        self.x = float(
            random.randint(
                self.size,
                screen_width - self.size,
            )
        )
        self.y = float(-self.size * 2)

        self.speed = random.uniform(
            175 + difficulty * 35,
            265 + difficulty * 55,
        )
        self.horizontal_speed = random.uniform(
            -55,
            55,
        )
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(
            -95,
            95,
        )
        self.hit_flash_timer = 0.0

        # Asteroizii mari au nevoie de mai multe lovituri pentru a fi distruși.
        if self.size <= 34:
            self.maximum_health = 1
        elif self.size <= 49:
            self.maximum_health = 2
        else:
            self.maximum_health = 3

        # În ultima parte a nivelului, rocile mari devin și mai rezistente.
        if (
            difficulty >= 0.65
            and self.size >= 54
        ):
            self.maximum_health += 1

        self.health = self.maximum_health

        self.base_image = self._create_image()
        self.image = self.base_image
        self.rect = self.image.get_rect(
            center=(
                int(self.x),
                int(self.y),
            )
        )
        self.collision_rect = pygame.Rect(
            0,
            0,
            int(self.size * 1.35),
            int(self.size * 1.35),
        )
        self.collision_rect.center = self.rect.center

    # Construiește procedural forma neregulată și craterele asteroidului.
    def _create_image(self):
        surface_size = self.size * 2 + 12
        surface = pygame.Surface(
            (surface_size, surface_size),
            pygame.SRCALPHA,
        )
        center = surface_size // 2

        points = []
        point_count = random.randint(9, 13)

        for index in range(point_count):
            point_angle = (
                index / point_count
            ) * math.tau
            point_radius = self.size * random.uniform(
                0.72,
                1.0,
            )
            points.append(
                (
                    center
                    + math.cos(point_angle)
                    * point_radius,
                    center
                    + math.sin(point_angle)
                    * point_radius,
                )
            )

        pygame.draw.polygon(
            surface,
            (75, 83, 105),
            points,
        )
        pygame.draw.polygon(
            surface,
            (145, 170, 205),
            points,
            3,
        )

        # Adaugă pete și cratere pentru ca asteroizii să nu fie cercuri simple.
        for _ in range(random.randint(3, 6)):
            crater_radius = random.randint(
                max(3, self.size // 10),
                max(5, self.size // 4),
            )
            crater_x = center + random.randint(
                -self.size // 2,
                self.size // 2,
            )
            crater_y = center + random.randint(
                -self.size // 2,
                self.size // 2,
            )
            pygame.draw.circle(
                surface,
                (42, 49, 70),
                (crater_x, crater_y),
                crater_radius,
            )
            pygame.draw.arc(
                surface,
                (185, 205, 225),
                (
                    crater_x - crater_radius,
                    crater_y - crater_radius,
                    crater_radius * 2,
                    crater_radius * 2,
                ),
                math.pi,
                math.tau,
                2,
            )

        return surface

    # Deplasează și rotește asteroidul.
    def update(
        self,
        delta_time,
        screen_width,
    ):
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= delta_time

        self.y += self.speed * delta_time
        self.x += self.horizontal_speed * delta_time

        if self.x < -self.size:
            self.x = screen_width + self.size
        elif self.x > screen_width + self.size:
            self.x = -self.size

        self.angle += (
            self.rotation_speed * delta_time
        )
        self.image = pygame.transform.rotate(
            self.base_image,
            self.angle,
        )
        self.rect = self.image.get_rect(
            center=(
                int(self.x),
                int(self.y),
            )
        )
        self.collision_rect.center = self.rect.center

    # Scade rezistența asteroidului și anunță dacă acesta a fost distrus.
    def take_damage(self):
        self.health -= 1
        self.hit_flash_timer = 0.09
        self.horizontal_speed += random.uniform(
            -18,
            18,
        )
        return self.health <= 0

    # Returnează True când asteroidul a trecut de partea de jos.
    def is_off_screen(self, screen_height):
        return (
            self.y - self.size
            > screen_height + 30
        )

    # Desenează asteroidul rotit.
    def draw(self, screen):
        if self.hit_flash_timer > 0:
            flash_image = self.image.copy()
            flash_image.fill(
                (105, 120, 145, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            screen.blit(
                flash_image,
                self.rect,
            )
        else:
            screen.blit(
                self.image,
                self.rect,
            )


# Controlează primul nivel jucabil al campaniei.
class AsteroidScene:

    # Încarcă imaginile, fonturile și pregătește checkpoint-ul.
    def __init__(
        self,
        screen,
        background_path=(
            "assets/images/intro/"
            "asteroid_background.png"
        ),
    ):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        original_background = pygame.image.load(
            background_path
        ).convert()
        self.background = pygame.transform.smoothscale(
            original_background,
            (
                self.width + 50,
                self.height + 50,
            ),
        )

        ship_image = pygame.image.load(
            "assets/images/player_galaxy_defender_v2.png"
        ).convert_alpha()

        # Elimină marginile transparente ale noului sprite înainte de scalare.
        visible_bounds = ship_image.get_bounding_rect(min_alpha=8)
        if visible_bounds.width > 0 and visible_bounds.height > 0:
            ship_image = ship_image.subsurface(visible_bounds).copy()
        self.ship_image = pygame.transform.smoothscale(
            ship_image,
            (112, 128),
        )

        self.small_font = pygame.font.Font(None, 27)
        self.medium_font = pygame.font.Font(None, 42)
        self.title_font = pygame.font.Font(None, 72)

        self.reset()

    # Resetează complet nivelul la ultimul checkpoint sigur.
    def reset(self, starting_score=0):
        self.elapsed_time = 0.0
        self.spawn_timer = 0.18
        self.fire_cooldown = 0.0
        self.invincibility_timer = 0.0
        self.completion_timer = 0.0

        self.ship_x = float(
            self.width // 2
            - self.ship_image.get_width() // 2
        )
        self.ship_y = float(
            self.height
            - self.ship_image.get_height()
            - 35
        )
        self.ship_speed = 430

        self.hull = STARTING_HULL
        # Scorul primit reprezintă punctele salvate la checkpoint.
        self.checkpoint_score = max(
            0,
            int(starting_score),
        )
        self.score = self.checkpoint_score
        self.destroyed_asteroids = 0
        self.game_over = False
        self.completed = False
        self.finished = False

        self.bullets = []
        self.asteroids = []
        self.particles = []

    # Procesează tragerea, reluarea checkpoint-ului și revenirea la meniu.
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            return "menu"

        if self.game_over:
            if event.key == pygame.K_r:
                return "retry"
            return None

        if (
            event.key == pygame.K_SPACE
            and not self.completed
        ):
            self._shoot()

        return None

    # Actualizează toate mecanicile nivelului.
    def update(self, delta_time):
        if self.game_over:
            self._update_particles(delta_time)
            return None

        if self.fire_cooldown > 0:
            self.fire_cooldown -= delta_time

        if self.invincibility_timer > 0:
            self.invincibility_timer -= delta_time

        self._move_ship(delta_time)

        # Permite tragerea continuă cât timp jucătorul ține apăsat SPACE.
        if (
            pygame.key.get_pressed()[
                pygame.K_SPACE
            ]
            and not self.completed
        ):
            self._shoot()

        self._update_bullets(delta_time)
        self._update_asteroids(delta_time)
        self._update_particles(delta_time)
        self._check_collisions()

        if not self.completed:
            self.elapsed_time += delta_time
            self._spawn_asteroids(delta_time)

            if self.elapsed_time >= SCENE_DURATION:
                self.completed = True
                self.completion_timer = 0.0
        else:
            self.completion_timer += delta_time

            if (
                self.completion_timer >= 2.4
                and not self.finished
            ):
                self.finished = True
                return "anomaly"

        return None

    # Mută nava cu WASD sau săgeți și o păstrează în interiorul ecranului.
    def _move_ship(self, delta_time):
        keys = pygame.key.get_pressed()
        horizontal_direction = 0
        vertical_direction = 0

        if (
            keys[pygame.K_a]
            or keys[pygame.K_LEFT]
        ):
            horizontal_direction -= 1
        if (
            keys[pygame.K_d]
            or keys[pygame.K_RIGHT]
        ):
            horizontal_direction += 1
        if (
            keys[pygame.K_w]
            or keys[pygame.K_UP]
        ):
            vertical_direction -= 1
        if (
            keys[pygame.K_s]
            or keys[pygame.K_DOWN]
        ):
            vertical_direction += 1

        # Normalizează deplasarea diagonală, ca nava să nu fie mai rapidă.
        if (
            horizontal_direction != 0
            and vertical_direction != 0
        ):
            diagonal_factor = 1 / math.sqrt(2)
        else:
            diagonal_factor = 1

        self.ship_x += (
            horizontal_direction
            * self.ship_speed
            * diagonal_factor
            * delta_time
        )
        self.ship_y += (
            vertical_direction
            * self.ship_speed
            * diagonal_factor
            * delta_time
        )

        self.ship_x = max(
            0,
            min(
                self.width
                - self.ship_image.get_width(),
                self.ship_x,
            ),
        )
        self.ship_y = max(
            80,
            min(
                self.height
                - self.ship_image.get_height(),
                self.ship_y,
            ),
        )

    # Creează două proiectile în dreptul motoarelor laterale ale navei.
    def _shoot(self):
        if self.fire_cooldown > 0:
            return

        bullet_y = self.ship_y + 14
        self.bullets.append(
            CampaignBullet(
                self.ship_x + 24,
                bullet_y,
            )
        )
        self.bullets.append(
            CampaignBullet(
                self.ship_x
                + self.ship_image.get_width()
                - 30,
                bullet_y,
            )
        )
        self.fire_cooldown = 0.19

    # Actualizează proiectilele și le elimină după ieșirea din ecran.
    def _update_bullets(self, delta_time):
        for bullet in self.bullets[:]:
            bullet.update(delta_time)

            if bullet.is_off_screen():
                self.bullets.remove(bullet)

    # Creează asteroizi din ce în ce mai repede pe parcursul nivelului.
    def _spawn_asteroids(self, delta_time):
        self.spawn_timer -= delta_time

        if self.spawn_timer > 0:
            return

        difficulty = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )
        # La început apare câte un asteroid, apoi sunt posibile grupuri.
        spawn_count = 1

        if random.random() < (
            0.20 + difficulty * 0.35
        ):
            spawn_count += 1

        if (
            difficulty >= 0.70
            and random.random() < 0.18
        ):
            spawn_count += 1

        for _ in range(spawn_count):
            self.asteroids.append(
                AsteroidObstacle(
                    self.width,
                    difficulty,
                )
            )

        minimum_delay = 0.18
        maximum_delay = (
            0.55 - difficulty * 0.21
        )
        self.spawn_timer = random.uniform(
            minimum_delay,
            maximum_delay,
        )

    # Actualizează asteroizii și îi elimină când ies din ecran.
    def _update_asteroids(self, delta_time):
        difficulty = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )

        for asteroid in self.asteroids[:]:
            asteroid.update(
                delta_time,
                self.width,
            )

            # Accelerează discret valul în ultima parte a nivelului.
            asteroid.speed += (
                difficulty * 2.2 * delta_time
            )

            if asteroid.is_off_screen(
                self.height
            ):
                self.asteroids.remove(asteroid)

    # Verifică impacturile proiectilelor și coliziunile cu nava.
    def _check_collisions(self):
        for bullet in self.bullets[:]:
            hit_asteroid = None

            for asteroid in self.asteroids:
                if bullet.rect.colliderect(
                    asteroid.collision_rect
                ):
                    hit_asteroid = asteroid
                    break

            if hit_asteroid is not None:
                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                asteroid_destroyed = (
                    hit_asteroid.take_damage()
                )

                if asteroid_destroyed:
                    if (
                        hit_asteroid
                        in self.asteroids
                    ):
                        self.asteroids.remove(
                            hit_asteroid
                        )

                    self.destroyed_asteroids += 1
                    self.score += (
                        70
                        + hit_asteroid.size
                        + hit_asteroid.maximum_health
                        * 45
                    )
                    self._create_explosion(
                        hit_asteroid.x,
                        hit_asteroid.y,
                        (100, 195, 255),
                        18,
                    )
                else:
                    # O lovitură care nu distruge roca oferă feedback și puncte.
                    self.score += 10
                    self._create_explosion(
                        bullet.rect.centerx,
                        bullet.rect.centery,
                        (175, 225, 255),
                        5,
                    )

        if self.invincibility_timer > 0:
            return

        ship_hitbox = pygame.Rect(
            int(self.ship_x + 25),
            int(self.ship_y + 20),
            self.ship_image.get_width() - 50,
            self.ship_image.get_height() - 42,
        )

        for asteroid in self.asteroids[:]:
            if not ship_hitbox.colliderect(
                asteroid.collision_rect
            ):
                continue

            self.asteroids.remove(asteroid)
            self.hull -= 1
            self.invincibility_timer = 1.6
            self._create_explosion(
                asteroid.x,
                asteroid.y,
                (255, 125, 85),
                22,
            )

            if self.hull <= 0:
                self.game_over = True
                self._create_explosion(
                    self.ship_x
                    + self.ship_image.get_width() / 2,
                    self.ship_y
                    + self.ship_image.get_height() / 2,
                    (105, 195, 255),
                    36,
                )
            break

    # Creează particulele folosite pentru impacturi și explozii.
    def _create_explosion(
        self,
        x_position,
        y_position,
        color,
        particle_count,
    ):
        for _ in range(particle_count):
            particle_angle = random.uniform(
                0,
                math.tau,
            )
            particle_speed = random.uniform(
                70,
                250,
            )
            self.particles.append(
                {
                    "x": float(x_position),
                    "y": float(y_position),
                    "vx": (
                        math.cos(particle_angle)
                        * particle_speed
                    ),
                    "vy": (
                        math.sin(particle_angle)
                        * particle_speed
                    ),
                    "life": random.uniform(
                        0.35,
                        0.85,
                    ),
                    "maximum_life": 0.85,
                    "radius": random.randint(2, 6),
                    "color": color,
                }
            )

    # Actualizează particulele și le șterge după stingere.
    def _update_particles(self, delta_time):
        for particle in self.particles[:]:
            particle["x"] += (
                particle["vx"] * delta_time
            )
            particle["y"] += (
                particle["vy"] * delta_time
            )
            particle["life"] -= delta_time
            particle["vx"] *= 0.97
            particle["vy"] *= 0.97

            if particle["life"] <= 0:
                self.particles.remove(particle)

    # Desenează nivelul complet în ordinea corectă.
    def draw(self):
        self._draw_background()

        for bullet in self.bullets:
            bullet.draw(self.screen)

        for asteroid in self.asteroids:
            asteroid.draw(self.screen)

        self._draw_ship()
        self._draw_particles()
        self._draw_interface()

        if self.game_over:
            self._draw_game_over()

        self._draw_fade()

    # Deplasează lent fundalul pentru a crea senzația de zbor.
    def _draw_background(self):
        horizontal_offset = int(
            -25
            + math.sin(self.elapsed_time * 0.18)
            * 10
        )
        vertical_offset = int(
            -25
            + math.cos(self.elapsed_time * 0.14)
            * 7
        )
        self.screen.blit(
            self.background,
            (
                horizontal_offset,
                vertical_offset,
            ),
        )

    # Desenează nava; în invincibilitate aceasta clipește.
    def _draw_ship(self):
        if self.game_over:
            return

        if (
            self.invincibility_timer > 0
            and int(
                self.invincibility_timer * 12
            ) % 2 == 0
        ):
            return

        # Imaginea conține deja flăcările motoarelor.
        # Nu adăugăm alte flăcări peste sprite.
        self.screen.blit(
            self.ship_image,
            (
                int(self.ship_x),
                int(self.ship_y),
            ),
        )

    # Desenează particulele cu transparență în funcție de durata rămasă.
    def _draw_particles(self):
        particle_surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )

        for particle in self.particles:
            alpha = int(
                255
                * min(
                    1.0,
                    particle["life"]
                    / particle["maximum_life"],
                )
            )
            pygame.draw.circle(
                particle_surface,
                (
                    *particle["color"],
                    alpha,
                ),
                (
                    int(particle["x"]),
                    int(particle["y"]),
                ),
                particle["radius"],
            )

        self.screen.blit(
            particle_surface,
            (0, 0),
        )

    # Desenează titlul, obiectivul, integritatea, scorul și timpul rămas.
    def _draw_interface(self):
        if self.elapsed_time < 4.5:
            title_surface = self.title_font.render(
                "ASTEROID OCEAN",
                True,
                (230, 244, 255),
            )
            subtitle_surface = self.small_font.render(
                "SURVIVE THE FIELD",
                True,
                (105, 215, 255),
            )
            title_x = (
                self.width // 2
                - title_surface.get_width() // 2
            )
            self.screen.blit(
                title_surface,
                (title_x + 3, 35),
            )
            self.screen.blit(
                subtitle_surface,
                (
                    self.width // 2
                    - subtitle_surface.get_width()
                    // 2,
                    103,
                ),
            )

        panel = pygame.Surface(
            (300, 132),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (4, 10, 27, 185),
            panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel,
            (80, 185, 255, 125),
            panel.get_rect(),
            2,
            border_radius=12,
        )

        remaining_time = max(
            0,
            int(
                math.ceil(
                    SCENE_DURATION
                    - self.elapsed_time
                )
            ),
        )
        hull_text = self.small_font.render(
            f"HULL          {self.hull}/{STARTING_HULL}",
            True,
            (
                (255, 115, 115)
                if self.hull == 1
                else (205, 232, 250)
            ),
        )
        score_text = self.small_font.render(
            f"SCORE         {self.score:05d}",
            True,
            (205, 232, 250),
        )
        time_text = self.small_font.render(
            f"EXIT VECTOR   {remaining_time:02d} S",
            True,
            (100, 220, 255),
        )

        panel.blit(hull_text, (20, 18))
        panel.blit(score_text, (20, 54))
        panel.blit(time_text, (20, 91))
        self.screen.blit(panel, (24, 22))

        instructions = self.small_font.render(
            "WASD / ARROWS - MOVE    SPACE - FIRE",
            True,
            (188, 215, 235),
        )
        self.screen.blit(
            instructions,
            (
                self.width
                - instructions.get_width()
                - 24,
                self.height
                - instructions.get_height()
                - 20,
            ),
        )

        self._draw_progress_bar()

        if self.completed:
            completed_text = self.medium_font.render(
                "SECTOR CLEARED",
                True,
                (125, 245, 255),
            )
            self.screen.blit(
                completed_text,
                (
                    self.width // 2
                    - completed_text.get_width()
                    // 2,
                    self.height // 2 - 25,
                ),
            )

    # Desenează bara care arată cât a mai rămas până la ieșirea din câmp.
    def _draw_progress_bar(self):
        progress = min(
            1.0,
            self.elapsed_time / SCENE_DURATION,
        )
        bar_rect = pygame.Rect(
            self.width // 2 - 210,
            22,
            420,
            9,
        )
        pygame.draw.rect(
            self.screen,
            (17, 27, 48),
            bar_rect,
            border_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            (75, 205, 255),
            (
                bar_rect.x,
                bar_rect.y,
                int(bar_rect.width * progress),
                bar_rect.height,
            ),
            border_radius=5,
        )

    # Desenează mesajul de distrugere și instrucțiunea pentru checkpoint.
    def _draw_game_over(self):
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        overlay.fill((2, 4, 14, 190))
        self.screen.blit(overlay, (0, 0))

        destroyed_text = self.title_font.render(
            "SHIP DESTROYED",
            True,
            (255, 105, 120),
        )
        retry_text = self.medium_font.render(
            "PRESS R - RETRY CHECKPOINT",
            True,
            (220, 235, 250),
        )

        self.screen.blit(
            destroyed_text,
            (
                self.width // 2
                - destroyed_text.get_width() // 2,
                self.height // 2 - 80,
            ),
        )
        self.screen.blit(
            retry_text,
            (
                self.width // 2
                - retry_text.get_width() // 2,
                self.height // 2 + 15,
            ),
        )

    # Creează tranziția neagră de la început și de la final.
    def _draw_fade(self):
        fade_alpha = 0

        if (
            not self.game_over
            and self.elapsed_time < 1.0
        ):
            fade_alpha = int(
                255
                * (1 - self.elapsed_time)
            )
        elif (
            self.completed
            and self.completion_timer > 1.5
        ):
            fade_alpha = int(
                255
                * min(
                    1.0,
                    (
                        self.completion_timer - 1.5
                    )
                    / 0.9,
                )
            )

        if fade_alpha <= 0:
            return

        fade_surface = pygame.Surface(
            (self.width, self.height)
        )
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade_alpha)
        self.screen.blit(fade_surface, (0, 0))
