#!/usr/bin/env python3

import os, sys, math, pygame, pygame.mixer
import collections
import numpy as np
from pygame.locals import *

black = (0,0,0)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
white = (255,255,255)


class Square:
    square_color = blue
    square_size = (10, 10)

    def __init__(self, x,y, color = blue):
        self.square_coord = ((x,y), self.square_size)
        self.square_color = color

    def draw(self,screen):
        pygame.draw.rect(screen, self.square_color, self.square_coord)


class Circle:
    circle_color = red
    circle_size = 10

    def __init__(self, x,y):
        self.circle_coord = (x,y)

    def update(self, x,y):
        _x,_y = self.circle_coord 
        self.circle_coord = (x + _x, y+_y)

    def draw(self,screen):
        pygame.draw.circle(screen, self.circle_color, self.circle_coord, self.circle_size)


class Window:
    fps_limit = 60
    def __init__(self):
        pygame.init()
        display_info = pygame.display.Info()
        self.screen = pygame.display.set_mode((display_info.current_w, display_info.current_h))
        pygame.display.set_caption('c36-Tracker')
        self.clock = pygame.time.Clock()
        self.bg = self._load_bg(display_info)

    def _load_bg(self, display_info):
        bg = pygame.image.load('plan.png')
        bg = pygame.transform.scale(bg, (display_info.current_w,display_info.current_h))
        return bg


    def update(self):
        self.clock.tick(self.fps_limit) 
        self.screen.blit(self.bg, (0,0))

    def close(self):
        pygame.quit()


class WindowManager:
    def __init__(self, window):
        self.window = window
        self.objects = collections.OrderedDict()

    def add_object(self,key, value):
        # value is a pygame object instance
        if not key in self.objects.keys():
            self.objects[key] = value

    def update(self, key, value):
        self.objects[key].update(*value)

    def step(self, moves=None):
        self.window.update()
        if moves is not None:
            for k,v in moves.items():
                try:
                    self.update(k, v)
                except AttributeError:
                    pass
        for k,v in self.objects.items():
            v.draw(self.window.screen)
        pygame.display.flip()

    def close(self):
        self.window.close()



def do_work():
    pos_x =0
    pos_y = 0
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            run_me = False
            raise ValueError()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                pos_x = - 10
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                pos_x = + 10
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                pos_y = + 10
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                pos_y = - 10

    steps = {0:(pos_x, pos_y)}
    return steps

#pos_x =  400
#pos_y = 200
#circle = Circle(pos_x, pos_y)

#window = Window()
#wm = WindowManager(window)
#
#import time
#for i  in range(5):
#    x,y = np.random.randint(100, 200, 2)
#    square = Square(x, y)
#    wm.add_object(i, square)
#    wm.step()
#    time.sleep(5)
#wm.close()

