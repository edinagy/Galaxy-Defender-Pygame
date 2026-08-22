import pygame
import random


class Star:

    def __init__(self, width, height):

        self.width = width
        self.height = height

        self.reset()

    def reset(self):

        self.x = random.randint(0, self.width)
        self.y = random.randint(0, self.height)

        self.speed = random.randint(1, 8)

        self.size = random.randint(1, 4)

    def update(self):

        self.y += self.speed

        if self.y > self.height:

            self.y = 0
            self.x = random.randint(0, self.width)

    def draw(self, screen):

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (self.x, self.y),
            self.size
        )