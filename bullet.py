import pygame


# Proiectilul navei jucătorului.
# Aspectul, viteza și damage-ul depind de nivelul armei care l-a creat.
class Bullet:

    LEVEL_COLORS = {
        1: ((0, 105, 255), (0, 220, 255), (245, 255, 255)),
        2: ((0, 175, 220), (35, 255, 220), (255, 255, 255)),
        3: ((115, 45, 255), (205, 90, 255), (255, 240, 255)),
        4: ((255, 120, 20), (255, 215, 55), (255, 255, 235)),
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
        self.weapon_level = max(
            1,
            min(4, int(weapon_level)),
        )
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
        # Păstrăm atributul vechi pentru compatibilitate cu explicațiile codului.
        self.speed = abs(self.velocity_y)

        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )

    # Deplasează proiectilul drept sau pe diagonală.
    def move(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    # Desenează un laser stratificat cu o culoare diferită pentru fiecare nivel.
    def draw(self, screen):
        glow_color, laser_color, core_color = (
            self.LEVEL_COLORS[self.weapon_level]
        )

        glow_padding = 6 if self.heavy else 4
        pygame.draw.rect(
            screen,
            glow_color,
            (
                int(self.x) - glow_padding,
                int(self.y) - 5,
                self.width + glow_padding * 2,
                self.height + 10,
            ),
            border_radius=5,
        )

        pygame.draw.rect(
            screen,
            laser_color,
            (
                int(self.x),
                int(self.y),
                self.width,
                self.height,
            ),
            border_radius=3,
        )

        core_width = 4 if self.heavy else 2
        pygame.draw.rect(
            screen,
            core_color,
            (
                int(self.x + self.width / 2 - core_width / 2),
                int(self.y),
                core_width,
                self.height,
            ),
            border_radius=2,
        )

        # Nivelul maxim primește un cap energetic ușor de recunoscut.
        if self.heavy:
            pygame.draw.circle(
                screen,
                (255, 250, 185),
                (
                    self.rect.centerx,
                    self.rect.top + 3,
                ),
                5,
            )
