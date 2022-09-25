import cv2
import numpy as np


class Point:
    def __init__(self, coord: tuple):
        self.coord = coord
        self.x = coord[0]
        self.y = coord[1]


class IntersectPoint(Point):
    def __init__(self, coord: tuple):
        super().__init__(coord)
        self.displayed = 0
