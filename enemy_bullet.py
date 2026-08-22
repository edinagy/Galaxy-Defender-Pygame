import pygame


class EnemyBullet:

    # bullet_type schimba miscarea si aspectul proiectilului.
    # "rapid" apartine scout-ului rosu, "spread" tank-ului verde,
    # iar "aimed" este proiectilul vertical al fighter-ului albastru.
    def __init__(
        self,
        x,
        y,
        speed_x=0,
        speed_y=5,
        bullet_type="standard",
    ):
        self.bullet_type = bullet_type

        if self.bullet_type == "rapid":
            # Proiectilul roșu este suficient de mare pentru fullscreen,
            # fără să transforme rafala scout-ului într-un zid imposibil.
            self.width = 10
            self.height = 24
        elif self.bullet_type == "spread":
            self.width = 12
            self.height = 12
        elif self.bullet_type == "aimed":
            # Diamantul albastru are o siluetă mai lată și mai ușor de citit.
            self.width = 16
            self.height = 24
        elif self.bullet_type == "elite":
            self.width = 14
            self.height = 20
        else:
            self.width = 6
            self.height = 14

        self.x = x
        self.y = y

        self.speed_x = speed_x
        self.speed_y = speed_y
        self.animation_timer = 0

        self.rect = pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )

    # Toate proiectilele isi pastreaza directia initiala.
    # Inamicii obisnuiti trag in jos, astfel incat traiectoriile sa fie clare.
    def move(self, player_rect=None):
        self.animation_timer += 1

        self.x += self.speed_x
        self.y += self.speed_y

        self.rect.topleft = (
            int(self.x),
            int(self.y),
        )

    def draw(self, screen):
        center = self.rect.center

        if self.bullet_type == "rapid":
            # Stratul exterior închis separă proiectilul de fundalul luminos.
            pygame.draw.line(
                screen,
                (95, 5, 30),
                (center[0], self.rect.top - 7),
                (center[0], self.rect.bottom + 5),
                14,
            )
            pygame.draw.line(
                screen,
                (255, 45, 75),
                (center[0], self.rect.top),
                (center[0], self.rect.bottom),
                8,
            )
            pygame.draw.line(
                screen,
                (255, 210, 220),
                (center[0], self.rect.top + 3),
                (center[0], self.rect.bottom - 3),
                3,
            )
            pygame.draw.circle(screen, (255, 245, 245), center, 4)

        elif self.bullet_type == "spread":
            # Tank-ul verde lanseaza globuri de plasma usor de recunoscut.
            pulse = 2 if self.animation_timer % 12 < 6 else 0
            pygame.draw.circle(
                screen,
                (20, 85, 35),
                center,
                10 + pulse,
            )
            pygame.draw.circle(screen, (55, 245, 100), center, 7)
            pygame.draw.circle(screen, (220, 255, 225), center, 3)

        elif self.bullet_type == "aimed":
            # Coada albastră are un contur întunecat și un nucleu cyan intens.
            pygame.draw.line(
                screen,
                (10, 45, 135),
                (center[0], self.rect.top - 12),
                (center[0], self.rect.bottom),
                13,
            )
            pygame.draw.line(
                screen,
                (35, 175, 255),
                (center[0], self.rect.top - 8),
                (center[0], self.rect.bottom - 2),
                7,
            )
            pygame.draw.polygon(
                screen,
                (10, 75, 180),
                [
                    (center[0], self.rect.top - 4),
                    (self.rect.right + 4, center[1]),
                    (center[0], self.rect.bottom + 4),
                    (self.rect.left - 4, center[1]),
                ],
            )
            pygame.draw.polygon(
                screen,
                (50, 195, 255),
                [
                    (center[0], self.rect.top),
                    (self.rect.right, center[1]),
                    (center[0], self.rect.bottom),
                    (self.rect.left, center[1]),
                ],
            )
            pygame.draw.circle(screen, (235, 255, 255), center, 4)

        elif self.bullet_type == "elite":
            # Salva elitei foloseste proiectile violete mai mari si vizibile.
            pygame.draw.circle(screen, (65, 15, 105), center, 12)
            pygame.draw.polygon(
                screen,
                (190, 60, 255),
                [
                    (center[0], self.rect.top - 3),
                    (self.rect.right + 2, center[1]),
                    (center[0], self.rect.bottom + 3),
                    (self.rect.left - 2, center[1]),
                ],
            )
            pygame.draw.circle(screen, (250, 225, 255), center, 4)

        else:
            # Aspectul vechi ramane disponibil pentru drone si alte sisteme.
            pygame.draw.rect(
                screen,
                (255, 70, 70),
                self.rect,
            )
