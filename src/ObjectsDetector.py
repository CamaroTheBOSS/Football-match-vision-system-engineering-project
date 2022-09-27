import cv2
import numpy as np


class ObjectsDetector:
    def __init__(self):
        self.frame = None

    def cut_footballers_silhouette(self, mask):
        # 1. Cutting silhouettes
        mask[np.logical_and(self.frame[:, :, 1] > self.frame[:, :, 2], self.frame[:, :, 2] > self.frame[:, :, 0])] = 255
        mask = cv2.erode(mask, (3, 3), iterations=5)

        # 2. Finding contours of silhouettes
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        # 3. Artifacts cleaning (area criterion)
        silhouettes = []
        for contour in contours:
            if 150 < len(contour) < 2500:
                silhouettes.append(contour)

        return mask, silhouettes
