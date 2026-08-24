import math

import pygame


class EnemyBullet:
    """Proiectil inamic cu siluetă diferită pentru fiecare clasă de navă."""

    # bullet_type schimbă numai aspectul proiectilului.
    # Viteza, direcția, hitbox-ul și damage-ul gameplay-ului rămân identice.
    def __init__(
        self,
        x,
        y,
        speed_x=0,
        speed_y=5,
        bullet_type="standard",
    ):
        self.bullet_type = bullet_type

        if bullet_type == "rapid":
            self.width = 10
            self.height = 24
            self.maximum_trail_points = 8
        elif bullet_type == "spread":
            self.width = 12
            self.height = 12
            self.maximum_trail_points = 9
        elif bullet_type == "aimed":
            self.width = 16
            self.height = 24
            self.maximum_trail_points = 10
        elif bullet_type == "elite":
            self.width = 14
            self.height = 20
            self.maximum_trail_points = 11
        elif bullet_type == "shield":
            self.width = 14
            self.height = 18
            self.maximum_trail_points = 12
        elif bullet_type == "phase":
            self.width = 16
            self.height = 24
            self.maximum_trail_points = 14
        else:
            self.width = 6
            self.height = 14
            self.maximum_trail_points = 7

        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.animation_timer = 0
        self.trail_points = []

        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )

    # Toate proiectilele își păstrează traiectoria stabilită la lansare.
    def move(self, player_rect=None):
        self.animation_timer += 1
        self.trail_points.append(self.rect.center)
        if len(self.trail_points) > self.maximum_trail_points:
            self.trail_points.pop(0)

        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.topleft = (int(self.x), int(self.y))

    # Returnează axele proiectilului, astfel încât desenul urmărește direcția.
    def _direction_axes(self):
        length = max(0.001, math.hypot(self.speed_x, self.speed_y))
        direction = (
            self.speed_x / length,
            self.speed_y / length,
        )
        perpendicular = (-direction[1], direction[0])
        return direction, perpendicular

    # Creează un punct aflat în fața/spatele și lateralul centrului.
    @staticmethod
    def _oriented_point(center, direction, perpendicular, forward, side=0):
        return (
            int(center[0] + direction[0] * forward + perpendicular[0] * side),
            int(center[1] + direction[1] * forward + perpendicular[1] * side),
        )

    # Coada graduală indică direcția și păstrează proiectilele vizibile.
    def _draw_trail(self, screen, color, maximum_width):
        if len(self.trail_points) < 2:
            return

        point_count = len(self.trail_points)
        for index in range(1, point_count):
            progress = index / point_count
            trail_color = tuple(
                max(3, int(channel * progress * 0.48))
                for channel in color
            )
            pygame.draw.line(
                screen,
                trail_color,
                self.trail_points[index - 1],
                self.trail_points[index],
                max(1, int(maximum_width * progress)),
            )

    def draw(self, screen):
        center = self.rect.center
        direction, perpendicular = self._direction_axes()

        if self.bullet_type == "rapid":
            self._draw_rapid(screen, center, direction, perpendicular)
        elif self.bullet_type == "spread":
            self._draw_spread(screen, center, direction, perpendicular)
        elif self.bullet_type == "aimed":
            self._draw_aimed(screen, center, direction, perpendicular)
        elif self.bullet_type == "elite":
            self._draw_elite(screen, center, direction, perpendicular)
        elif self.bullet_type == "shield":
            self._draw_shield(screen, center, direction, perpendicular)
        elif self.bullet_type == "phase":
            self._draw_phase(screen, center, direction, perpendicular)
        else:
            self._draw_standard(screen, center, direction, perpendicular)

    # Scout roșu: ac energetic foarte rapid, cu aripioare de stabilizare.
    def _draw_rapid(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (255, 30, 65), 5)
        tip = self._oriented_point(center, direction, perpendicular, 16)
        tail = self._oriented_point(center, direction, perpendicular, -12)

        pygame.draw.line(screen, (70, 4, 22), tail, tip, 13)
        pygame.draw.line(screen, (255, 25, 65), tail, tip, 7)
        pygame.draw.line(screen, (255, 225, 235), tail, tip, 2)

        fin_center = self._oriented_point(center, direction, perpendicular, -3)
        fins = [
            self._oriented_point(fin_center, direction, perpendicular, -6, 8),
            self._oriented_point(fin_center, direction, perpendicular, 4, 3),
            self._oriented_point(fin_center, direction, perpendicular, -6, -8),
        ]
        pygame.draw.polygon(screen, (145, 10, 45), fins)
        pygame.draw.circle(screen, (255, 250, 250), tip, 3)

    # Tank verde: sferă grea de plasmă, cu nucleu și sateliți rotativi.
    def _draw_spread(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (55, 245, 105), 7)
        pulse = 1 + int((math.sin(self.animation_timer * 0.35) + 1) * 1.5)

        # Coada de plasmă se aliniază și pentru proiectilele laterale.
        tail = self._oriented_point(center, direction, perpendicular, -14)
        pygame.draw.line(screen, (7, 55, 25), tail, center, 11)
        pygame.draw.line(screen, (30, 180, 65), tail, center, 6)

        pygame.draw.circle(screen, (5, 55, 25), center, 12 + pulse)
        pygame.draw.circle(screen, (25, 175, 65), center, 9 + pulse)
        pygame.draw.circle(screen, (85, 255, 125), center, 6)
        pygame.draw.circle(screen, (235, 255, 235), center, 3)

        orbit_angle = self.animation_timer * 0.22
        for orbit_offset in (0, math.pi):
            angle = orbit_angle + orbit_offset
            satellite = (
                int(center[0] + math.cos(angle) * (11 + pulse)),
                int(center[1] + math.sin(angle) * (11 + pulse)),
            )
            pygame.draw.circle(screen, (165, 255, 180), satellite, 2)

    # Fighter albastru: lance ionică în formă de diamant dublu.
    def _draw_aimed(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (35, 175, 255), 7)
        tip = self._oriented_point(center, direction, perpendicular, 17)
        tail = self._oriented_point(center, direction, perpendicular, -15)
        left = self._oriented_point(center, direction, perpendicular, 0, 10)
        right = self._oriented_point(center, direction, perpendicular, 0, -10)

        pygame.draw.line(screen, (3, 25, 85), tail, tip, 15)
        pygame.draw.polygon(screen, (15, 80, 205), [tip, left, tail, right])
        inner_left = self._oriented_point(center, direction, perpendicular, 0, 5)
        inner_right = self._oriented_point(center, direction, perpendicular, 0, -5)
        inner_tail = self._oriented_point(center, direction, perpendicular, -10)
        pygame.draw.polygon(
            screen,
            (55, 205, 255),
            [tip, inner_left, inner_tail, inner_right],
        )
        pygame.draw.line(screen, (235, 255, 255), center, tip, 3)
        pygame.draw.circle(screen, (245, 255, 255), center, 3)

    # Elită: cristal instabil violet, înconjurat de un inel orbital.
    def _draw_elite(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (195, 65, 255), 8)
        pulse = math.sin(self.animation_timer * 0.28)
        tip = self._oriented_point(center, direction, perpendicular, 15)
        tail = self._oriented_point(center, direction, perpendicular, -13)
        left = self._oriented_point(center, direction, perpendicular, -1, 9)
        right = self._oriented_point(center, direction, perpendicular, -1, -9)

        pygame.draw.circle(
            screen,
            (35, 5, 65),
            center,
            13 + int((pulse + 1) * 1.5),
        )
        pygame.draw.polygon(screen, (105, 20, 165), [tip, left, tail, right])
        pygame.draw.polygon(
            screen,
            (220, 75, 255),
            [
                tip,
                self._oriented_point(center, direction, perpendicular, 0, 4),
                tail,
                self._oriented_point(center, direction, perpendicular, 0, -4),
            ],
        )
        pygame.draw.line(screen, (255, 225, 255), center, tip, 3)

        orbit_radius = 15 + int(pulse * 2)
        orbit_rect = pygame.Rect(0, 0, orbit_radius * 2, orbit_radius * 2)
        orbit_rect.center = center
        rotation = self.animation_timer * 0.18
        pygame.draw.arc(
            screen,
            (195, 85, 255),
            orbit_rect,
            rotation,
            rotation + 2.0,
            2,
        )
        pygame.draw.arc(
            screen,
            (90, 35, 185),
            orbit_rect,
            rotation + math.pi,
            rotation + math.pi + 2.0,
            2,
        )
        pygame.draw.circle(screen, (255, 250, 255), center, 3)

    # Shield Carrier: nucleu cyan înconjurat de două inele defensive.
    def _draw_shield(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (45, 225, 255), 7)
        pulse = (
            math.sin(self.animation_timer * 0.32) + 1.0
        ) / 2.0
        tail = self._oriented_point(
            center,
            direction,
            perpendicular,
            -14,
        )
        pygame.draw.line(
            screen,
            (5, 55, 90),
            tail,
            center,
            10,
        )
        pygame.draw.circle(
            screen,
            (5, 45, 85),
            center,
            11 + int(pulse * 2),
        )
        pygame.draw.circle(
            screen,
            (30, 190, 235),
            center,
            8,
        )
        pygame.draw.circle(
            screen,
            (220, 255, 255),
            center,
            3,
        )
        ring_radius = 13 + int(pulse * 2)
        pygame.draw.circle(
            screen,
            (105, 235, 255),
            center,
            ring_radius,
            2,
        )
        pygame.draw.arc(
            screen,
            (205, 105, 255),
            (
                center[0] - ring_radius - 3,
                center[1] - ring_radius - 3,
                (ring_radius + 3) * 2,
                (ring_radius + 3) * 2,
            ),
            self.animation_timer * 0.16,
            self.animation_timer * 0.16 + 2.4,
            2,
        )

    # Phase Hunter: lance magenta cu miez cyan și ecou spectral dublu.
    def _draw_phase(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (255, 35, 205), 8)
        tip = self._oriented_point(center, direction, perpendicular, 18)
        tail = self._oriented_point(center, direction, perpendicular, -16)
        left = self._oriented_point(center, direction, perpendicular, -2, 9)
        right = self._oriented_point(center, direction, perpendicular, -2, -9)

        for side_offset in (-8, 8):
            echo_start = self._oriented_point(
                center,
                direction,
                perpendicular,
                -15,
                side_offset,
            )
            echo_end = self._oriented_point(
                center,
                direction,
                perpendicular,
                7,
                side_offset * 0.35,
            )
            pygame.draw.line(
                screen,
                (25, 110, 125),
                echo_start,
                echo_end,
                3,
            )

        pygame.draw.line(screen, (55, 4, 65), tail, tip, 17)
        pygame.draw.polygon(
            screen,
            (205, 25, 170),
            [tip, left, tail, right],
        )
        inner_left = self._oriented_point(
            center, direction, perpendicular, 0, 4
        )
        inner_right = self._oriented_point(
            center, direction, perpendicular, 0, -4
        )
        inner_tail = self._oriented_point(
            center, direction, perpendicular, -10
        )
        pygame.draw.polygon(
            screen,
            (55, 235, 225),
            [tip, inner_left, inner_tail, inner_right],
        )
        pygame.draw.line(screen, (245, 255, 255), center, tip, 2)
        pygame.draw.circle(screen, (255, 235, 255), center, 3)

    # Dronă: bolt chihlimbariu compact, orientat spre jucător la lansare.
    def _draw_standard(self, screen, center, direction, perpendicular):
        self._draw_trail(screen, (255, 105, 25), 5)
        tip = self._oriented_point(center, direction, perpendicular, 12)
        tail = self._oriented_point(center, direction, perpendicular, -9)

        pygame.draw.line(screen, (75, 16, 3), tail, tip, 11)
        pygame.draw.line(screen, (255, 95, 20), tail, tip, 6)
        pygame.draw.line(screen, (255, 235, 175), tail, tip, 2)

        fin_center = self._oriented_point(center, direction, perpendicular, -2)
        pygame.draw.polygon(
            screen,
            (255, 165, 45),
            [
                tip,
                self._oriented_point(fin_center, direction, perpendicular, 0, 5),
                self._oriented_point(fin_center, direction, perpendicular, 0, -5),
            ],
        )
        pygame.draw.circle(screen, (255, 250, 220), tip, 2)
