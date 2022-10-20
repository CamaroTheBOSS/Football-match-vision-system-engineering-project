import cv2
import numpy as np

from Line import Line


class Camera:
    def __init__(self, coord: tuple):
        self.coord = coord

        self.left_down_corner = tuple(map(sum, zip(coord, (-40, -90))))
        self.right_down_corner = tuple(map(sum, zip(coord, (40, -90))))

        left_tmp_line = Line(coord, self.left_down_corner)
        right_tmp_line = Line(coord, self.right_down_corner)

        self.left_up_corner = (left_tmp_line.calculate_x(coord[1] - 245), coord[1] - 245)
        self.right_up_corner = (right_tmp_line.calculate_x(coord[1] - 245), coord[1] - 245)

        self.bottom = Line(self.left_down_corner, self.right_down_corner)
        self.right = Line(self.right_down_corner, self.right_up_corner)
        self.top = Line(self.left_up_corner, self.right_up_corner)
        self.left = Line(self.left_up_corner, self.left_down_corner)

    def draw(self, frame: np.ndarray):
        cv2.line(frame, self.left_down_corner, self.right_down_corner, (0, 0, 255), 1)
        cv2.line(frame, self.left_down_corner, self.left_up_corner, (0, 0, 255), 1)
        cv2.line(frame, self.right_down_corner, self.right_up_corner, (0, 0, 255), 1)
        cv2.line(frame, self.left_up_corner, self.right_up_corner, (0, 0, 255), 1)
