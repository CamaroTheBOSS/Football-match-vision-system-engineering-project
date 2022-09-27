import cv2
import numpy as np


class Drawer:
    def __init__(self, footballers):
        self.footballers = footballers
        self.frame = None

    def draw_footballers(self, frame: np.ndarray):
        for footballer in self.footballers:
            box = footballer.box
            cv2.rectangle(frame, (box[0], box[1]), (box[0] + box[2], box[1] + box[3]), footballer.color, 3)

    def draw_frame(self, window: str):
        cv2.imshow(window, self.frame)
