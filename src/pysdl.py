#!/usr/bin/python
# -*- coding: utf-8 -*-

# XXX: very loose RSDL wrapper to resemble pygame's API

from pypy.rlib.rsdl import RSDL, RSDL_helper
from pypy.rlib.rarithmetic import r_uint, intmask
from pypy.rpython.lltypesystem import lltype, rffi
from pypy.rlib.jit import dont_look_inside

K_4 = RSDL.K_4
K_UP = RSDL.K_UP
K_6 = RSDL.K_6
K_7 = RSDL.K_7
K_LEFT = RSDL.K_LEFT
K_SPACE = RSDL.K_SPACE
K_RIGHT = RSDL.K_RIGHT
K_u = RSDL.K_u
K_f = RSDL.K_f
K_DOWN = RSDL.K_DOWN
K_h = RSDL.K_h
K_j = RSDL.K_j
K_v = RSDL.K_v
K_b = RSDL.K_b
K_n = RSDL.K_n
K_m = RSDL.K_m

HWSURFACE = 0
DOUBLEBUF = 0

def init():
    RSDL.Init(RSDL.INIT_VIDEO)

class Display(object):
    def set_caption(self, caption):
        RSDL.WM_SetCaption(caption, caption)
    def set_mode(self, size, flags):
        self.screen = RSDL.SetVideoMode(size[0], size[1], 32, 0)
        return self.screen
    def flip(self):
        RSDL.Flip(self.screen)

class Surface(object):
    def __init__(self, size):
        self.surface = RSDL.CreateRGBSurface(0, size[0], size[1], 32,
                                             r_uint(0xFF000000),
                                             r_uint(0x00FF0000),
                                             r_uint(0x0000FF00),
                                             r_uint(0x000000FF))

    # pypy has been unable to jit calls to RSDL_helper get_pixel and
    # set_pixel so far when translating, that's why we prevent the
    # jitter from looking inside this and the next method.
    @dont_look_inside
    def get_at(self, xy):
        x, y = xy
        RSDL.LockSurface(self.surface)
        col = RSDL_helper.get_pixel(self.surface, x, y)
        RSDL.UnlockSurface(self.surface)
        return (intmask((col >> 24) & 0xff),
                intmask((col >> 16) & 0xff),
                intmask((col >> 8) & 0xff),
                intmask(col & 0xff))

    @dont_look_inside
    def set_at(self, xy, col):
        x, y = xy
        c = r_uint((col[0] << 24) + (col[1] << 16) + (col[2] << 8) + col[3])
        RSDL.LockSurface(self.surface)
        RSDL_helper.set_pixel(self.surface, x, y, c)
        RSDL.UnlockSurface(self.surface)
    
    def fill(self, col):
        c = r_uint((col[0] << 24) + (col[1] << 16) + (col[2] << 8) + col[3])
        RSDL.FillRect(self.surface, lltype.nullptr(RSDL.Rect), c)

display = Display()

class Time(object):
    def get_ticks(self):
        return RSDL.GetTicks()
    def wait(self, delay):
        RSDL.Delay(delay)

time = Time()

class Event(object):
    def __init__(self, etype, key):
        self.type = etype
        self.key = key

class EventQueue(object):
    def get(self):
        rv = []
        event = lltype.malloc(RSDL.Event, flavor='raw')
        ok = RSDL.PollEvent(event)
        if ok:
            c_type = rffi.getintfield(event, 'c_type')
            if c_type in (RSDL.KEYDOWN, RSDL.KEYUP):
                p = rffi.cast(RSDL.KeyboardEventPtr, event)
                c_sym = rffi.getintfield(p.c_keysym, 'c_sym')
                pyevent = Event(etype=c_type, key=c_sym)
                rv.append(pyevent)
        lltype.free(event, flavor='raw')
        return rv

event = EventQueue()

QUIT = RSDL.QUIT
KEYDOWN = RSDL.KEYDOWN
K_ESCAPE = RSDL.K_ESCAPE
KEYUP = RSDL.KEYUP

class Transform(object):
    def scale(self, surface, size, screen):
        # XXX: it doesn't scale actually
        RSDL_helper.blit_complete_surface(surface.surface, screen, 0, 0)

transform = Transform()
