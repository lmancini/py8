#!/usr/bin/python
# -*- coding: utf-8 -*-

class Chip8(object):

    def loadRom(self, rom):
        raise NotImplementedError
    
    def setScreen(self, scr):
        raise NotImplementedError
    
    def execute(self, num_cycles):
        raise NotImplementedError
    
    def setPressed(self, key):
        raise NotImplementedError
    
    def setReleased(self, key):
        raise NotImplementedError
