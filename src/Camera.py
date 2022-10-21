import copy

import cv2
import numpy as np

from Line import LinearFunction


class Camera:
    def __init__(self, coord: tuple[int, int], theta: float, y1: int, y2: int):
        self.coord = coord
        self.theta = theta
        self.y1 = y1
        self.y2 = y2

        self.video_resolution = (0, 0)
        self.projection_resolution = (0, 0)
        self.offset = (0, 0)

        dX = int(y1 * np.tan(theta / 2))
        self.left_down_corner = tuple(map(sum, zip(coord, (-dX, -y1))))
        self.right_down_corner = tuple(map(sum, zip(coord, (dX, -y1))))

        self.left = LinearFunction(coord, self.left_down_corner)
        self.right = LinearFunction(coord, self.right_down_corner)

        self.left_up_corner = (int(self.left.calculate_x(coord[1] - y2)), coord[1] - y2)
        self.right_up_corner = (int(self.right.calculate_x(coord[1] - y2)), coord[1] - y2)

        self.projection_matrix = np.zeros((3, 3))

    def set_resolution(self, resolution: tuple[int, int]):
        self.video_resolution = resolution

        x1, y1 = (0, 0)
        x2, y2 = (0, resolution[1])
        x3, y3 = (resolution[0], 0)
        x4, y4 = resolution

        xp1, yp1 = self.left_up_corner
        xp2, yp2 = self.left_down_corner
        xp3, yp3 = self.right_up_corner
        xp4, yp4 = self.right_down_corner

        A = np.array([[x1, y1, 1, 0, 0, 0, -xp1*x1, -xp1*y1],
                      [0, 0, 0, x1, y1, 1, -yp1*x1, -yp1*y1],
                      [x2, y2, 1, 0, 0, 0, -xp2*x2, -xp2*y2],
                      [0, 0, 0, x2, y2, 1, -yp2*x2, -yp2*y2],
                      [x3, y3, 1, 0, 0, 0, -xp3*x3, -xp3*y3],
                      [0, 0, 0, x3, y3, 1, -yp3*x3, -yp3*y3],
                      [x4, y4, 1, 0, 0, 0, -xp4*x4, -xp4*y4],
                      [0, 0, 0, x4, y4, 1, -yp4*x4, -yp4*y4]])

        XP = np.array([xp1, yp1, xp2, yp2, xp3, yp3, xp4, yp4]).T

        H = np.linalg.solve(A, XP)
        H = np.append(H, 1).reshape(3, 3)
        self.projection_matrix = H

    def image_coord_to_projected_coord_conversion(self, coord: tuple[int, int]):
        coordinates = np.array((*coord, 1))
        projected_coord = np.dot(self.projection_matrix, coordinates)
        projected_coord /= projected_coord[2]
        return tuple(map(sum, zip(projected_coord, (*self.offset, 0))))

    def draw(self, frame: np.ndarray):
        ld = tuple(map(sum, zip(self.left_down_corner, (*self.offset, 0))))
        rd = tuple(map(sum, zip(self.right_down_corner, (*self.offset, 0))))
        lt = tuple(map(sum, zip(self.left_up_corner, (*self.offset, 0))))
        rt = tuple(map(sum, zip(self.right_up_corner, (*self.offset, 0))))
        cv2.line(frame, ld, rd, (0, 0, 255), 3)
        cv2.line(frame, ld, lt, (0, 0, 255), 3)
        cv2.line(frame, rd, rt, (0, 0, 255), 3)
        cv2.line(frame, lt, rt, (0, 0, 255), 3)

    def move(self, position):
        x = position[0] * self.projection_resolution[0] / 3000
        y = 100 + position[1] * self.projection_resolution[1] / 2500
        self.offset = (int(x), int(y))

