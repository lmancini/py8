#!/usr/bin/python
# -*- coding: utf-8 -*-

USE_PYPY = 0

if USE_PYPY:
    from rpython.rlib.rarithmetic import intmask
    from rpython.rlib.rrandom import Random

    class rand(object):
        def seed(self, seed):
            self.r = Random(seed)
        def randint(self, a, b):
            r32 = intmask(self.r.genrand32())
            r = a + r32 % (b - a)
            return intmask(r)
    random = rand()
else:
    import random

if USE_PYPY:
    from rpython.rlib.jit import JitDriver
    jitdriver = JitDriver(greens=['pc', 'b0', 'b1'],
                          reds=['v', 'mem', 'self'])

def iterbits(char):
    if not 0 <= char < 256:
        raise RuntimeError
    return [((char >> (7 - dd)) & 0x1) for dd in range(8)]

class Chip8(object):
    def __init__(self, original=False):

        # Flag to force behaviours that are closer to original interpreter
        # (e.g. i incremented after FX55/FX65), but that break games (blinky,
        # hidden, etc...)
        self._original = original

        self.pc = 0x200
        self.v = [0] * 16
        self.i = 0
        self.stack = []
        self.mem = [0] * 4096
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
        self.mem[0x200:0x200 + len(rom)] = [ord(c) for c in rom]

    def update_timers(self):
        assert not self.delay_timer < 0

        if self.delay_timer > 0:
            self.delay_timer -= 1

        # Emulate me please!
        if self.sound_timer > 0:
            self.sound_timer -= 1

    def fetch(self):
        return self.mem[self.pc], self.mem[self.pc+1]

    def execute(self, num_cycles):
        for _ in range(num_cycles):
            b0, b1 = self.fetch()
            newpc = self.opcode(b0, b1)
            if newpc != -1:
                self.pc = newpc
            else:
                self.pc += 2

            self.update_timers()

    def opcode(self, b0, b1):

        if False:
            if USE_PYPY:
                print "%x%x" % (b0, b1)
            else:
                print "%02X%02X" % (b0, b1)

        if USE_PYPY:
            jitdriver.jit_merge_point(pc=self.pc, v=self.v, mem=self.mem,
                                      b0=b0, b1=b1, self=self)

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
        elif n0 == 8 and n3 == 7:
            # 8XY7 Sets VX to VY minus VX. VF is set to 0 when there's a
            # borrow, and 1 when there isn't.
            sub = self.v[n2] - self.v[n1]
            self.v[n1] = sub % 256
            self.v[15] = (sub / 256) + 1
        elif n0 == 8 and n3 == 0xe:
            # 8XYE Shifts VX left by one. VF is set to the value of the most
            # significant bit of VX before the shift.
            self.v[15] = (self.v[n1] & (1 << 7)) >> 7
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
            self.v[n1] = random.randint(0, 256) & b1
        elif n0 == 0xd:
            # Draws a sprite at coordinate (VX, VY) that has a width of 8
            # pixels and a height of N pixels. Each row of 8 pixels is read as
            # bit-coded starting from memory location I; I value doesn't change
            # after the execution of this instruction. As described above, VF
            # is set to 1 if any screen pixels are flipped from set to unset
            # when the sprite is drawn, and to 0 if that doesn't happen.
            vx, vy = self.v[n1], self.v[n2]
            w, h = 8, n3
            self.v[15] = 0

            for row in range(h):
                rb = self.mem[self.i + row]
                sy = vy + row

                # Towers drawing code in BLITZ seems to expect this
                if not 0 <= sy < 32:
                    continue

                for col in range(w):
                    bit = (rb >> (w - 1 - col)) & 0x1

                    if not bit:
                        continue

                    # This is expected behaviour: pixels flip on the other side
                    sx = (vx + col) % 64

                    pixelpos = (sx, sy)

                    pixel = self.scr.get_at(pixelpos)

                    if pixel == (255, 255, 255, 255):
                        self.scr.set_at(pixelpos, (0, 0, 0, 255))
                        self.v[15] = 1
                    else:
                        self.scr.set_at(pixelpos, (255, 255, 255, 255))

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
            if USE_PYPY:
                sn = "%d" % self.v[n1]
                while len(sn) < 3:
                    sn = "0" + sn
            else:
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
            if USE_PYPY:
                msg = "%x%x unimplemented" % (b0, b1)
            else:
                msg = "%02X%02X unimplemented" % (b0, b1)
            print msg
            raise RuntimeError, msg

        return -1
