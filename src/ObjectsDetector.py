import cv2
import numpy as np

from Objects import Candidate


def get_box_and_center(object_contour: np.ndarray):
    m = cv2.moments(object_contour)
    box = cv2.boundingRect(object_contour)
    center = (int(m['m10'] / m['m00']), int(m['m01'] / m['m00'])) if m['m00'] != 0.0 else \
        tuple(coord // 2 for coord in box[0:2])

    return center, box


class ObjectsDetector:
    def __init__(self):
        self.original_frame = None
        self.workspace_frame = None
        self.mask = None
        self.objects = []
        self.candidates = []

    def get_object_color(self, ROI: list[int]):
        x, y, w, h = ROI[0] + ROI[2] // 3, ROI[1] + ROI[3] // 5, ROI[2] // 3, 3 * ROI[3] // 10
        x_vec = np.linspace(x, x + w - 1, 5, dtype=int)
        y_vec = np.linspace(y, y + h - 1, 5, dtype=int)
        probes = [self.original_frame[y, x] for x in x_vec for y in y_vec]
        divider = 0
        object_color = (0, 0, 0)
        for color in probes:
            if not np.logical_and(color[1] > color[0], color[1] > color[2]):
                object_color = tuple(map(sum, zip(object_color, color)))
                divider += 1
        if not divider:
            divider = 1
        object_color = tuple(int(color) // divider for color in object_color)
        # cv2.rectangle(self.original_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        return object_color

    def look_for_objects(self):
        # 1. Cutting silhouettes
        self.mask[np.logical_and(self.workspace_frame[:, :, 1] > self.workspace_frame[:, :, 2],
                                 self.workspace_frame[:, :, 2] > self.workspace_frame[:, :, 0])] = 255
        self.mask = cv2.erode(self.mask, (3, 3), iterations=5)

        # 2. Finding contours of silhouettes
        contours, hierarchy = cv2.findContours(self.mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        # 3. Artifacts cleaning (area criterion)
        self.objects = []
        for contour in contours:
            if 150 < len(contour) < 2500:
                self.objects.append(contour)

        return self.mask, self.objects

    def extrude_objects(self):
        self.workspace_frame = cv2.bitwise_and(self.original_frame, self.original_frame, mask=self.mask)
        return self.workspace_frame, self.mask

    def prepare_candidates(self):
        self.candidates = []
        for i, contour in enumerate(self.objects):
            center, box = get_box_and_center(contour)
            color = self.get_object_color(box)
            self.candidates.append(Candidate(i, center, box, color))
        return self.candidates

