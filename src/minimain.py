#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import pygame
from minichip8 import Chip8

hz60 = int(1000.0 / 60.0)
hz60_3 = int(1000.0 / 60.0 / 3.0)
screen_size = (1024, 512)

def entry_point(argv):
    c8 = Chip8()
    c8.loadRom(open(argv[1], "rb").read())

    pygame.init()
    pygame.display.set_caption("Py8")

    screen = pygame.display.set_mode(screen_size, pygame.HWSURFACE|pygame.DOUBLEBUF)
    surface = pygame.Surface((64, 32))
    c8.setScreen(surface)

    while True:
        start = pygame.time.get_ticks()

        exit = handle_keypresses(c8)
        if exit:
            break

        c8.execute(1)
        pygame.transform.scale(surface, screen_size, screen)
        pygame.display.flip()

        elapsed = pygame.time.get_ticks() - start
        if elapsed < hz60_3:
            pygame.time.wait(hz60_3 - elapsed)

def handle_keypresses(c8):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
            if event.key == pygame.K_ESCAPE:
                return True
            else:
                try:
                    key = convert_key(event.key)
                except KeyError:
                    pass
                else:
                    if event.type == pygame.KEYDOWN:
                        c8.setPressed(key)
                    elif event.type == pygame.KEYUP:
                        c8.setReleased(key)

def convert_key(key):
    keys = {
        pygame.K_4: 1,
        pygame.K_UP: 2,
        pygame.K_6: 3,
        pygame.K_7: 0xc,
        pygame.K_LEFT: 4,
        pygame.K_SPACE: 5,
        pygame.K_RIGHT: 6,
        pygame.K_u: 0xd,
        pygame.K_f: 7,
        pygame.K_DOWN: 8,
        pygame.K_h: 9,
        pygame.K_j: 0xe,
        pygame.K_v: 0xa,
        pygame.K_b: 0,
        pygame.K_n: 0xb,
        pygame.K_m: 0xf,
    }

    return keys[key]

if __name__ == "__main__":
    entry_point(sys.argv)
