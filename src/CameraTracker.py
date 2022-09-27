import cv2
import numpy as np

from Config import Config


class CameraTracker:
    def __init__(self):
        self.frame = None
