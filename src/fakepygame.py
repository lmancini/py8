#!/usr/bin/python
# -*- coding: utf-8 -*-

K_4 = 1
K_UP = 2
K_6 = 3
K_7 = 0xc
K_LEFT = 4
K_SPACE = 5
K_RIGHT = 6
K_u = 0xd
K_f = 7
K_DOWN = 8
K_h = 9
K_j = 0xe
K_v = 0xa
K_b = 0
K_n = 0xb
K_m = 0xf

HWSURFACE = 0
DOUBLEBUF = 0

def init():
    pass

class Display(object):
    def set_caption(self, caption):
        pass
    def set_mode(self, size, flags):
        pass
    def flip(self):
        pass

class Surface(object):
    def __init__(self, size):
        w, h = size
        self.w = w
        self.h = h
        self.surf = [(0, 0, 0, 255)]*(w*h)
    def get_at(self, xy):
        x, y = xy
        return self.surf[self.w * y + x]
    def set_at(self, xy, col):
        x, y = xy
        self.surf[self.w * y + x] = col

display = Display()

class Time(object):
    def get_ticks(self):
        return 0
    def wait(self, delay):
        pass

time = Time()

class Event(object):
    type = 100
class EventQueue(object):
    def get(self):
        return [Event()]

event = EventQueue()

QUIT = 1
KEYDOWN = 2
K_ESCAPE = 3
KEYUP = 4

class Transform(object):
    def scale(self, surface, size, screen):
        pass

transform = Transform()

if __name__ == "__main__":
    main(sys.argv[1])
