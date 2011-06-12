#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

USE_PYPY = 0
BENCHMARK = 0

if USE_PYPY:
    import pysdl as pygame
else:
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

    return keys[key]

def read_file(fn):
    if USE_PYPY:
        res = ""
        fp = os.open(fn, os.O_RDONLY, 0777)
        while True:
            read = os.read(fp, 4096)
            if len(read) == 0:
                break
            res += read
        os.close(fp)
        return res
    else:
        return open(fn, "rb").read()

def entry_point(argv):
    c8 = Chip8()
    c8.loadRom(read_file(argv[1]))

    pygame.init()
    pygame.display.set_caption("Py8")

    screen = pygame.display.set_mode((256, 128), pygame.HWSURFACE|pygame.DOUBLEBUF)

    surface = pygame.Surface((64, 32))
    surface.fill((0, 0, 0, 255))
    c8.setScreen(surface)

    # Used for benchmark mode
    start_time = pygame.time.get_ticks()
    opcodes = 0

    running = True
    while running:
        if BENCHMARK == 0:
            start = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    if event.key == pygame.K_ESCAPE:
                        running = False
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

        c8.execute(1)

        pygame.transform.scale(surface, (256, 128), screen)
        pygame.display.flip()

        opcodes += 1

        if opcodes % 10000 == 0:
            secs = float(pygame.time.get_ticks() - start_time) / 1000.0
            print "OPS: %f" % (opcodes / secs)

        if BENCHMARK == 0:
            elapsed = pygame.time.get_ticks() - start
            if elapsed < hz60_3:
                pygame.time.wait(hz60_3 - elapsed)
        else:
            if opcodes == 100000:
                running = False

    return 0

def target(*args):
    return entry_point, None

if __name__ == "__main__":
    #import cProfile
    #cProfile.run("entry_point(sys.argv)", sort=1)
    entry_point(sys.argv)
