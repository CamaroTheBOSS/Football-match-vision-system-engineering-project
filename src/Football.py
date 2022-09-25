from operator import sub

import cv2
import numpy as np


class MovingObject:
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        # Unchangeable
        self.id = identifier
        self.color = color

        # Changeable
        self.box = box
        self.center = center
        self.detected = False
        self.velocity = (0, 0)

    def track(self, new_center: tuple, new_box: tuple) -> None:
        self.detected = True
        self.velocity = tuple(map(sub, zip(new_center, self.center)))
        self.center = new_center
        self.box = new_box

    def update(self) -> None:
        if not self.detected:
            self.center = tuple(map(sum, zip(self.center, self.velocity)))
        self.detected = False


class Footballer(MovingObject):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
        self.team = None


class Ball(MovingObject):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)


class FootballManager:
    def __init__(self):
        self.footballers = []
        self.ball = None

    def fit_contours_to_objects(self, frame: np.ndarray, contours: list[np.ndarray]):
        for contour in contours:
            # 1. Finding center of mass and bounding box of the contour
            m = cv2.moments(contour)
            box = cv2.boundingRect(contour)
            x, y, w, h = box[0] + box[2] // 3, box[1] + box[3] // 10, box[2] // 3, 3 * box[3] // 10
            center = (int(m['m10'] / m['m00']), int(m['m01'] / m['m00'])) if m['m00'] != 0.0 else \
                tuple(coord // 2 for coord in box[0:2])

            # 2. Finding average color
            x_vec = np.linspace(x, x + w - 1, 10, dtype=int)
            y_vec = np.linspace(y, y + h - 1, 10, dtype=int)
            colors_list = [frame[y, x] for x in x_vec for y in y_vec]
            average_color = (0, 0, 0)
            divider = 0
            for color in colors_list:
                if not np.logical_and(color[0] > color[1], color[1] > color[2]):
                    average_color = tuple(map(sum, zip(average_color, color)))
                    divider += 1
            if not divider:
                divider = 1
            average_color = tuple(int(color) // divider for color in average_color)
            cv2.rectangle(frame, (box[0], box[1]), (box[0] + box[2], box[1] + box[3]), average_color, 3)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)











