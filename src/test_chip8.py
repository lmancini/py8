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

if __name__ == "__main__":
    unittest.main()
