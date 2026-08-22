import pygame
import random


class HitEffect:

    def __init__(self, x, y):

        self.particles = []

        for i in range(15):

            self.particles.append({

                "x": x,
                "y": y,

                "dx": random.uniform(-3, 3),
                "dy": random.uniform(-3, 3),

                "size": random.randint(2, 5),

                "life": 20
            })


        self.finished = False


    def update(self):

        for particle in self.particles[:]:

            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]

            particle["life"] -= 1


            if particle["life"] <= 0:

                self.particles.remove(particle)


        if len(self.particles) == 0:

            self.finished = True



    def draw(self, screen):

        for particle in self.particles:

            pygame.draw.circle(

                screen,

                (255, 220, 50),

                (
                    int(particle["x"]),
                    int(particle["y"])
                ),

                particle["size"]

            )