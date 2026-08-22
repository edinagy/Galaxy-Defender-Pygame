import pygame
import random


class PowerUp:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 36
        self.height = 36

        self.speed = 3

        # Alege tipul power-up-ului cu rarități diferite.
        # Upgrade-ul de armă este intenționat rar, fiind cel mai puternic.

        roll = random.randint(1, 100)

        if roll <= 3:

            self.powerup_type = "weapon_upgrade"


        elif roll <= 10:

            self.powerup_type = "shield"


        elif roll <= 12:

            self.powerup_type = "life"


        else:

            self.powerup_type = None

        self.rect = pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )


    def move(self):

        self.y += self.speed

        self.rect.topleft = (
            self.x,
            self.y
        )


    def draw(self, screen):

        center_x = int(self.x + self.width // 2)
        center_y = int(self.y + self.height // 2)

        # WEAPON UPGRADE - nucleu energetic cyan-violet.
        if self.powerup_type == "weapon_upgrade":

            pygame.draw.circle(
                screen,
                (120, 45, 235),
                (center_x, center_y),
                18
            )

            pygame.draw.circle(
                screen,
                (65, 225, 255),
                (center_x, center_y),
                18,
                3
            )

            # Trei chevroane indică progresul armei.
            for chevron_y in (-7, 0, 7):
                pygame.draw.lines(
                    screen,
                    (255, 255, 255),
                    False,
                    (
                        (center_x - 7, center_y + chevron_y + 3),
                        (center_x, center_y + chevron_y - 3),
                        (center_x + 7, center_y + chevron_y + 3),
                    ),
                    2,
                )

        # SHIELD - verde-turcoaz
        elif self.powerup_type == "shield":


            pygame.draw.circle(
                screen,
                (0, 220, 180),
                (center_x, center_y),
                18
            )

            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (center_x, center_y),
                18,
                3
            )

            # Simbol de scut
            shield_points = [
                (center_x, center_y - 10),
                (center_x + 9, center_y - 5),
                (center_x + 7, center_y + 6),
                (center_x, center_y + 12),
                (center_x - 7, center_y + 6),
                (center_x - 9, center_y - 5)
            ]

            pygame.draw.polygon(
                screen,
                (255, 255, 255),
                shield_points,
                3
            )
        elif self.powerup_type == "life":

            pygame.draw.circle(
                screen,
                (255, 50, 50),
                (center_x, center_y),
                18
            )

            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (center_x, center_y),
                18,
                3
            )

            pygame.draw.line(
                screen,
                (255, 255, 255),
                (center_x - 8, center_y),
                (center_x + 8, center_y),
                4
            )

            pygame.draw.line(
                screen,
                (255, 255, 255),
                (center_x, center_y - 8),
                (center_x, center_y + 8),
                4
            )
