# -*- coding: utf-8 -*-
from __future__ import division

import random, numpy, math
from collections import deque

from perlin import Perlin
from geom3 import *

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

def cross(a, b):
  return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def normal(center_point, clockwise, widdershins):
  n = numpy.zeros((len(center_point),len(center_point[0]),3))
  for i in range(len(center_point)):
    for j in range(len(center_point[0])):
      n[i,j] = cross((widdershins - center_point)[i,j], (clockwise - center_point)[i,j])
  return n

def smoothed_normals(a, direction):
  # print y
  if direction == 'forward':
    n = (normal(a[1:-2, 1:-2], a[ :-3,1:-2], a[1:-2, :-3]) +
         normal(a[1:-2, 1:-2], a[1:-2, :-3], a[2:-1,1:-2]) +
         normal(a[1:-2, 1:-2], a[2:-1,1:-2], a[1:-2,2:-1]) +
         normal(a[1:-2, 1:-2], a[1:-2,2:-1], a[ :-3,1:-2])) / 4
  elif direction == 'backward':
    n = (normal(a[1:-2, 1:-2], a[1:-2, :-3], a[ :-3,1:-2]) +
         normal(a[1:-2, 1:-2], a[2:-1,1:-2], a[1:-2, :-3]) +
         normal(a[1:-2, 1:-2], a[1:-2,2:-1], a[2:-1,1:-2]) +
         normal(a[1:-2, 1:-2], a[ :-3,1:-2], a[1:-2,2:-1])) / 4
  return n


class Point(object):
  def __init__(self, x, z):
    self.x = x
    self.z = z

  def __mul__(self, other):
    return Point(self.x * other, self.z * other)

  def __add__(self, other):
    return Point(self.x + other.x, self.z + other.z)

  def t(self):
    return (self.x, self.z)

  def __repr__(self):
    return "Point: (%d, %d)" % (self.x, self.z)


# 0 - Undefined square
# 1 - Wall
# 2 - Floor
class Maze(object):
  def __init__(self, config):
    self.size = config['size']
    self.scale = config['scale']
    self.y_scale = config['y_scale']
    num_runners = config['num_runners']
    dead_end_chance = config['dead_end_chance']
    self.startPoint = Point(random.randint(0, self.size - 1), random.randint(0, self.size - 1))
    self.generate_maze(num_runners, dead_end_chance)
    self.disp_map = Perlin(config['disp_map']['octaves'], config['disp_map']['persistence'])
    self.disp_map_res = config['disp_map']['res']
    self.disp_map_dist = config['disp_map']['dist']

  def generate_maze(self, num_runners, dead_end_chance):
    self.map = numpy.zeros((self.size,self.size),numpy.int8)
    self.map[self.startPoint.t()] = 2
    runners = deque([self.startPoint])
    while (len(runners) > 0):
      current = runners.popleft()
      next = self.choose_direction(current)
      while len(runners) < num_runners and next is not None:
        if random.random() < dead_end_chance:
          self.map[next.t()] = 1
        else:
          self.map[next.t()] = 2
          runners.append(next)
        next = self.choose_direction(current)
      for point in self.neighbours(current):
        self.map[point.t()] = 1
    self.draw()
    
    
  def choose_direction(self, point):
    # Generate all neighbouring points
    n = self.neighbours(point)
    # Return None if no possible neighbour
    if len(n) == 0:
      return None
    else:
      return random.choice(list(n))

  
  def neighbours(self, point):
    n = set((Point(point.x - 1, point.z),
             Point(point.x + 1, point.z),
             Point(point.x, point.z - 1),
             Point(point.x, point.z + 1)))
    # Remove neighbours outside map
    outsiders = set(filter(lambda p: p.x not in range(self.size) or p.z not in range(self.size), n))
    n -= outsiders
    po = random.choice(list(n))
    # Remove neighbours that have been specified
    specs = set(filter(lambda p: self.map[p.t()] == 1 or self.map[p.t()] == 2, n))
    n -= specs
    return n


  def draw(self):
    for j in range(self.size+1):
      print '#',
    print '#'
    for z in range(self.size):
      print '#',
      for x in range(self.size):
        if x == self.startPoint.x and z == self.startPoint.z:
          print 'x'
        else:
          print ['?','#',' '][self.map[x,z]],
      print '#'
    for j in range(self.size+1):
      print '#',
    print '#'
  
  def gl_init(self):
    self.listID = glGenLists(1)
    self.generate_list()
  
  def generate_list(self):
    glNewList(self.listID, GL_COMPILE_AND_EXECUTE)
    glBegin(GL_TRIANGLES)
    # glMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE, (0.6,0.3,0))
    glColor(0.6,0.3,0)
    y1 =  self.y_scale * self.scale / 2
    y2 = -self.y_scale * self.scale / 2
    for x in range(self.size):
      for z in range(self.size):
        x1 = (x + 0.5 - self.size / 2) * self.scale + self.scale / 2
        x2 = (x + 0.5 - self.size / 2) * self.scale - self.scale / 2
        z1 = (z + 0.5 - self.size / 2) * self.scale + self.scale / 2
        z2 = (z + 0.5 - self.size / 2) * self.scale - self.scale / 2
        if self.map[x,z] == 2:
          self.generate_roof(x1, x2, y1, y2, z1, z2)
          self.generate_floor(x1, x2, y1, y2, z1, z2)
        else:
          if x != self.size - 1 and self.map[x+1,z] == 2:
            None
            #self.generate_right(x1, x2, y1, y2, z1, z2)
          if x != 0 and self.map[x-1,z] == 2:
            None
            self.generate_left(x1, x2, y1, y2, z1, z2)
          if z != self.size - 1 and self.map[x,z+1] == 2:
            None
            #self.generate_forward(x1, x2, y1, y2, z1, z2)
          if z != 0 and self.map[x,z-1] == 2:
            None
            #self.generate_back(x1, x2, y1, y2, z1, z2)
    x1 = z1 =  self.size / 2 * self.scale
    x2 = z2 = -self.size / 2 * self.scale
    #self.generate_outer_walls(x1, x2, y1, y2, z1, z2)
    glEnd()
    glEndList()
  
  def generate_floor(self, x1, x2, y1, y2, z1, z2):
    res = self.disp_map_res
    size = self.disp_map_res + 4
    y_scale = self.disp_map_dist
    x_scale = (x1 - x2) / res
    z_scale = (z1 - z2) / res
    
    y = numpy.zeros((size, size))
    for i in range(size):
      x = x1 + (i - 1) * x_scale
      for j in range(size):
        z = z1 + (j - 1) * z_scale
        y[i, j] = self.disp_map[x, y2, z] * y_scale
    
    a = numpy.asarray([[(x * x_scale, y[x,z], z * z_scale) for z in range(size)] for x in range(size)])
    n = smoothed_normals(a, 'forward')
    
    for i in range(1, size - 3):
      x3 = x1 + (i-1) * x_scale
      x4 = x3 + x_scale
      for j in range(1, size - 3):
        z3 = z1 + (j-1) * z_scale
        z4 = z3 + z_scale
        glNormal(*n[i-1][j-1]); glVertex(x3, y2 + y[i  ,j  ], z3)
        glNormal(*n[i  ][j  ]); glVertex(x4, y2 + y[i+1,j+1], z4)
        glNormal(*n[i  ][j-1]); glVertex(x4, y2 + y[i+1,j  ], z3)
        
        glNormal(*n[i-1][j-1]); glVertex(x3, y2 + y[i  ,j  ], z3)
        glNormal(*n[i-1][j  ]); glVertex(x3, y2 + y[i  ,j+1], z4)
        glNormal(*n[i  ][j  ]); glVertex(x4, y2 + y[i+1,j+1], z4)
  
  
  def generate_roof(self, x1, x2, y1, y2, z1, z2):
    res = self.disp_map_res
    size = self.disp_map_res + 4
    y_scale = self.disp_map_dist
    x_scale = (x1 - x2) / res
    z_scale = (z1 - z2) / res
    
    y = numpy.zeros((size, size))
    for i in range(size):
      x = x1 + (i - 1) * x_scale
      for j in range(size):
        z = z1 + (j - 1) * z_scale
        y[i, j] = self.disp_map[x, y1, z] * y_scale
    
    a = numpy.asarray([[(x * x_scale, y[x,z], z * z_scale) for z in range(size)] for x in range(size)])
    n = smoothed_normals(a, 'backward')
    
    for i in range(1, size - 3):
      x3 = x1 + (i-1) * x_scale
      x4 = x3 + x_scale
      for j in range(1, size - 3):
        z3 = z1 + (j-1) * z_scale
        z4 = z3 + z_scale
        glNormal(*n[i-1][j-1]); glVertex(x3, y1 + y[i  ,j  ], z3)
        glNormal(*n[i  ][j-1]); glVertex(x4, y1 + y[i+1,j  ], z3)
        glNormal(*n[i  ][j  ]); glVertex(x4, y1 + y[i+1,j+1], z4)
        
        glNormal(*n[i-1][j-1]); glVertex(x3, y1 + y[i  ,j  ], z3)
        glNormal(*n[i  ][j  ]); glVertex(x4, y1 + y[i+1,j+1], z4)
        glNormal(*n[i-1][j  ]); glVertex(x3, y1 + y[i  ,j+1], z4)
  
  def generate_left(self, x1, x2, y1, y2, z1, z2):
    res = self.disp_map_res
    size = self.disp_map_res + 6
    y_scale = (y1 - y2) / res
    x_scale = self.disp_map_dist
    z_scale = (z1 - z2) / res
    
    x = numpy.zeros((size, size))
    for i in range(size):
      y = y2 + (i - 1) * y_scale
      for j in range(size):
        z = z1 + (j - 1) * z_scale
        x[i, j] = self.disp_map[x1, y, z] * x_scale
    
    a = numpy.asarray([[(x[y,z], y * y_scale, z * z_scale) for z in range(size)] for y in range(size)])
    n = smoothed_normals(a, 'forward')
    
    for i in range(1, size - 3):
      y3 = y2 + (i - 2) * y_scale
      y4 = y3 + y_scale
      for j in range(1, size - 3):
        z3 = z1 + (j - 2) * z_scale
        z4 = z3 + z_scale
        glNormal(*n[i-1][j-1]); glVertex(x1 + x[i  ,j  ], y3, z3)
        glNormal(*n[i  ][j  ]); glVertex(x1 + x[i+1,j+1], y4, z4)
        glNormal(*n[i  ][j-1]); glVertex(x1 + x[i+1,j  ], y4, z3)
        
        glNormal(*n[i-1][j-1]); glVertex(x1 + x[i  ,j  ], y3, z3)
        glNormal(*n[i-1][j  ]); glVertex(x1 + x[i  ,j+1], y3, z4)
        glNormal(*n[i  ][j  ]); glVertex(x1 + x[i+1,j+1], y4, z4)
  
  def generate_right(self, x1, x2, y1, y2, z1, z2):
    glNormal( 1,  0,  0)
    glVertex(x1, y2, z1)
    glVertex(x1, y2, z2)
    glVertex(x1, y1, z2)
    glVertex(x1, y1, z1)
  
  def generate_forward(self, x1, x2, y1, y2, z1, z2):
     glNormal( 0,  0,  1)
     glVertex(x2, y2, z1)
     glVertex(x1, y2, z1)
     glVertex(x1, y1, z1)
     glVertex(x2, y1, z1)
  
  def generate_back(self, x1, x2, y1, y2, z1, z2):
    glNormal( 0,  0, -1)
    glVertex(x1, y2, z2)
    glVertex(x2, y2, z2)
    glVertex(x2, y1, z2)
    glVertex(x1, y1, z2)
  
  def generate_outer_walls(self, x1, x2, y1, y2, z1, z2):
    glNormal( 1,  0,  0)
    glVertex(x2, y2, z1)
    glVertex(x2, y2, z2)
    glVertex(x2, y1, z2)
    glVertex(x2, y1, z1)
    glNormal(-1,  0,  0)
    glVertex(x1, y2, z2)
    glVertex(x1, y2, z1)
    glVertex(x1, y1, z1)
    glVertex(x1, y1, z2)
    glNormal( 0,  0,  1)
    glVertex(x2, y2, z2)
    glVertex(x1, y2, z2)
    glVertex(x1, y1, z2)
    glVertex(x2, y1, z2)
    glNormal( 0,  0, -1)
    glVertex(x1, y2, z1)
    glVertex(x2, y2, z1)
    glVertex(x2, y1, z1)
    glVertex(x1, y1, z1)
    
  def display(self):
    glCallList(self.listID)
    # None
