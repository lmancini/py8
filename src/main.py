#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import pygame
from chip8 import Chip8

hz60 = int(1000.0 / 60.0)
hz60_3 = int(1000.0 / 60.0 / 3.0)

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

    return keys.get(key)

def main(fn):
    c8 = Chip8()
    c8.loadRom(open(fn, "rb").read())

    pygame.init()
    pygame.display.set_caption("Py8")

    screen = pygame.display.set_mode((256, 128), pygame.HWSURFACE|pygame.DOUBLEBUF)

    surface = pygame.Surface((64, 32))
    c8.setScreen(surface)

    while True:
        start = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit(0)
                else:
                    key = convert_key(event.key)
                    if key is not None:
                        c8.setPressed(key)
            elif event.type == pygame.KEYUP:
                key = convert_key(event.key)
                if key is not None:
                    c8.setReleased(key)

        c8.execute(1)
        pygame.transform.scale(surface, (256, 128), screen)
        pygame.display.flip()
        pygame.time.wait(hz60_3 - (pygame.time.get_ticks() - start))

if __name__ == "__main__":
    main(sys.argv[1])
