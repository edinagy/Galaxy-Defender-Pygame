import pygame
import random


class Explosion:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.particles = []

        self.flash = 8

        self.finished = False


        colors = [
            (255, 255, 255),
            (255, 220, 50),
            (255, 120, 20),
            (255, 50, 0)
        ]


        for i in range(35):

            self.particles.append({

                "x": self.x,
                "y": self.y,

                "dx": random.uniform(-5, 5),
                "dy": random.uniform(-5, 5),

                "size": random.randint(3, 8),

                "life": random.randint(20, 40),

                "color": random.choice(colors)

            })


    def update(self):

        if self.flash > 0:
            self.flash -= 1


        for particle in self.particles[:]:

            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]

            particle["life"] -= 1

            particle["size"] *= 0.94


            if particle["life"] <= 0:
                self.particles.remove(particle)


        if len(self.particles) == 0:

            self.finished = True



    def draw(self, screen):

        # Flash alb la impact

        if self.flash > 0:

            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (
                    int(self.x),
                    int(self.y)
                ),
                25
            )


        # Particule

        for particle in self.particles:

            pygame.draw.circle(

                screen,

                particle["color"],

                (
                    int(particle["x"]),
                    int(particle["y"])
                ),

                max(1, int(particle["size"]))

            )