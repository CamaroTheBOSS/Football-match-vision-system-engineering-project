import copy

import cv2
import numpy as np

from Line import Line, LinearFunction


class Camera:
    def __init__(self, coord: tuple[int, int], theta: float, y1: int, y2: int):
        self.coord = coord
        self.theta = theta
        self.y1 = y1
        self.y2 = y2

        self.video_resolution = (0, 0)

        dX = int(y1 * np.tan(theta / 2))
        self.left_down_corner = tuple(map(sum, zip(coord, (-dX, -y1))))
        self.right_down_corner = tuple(map(sum, zip(coord, (dX, -y1))))

        left_tmp_line = Line(coord, self.left_down_corner)
        right_tmp_line = Line(coord, self.right_down_corner)

        self.left_up_corner = (int(left_tmp_line.calculate_x(coord[1] - y2)), coord[1] - y2)
        self.right_up_corner = (int(right_tmp_line.calculate_x(coord[1] - y2)), coord[1] - y2)

        self.bottom = Line(self.left_down_corner, self.right_down_corner)
        self.right = Line(self.right_down_corner, self.right_up_corner)
        self.top = Line(self.left_up_corner, self.right_up_corner)
        self.left = Line(self.left_up_corner, self.left_down_corner)

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
        return projected_coord

    def draw(self, frame: np.ndarray):
        cv2.line(frame, self.left_down_corner, self.right_down_corner, (0, 0, 255), 3)
        cv2.line(frame, self.left_down_corner, self.left_up_corner, (0, 0, 255), 3)
        cv2.line(frame, self.right_down_corner, self.right_up_corner, (0, 0, 255), 3)
        cv2.line(frame, self.left_up_corner, self.right_up_corner, (0, 0, 255), 3)
