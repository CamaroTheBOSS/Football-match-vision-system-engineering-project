from enum import Enum

import numpy as np


class Line:
    video_resolution = (0, 0)

    class Orientation(Enum):
        undefined = 0
        horizontal = 1
        vertical = 2

    def __init__(self, p1: tuple, p2: tuple):
        # Segment form
        self.p1 = tuple(map(int, p1))
        self.p2 = tuple(map(int, p2))

        # y = ax + b Analytic form
        self.a = None
        self.b = None

        # Border form (points which are intersections of Analytic form and edges of the video window)
        self.ep1 = None
        self.ep2 = None

        # r, theta form
        self.r = None
        self.theta = None

        self.orientation = self.Orientation.undefined

        self.get_analytic_form()
        self.get_r_theta_form()
        self.get_line_orientation()
        self.get_elongate_form(30)

    def calculate_y(self, x):
        return self.a * x + self.b

    def calculate_x(self, y):
        return (y - self.b) / self.a

    def get_analytic_form(self):
        x1, y1 = self.p1
        x2, y2 = self.p2
        self.a = (y2 - y1) / (x2 - x1) if (x2 != x1) else 10000
        self.b = y1 - self.a * x1
        return self.a, self.b

    def get_elongate_form(self, pixels: int):
        if self.is_horizontal():
            dP = pixels if self.p1[0] < self.p2[0] else -pixels
            x1 = self.p1[0] - dP
            x2 = self.p2[0] + dP
            y1 = self.calculate_y(x1)
            y2 = self.calculate_y(x2)
        else:
            dP = pixels if self.p1[1] < self.p2[1] else -pixels
            y1 = self.p1[1] - dP
            y2 = self.p2[1] + dP
            x1 = self.calculate_x(y1)
            x2 = self.calculate_x(y2)
        self.ep1 = (int(x1), int(y1))
        self.ep2 = (int(x2), int(y2))

        return self.ep1, self.ep2

    def get_r_theta_form(self):
        if self.a == 0:
            self.r = self.b
            self.theta = 0
        else:
            x = self.b / (-1 / self.a - self.a)
            y = self.calculate_y(x)
            self.r = np.sqrt(y ** 2 + x ** 2)  # Maybe its computationally better to use abs(y + x)
            self.theta = np.arctan2(x, y)

    def get_line_orientation(self):
        if abs(self.theta) < 0.2:
            self.orientation = self.Orientation.horizontal
        elif 2.6 > abs(self.theta) > 0.7:
            self.orientation = self.Orientation.vertical
        else:
            self.orientation = self.Orientation.undefined
        return self.orientation

    def is_horizontal(self):
        return self.orientation == self.Orientation.horizontal

    def is_vertical(self):
        return self.orientation == self.Orientation.vertical
