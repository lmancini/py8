#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from chip8 import Chip8

class TestChip8(unittest.TestCase):
    def setUp(self):
        self.c8 = Chip8()

    def run_code(self, code):
        self.c8.loadRom(code)
        self.c8.execute(len(code) / 2)

    def test_FX65_increments_i(self):
        # Set i to 0x200, then call ff65
        self.run_code("\xa2\x00\xff\x65")
        self.assertEqual(self.c8.i, 0x210)

    def test_7XNN_wrap_no_carry(self):
        # Set v0 to 0xFF, add 2
        self.run_code("\x60\xff\x70\x02")
        self.assertEqual(self.c8.v[0], 1)
        # Carry untouched
        self.assertEqual(self.c8.v[15], 0)

if __name__ == "__main__":
    unittest.main()
