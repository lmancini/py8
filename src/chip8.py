#!/usr/bin/python
# -*- coding: utf-8 -*-

import random

def iterbits(char):
    if not 0 <= char < 256:
        raise RuntimeError
    for dd in range(8):
        yield ((char & (1 << (7 - dd))) >> (7 - dd)) & 0xff

class Chip8(object):
    def __init__(self, original=False):

        # Flag to force behaviours that are closer to original interpreter
        # (e.g. i incremented after FX55/FX65), but that break games (blinky,
        # hidden, etc...)
        self._original = original

        self.pc = 0x200
        self.v = [0] * 16
        self.i = None
        self.stack = []
        self.mem = [0]*4096 # 4096 bytes
        self.delay_timer = 0
        self.sound_timer = 0

        self.keys = [False] * 16

        self.loadChars()

        # Initializing with a fixed seed makes random numbers generation a
        # fixed sequence, like it probably was on actual hardware. This also
        # makes emulation results reproducible and unit testing possible.
        random.seed(self.pc)

    def loadChars(self):
        chars = [
        [0xF0, 0x90, 0x90, 0x90, 0xF0],
        [0x20, 0x60, 0x20, 0x20, 0x70],
        [0xF0, 0x10, 0xF0, 0x80, 0xF0],
        [0xF0, 0x10, 0xF0, 0x10, 0xF0], #3
        [0x90, 0x90, 0xF0, 0x10, 0x10],
        [0xF0, 0x80, 0xF0, 0x10, 0xF0],
        [0xF0, 0x80, 0xF0, 0x90, 0xF0], #6
        [0xF0, 0x10, 0x20, 0x40, 0x40],
        [0xF0, 0x90, 0xF0, 0x90, 0xF0],
        [0xF0, 0x90, 0xF0, 0x10, 0xF0], #9
        [0xF0, 0x90, 0xF0, 0x90, 0x90],
        [0xE0, 0x90, 0xE0, 0x90, 0xE0],
        [0xF0, 0x80, 0x80, 0x80, 0xF0], #C
        [0xE0, 0x90, 0x90, 0x90, 0xE0],
        [0xF0, 0x80, 0xF0, 0x80, 0xF0],
        [0xF0, 0x80, 0xF0, 0x80, 0x80], #F
        ]

        self.chars_lut = {}
        addr = 0
        for i_c, c in enumerate(chars):
            self.chars_lut[i_c] = addr
            for cc in c:
                self.mem[addr] = cc
                addr += 1

    def setPressed(self, key):
        self.keys[key] = True

    def setReleased(self, key):
        self.keys[key] = False

    def setScreen(self, scr):
        self.scr = scr

    def loadRom(self, rom):
        for i_c, c in enumerate(rom):
            self.mem[0x200 + i_c] = ord(c)

    def fetch(self):
        return self.mem[self.pc], self.mem[self.pc+1]

    def opcode(self, b0, b1):

        if __debug__:
            print "%02X%02X" % (b0, b1)

        n0 = (b0 & 0b11110000) >> 4
        n1 = (b0 & 0b00001111)
        n2 = (b1 & 0b11110000) >> 4
        n3 = (b1 & 0b00001111)

        if n0 == 0 and n1 == 0 and n2 == 0xe and n3 == 0:
            # 00E0 Clears the screen.
            self.scr.fill((0, 0, 0, 255))
        elif n0 == 0 and n1 == 0 and n2 == 0xe and n3 == 0xe:
            # 00EE Returns from a subroutine.
            return self.stack.pop()
        elif n0 == 1:
            # 1NNN Jumps to address NNN.
            return (n1 << 8) + b1
        elif n0 == 2:
            # 2NNN Calls subroutine at NNN.
            self.stack.append(self.pc+2)
            return (n1 << 8) + b1
        elif n0 == 3:
            # 3XNN Skips the next instruction if VX equals NN.
            if self.v[n1] == b1:
                self.pc += 2
        elif n0 == 4:
            # 4XNN Skips the next instruction if VX doesn't equal NN.
            if self.v[n1] != b1:
                self.pc += 2
        elif n0 == 5 and n3 == 0:
            # 5XY0 Skips the next instruction if VX equals VY.
            if self.v[n1] == self.v[n2]:
                self.pc += 2
        elif n0 == 6:
            # 6XNN Sets VX to NN.
            self.v[n1] = b1
        elif n0 == 7:
            # 7XNN Adds NN to VX.
            self.v[n1] = (self.v[n1] + b1) % 256
        elif n0 == 8 and n3 == 0:
            # 8XY0 Sets VX to the value of VY.
            self.v[n1] = self.v[n2]
        elif n0 == 8 and n3 == 1:
            # 8XY1 Sets VX to VX or VY.
            self.v[n1] = self.v[n1] | self.v[n2]
        elif n0 == 8 and n3 == 2:
            # 8XY2 Sets VX to VX and VY.
            self.v[n1] = self.v[n1] & self.v[n2]
        elif n0 == 8 and n3 == 3:
            # 8XY3 Sets VX to VX xor VY.
            self.v[n1] = self.v[n1] ^ self.v[n2]
        elif n0 == 8 and n3 == 4:
            # 8XY4 Adds VY to VX. VF is set to 1 when there's a carry, and to
            # 0 when there isn't.
            sum = self.v[n1] + self.v[n2]
            self.v[n1] = sum % 256
            self.v[15] = sum / 256
        elif n0 == 8 and n3 == 5:
            # 8XY5 VY is subtracted from VX. VF is set to 0 when there's a
            # borrow, and 1 when there isn't.
            sub = self.v[n1] - self.v[n2]
            self.v[n1] = sub % 256
            self.v[15] = (sub / 256) + 1
        elif n0 == 8 and n3 == 6:
            # 8XY6 Shifts VX right by one. VF is set to the value of the least
            # significant bit of VX before the shift.
            self.v[15] = (self.v[n1] & 1)
            self.v[n1] >>= 1
        elif n0 == 8 and n3 == 0xe:
            # 8XYE Shifts VX left by one. VF is set to the value of the most
            # significant bit of VX before the shift.
            self.v[15] = (self.v[n1] & 1)
            self.v[n1] <<= 1
        elif n0 == 9 and n3 == 0:
            # 9XY0 Skips the next instruction if VX doesn't equal VY.
            if self.v[n1] != self.v[n2]:
                self.pc += 2
        elif n0 == 0xa:
            # ANNN Sets I to the address NNN.
            self.i = (n1 << 8) + b1
        elif n0 == 0xc:
            # CXNN Sets VX to a random number and NN.
            self.v[n1] = random.randint(0, 255) & b1
        elif n0 == 0xd:
            # DXYN Draws a sprite at coordinate (VX, VY) that has a width of 8
            # pixels and a height of N pixels. As described above, VF is set
            # to 1 if any screen pixels are flipped from set to unset when the
            # sprite is drawn, and to 0 if that doesn't happen.
            vx, vy = n1, n2

            if n3 == 0:
                w = 16
                h = 16
            else:
                w = 8
                h = n3

            x = self.v[vx]
            y = self.v[vy]

            if n3 == 0:
                data = [1]*16*16
            else:
                data = []
                for ii in range(h):
                    data.extend(list(iterbits(self.mem[self.i + ii])))

            self.v[15] = 0
            for yy in range(h):
                sy = (y + yy)

                # Towers drawing code in BLITZ seems to expect this
                if not 0 <= sy < 32:
                    continue

                for xx in range(w):
                    sx = (x + xx) % 64

                    pixel = data[yy*w + xx]

                    if not pixel:
                        continue

                    pcol = self.scr.get_at((sx, sy))

                    if pcol == (0, 0, 0, 255):
                        self.scr.set_at((sx, sy), (255, 255, 255, 255))
                    else:
                        assert pcol == (255, 255, 255, 255), pcol
                        self.v[15] = 1
                        self.scr.set_at((sx, sy), (0, 0, 0, 255))

        elif n0 == 0xe and n2 == 0xa and n3 == 1:
            # EXA1 Skips the next instruction if the key stored in VX isn't
            # pressed.
            if not self.keys[self.v[n1]]:
                self.pc += 2

        elif n0 == 0xe and n2 == 9 and n3 == 0xe:
            # EX9E Skips the next instruction if the key stored in VX is
            # pressed.
            if self.keys[self.v[n1]]:
                self.pc += 2

        elif n0 == 0xf and n2 == 0 and n3 == 7:
            # FX07 Sets VX to the value of the delay timer.
            self.v[n1] = self.delay_timer

        elif n0 == 0xf and n2 == 0 and n3 == 0xa:
            # FX0A A key press is awaited, and then stored in VX.
            if not True in self.keys:
                return self.pc
            self.v[n1] = self.keys.index(True)

        elif n0 == 0xf and n2 == 1 and n3 == 5:
            # FX15 Sets the delay timer to VX.
            self.delay_timer = self.v[n1]

        elif n0 == 0xf and n2 == 1 and n3 == 8:
            # FX18 Sets the sound timer to VX.
            self.sound_timer = self.v[n1]

        elif n0 == 0xf and n2 == 1 and n3 == 0xe:
            # FX1E Adds VX to I.
            self.i += self.v[n1]

        elif n0 == 0xf and n2 == 2 and n3 == 9:
            # FX29 Sets I to the location of the sprite for the character in
            # VX. Characters 0-F (in hexadecimal) are represented by a 4x5
            # font.
            idx = self.v[n1]
            self.i = self.chars_lut[idx]

        elif n0 == 0xf and n2 == 3 and n3 == 3:
            # FX33 Stores the Binary-coded decimal representation of VX at the
            # addresses I, I plus 1, and I plus 2.
            sn = "%03d" % (self.v[n1],)

            self.mem[self.i] = int(sn[0])
            self.mem[self.i + 1] = int(sn[1])
            self.mem[self.i + 2] = int(sn[2])

        elif n0 == 0xf and n2 == 5 and n3 == 5:
            # FX55 Stores V0 to VX in memory starting at address I.
            for vv in range(n1+1):
                self.mem[self.i + vv] = self.v[vv]
            if self._original:
                self.i += (n1+1)

        elif n0 == 0xf and n2 == 6 and n3 == 5:
            # FX65 Fills V0 to VX with values from memory starting at address
            # I.
            for vv in range(n1+1):
                self.v[vv] = self.mem[self.i + vv]
            if self._original:
                self.i += (n1+1)

        else:
            raise RuntimeError, "%02X%02X unimplemented" % (b0, b1)

    def execute(self, num_cycles):
        for _ in xrange(num_cycles):
            b0, b1 = self.fetch()
            newpc = self.opcode(b0, b1)
            if newpc:
                self.pc = newpc
            else:
                self.pc += 2

            self.update_timers()

    def update_timers(self):
        assert not self.delay_timer < 0

        if self.delay_timer > 0:
            self.delay_timer -= 1

        # Emulate me please!
        if self.sound_timer > 0:
            self.sound_timer -= 1
