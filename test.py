from __future__ import division

from maze2 import Maze
from perlin import Perlin
from PIL import Image
from math import cos, pi, sqrt
# m = Maze(20, 40, 5, 0.6)
# m.p()

size = 128
p = Perlin(6, 0.5)
data = [128 * p.value(6, x, y) + 171 * cos(pi / 118 * sqrt((x - size/2) ** 2 + (y - size/2) ** 2)) for x in range(size) for y in range(size)]
colour = [(0,datum,0) if datum > 128 else (0,0,256-datum) for datum in data]
im = Image.new("RGB", (size,size))
im.putdata(colour)
im.save("test.bmp")
