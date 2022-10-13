import cv2
import numpy as np

from Config import Config
from Objects import Candidate
from utils import color_distance


def get_box_and_center(object_contour: np.ndarray):
    m = cv2.moments(object_contour)
    box = cv2.boundingRect(object_contour)
    center = (int(m['m10'] / m['m00']), int(m['m01'] / m['m00'])) if m['m00'] != 0.0 else \
        tuple(coord // 2 for coord in box[0:2])

    return center, box


def circularity_score(contour):
    (sx, sy), r = cv2.minEnclosingCircle(contour)
    circleArea = np.pi * r ** 2
    shapeArea = cv2.contourArea(contour)
    if shapeArea == 0:
        return 0
    return 1000 * shapeArea / circleArea


class ObjectsDetector:
    def __init__(self):
        self.original_frame = None
        self.workspace_frame = None
        self.ball_frame = None
        self.mask = None

        self.objects = []
        self.ball_objects = []

        self.candidates = []
        self.ball_candidates = []

        self.BALL_COLOR = Config.get_BALL_COLOR()

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

    def get_ball_color(self, ROI: list[int]):
        x, y, w, h = ROI[0] + ROI[2] // 5, ROI[1] + ROI[3] // 5, 3 * ROI[2] // 5, 2 * ROI[3] // 5
        x_vec = np.linspace(x, x + w - 1, 10, dtype=int)
        y_vec = np.linspace(y, y + h - 1, 10, dtype=int)
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

        return object_color

    def look_for_ball(self):
        self.ball_frame = cv2.erode(self.ball_frame, (5, 5), iterations=5)
        contours, hierarchy = cv2.findContours(self.ball_frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        self.ball_objects = []
        for contour in contours:
            if 100 < cv2.contourArea(contour) < 350:
                self.ball_objects.append(contour)
        return self.ball_objects

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

    def _determine_ball_score(self, candidate: Candidate):
        # 1. Get ROI
        box = candidate.box
        ROI = self.original_frame[box[1]:box[1] + box[3], box[0]:box[0] + box[2]]
        if any(ROI.shape) == 0:
            return -1

        # 2. Preprocess ROI
        gray_ROI = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
        blurred_ROI = cv2.blur(gray_ROI, (3, 3))
        canny = cv2.Canny(blurred_ROI, 100, 200)

        # 3. Find contours
        contours, hierarchy = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours = sorted(contours, key=lambda cnt: cv2.contourArea(cnt), reverse=True)
        contours = contours[:1]

        score = 0
        if len(contours):
            score = circularity_score(contours[0]) - color_distance(self.BALL_COLOR, candidate.color)

        candidate.distance = score
        return score

    def prepare_ball_candidates(self):
        self.ball_candidates = []
        for contour in self.ball_objects:
            center, box = get_box_and_center(contour)
            color = self.get_ball_color(box)
            candidate = Candidate(0, center, box, color)
            self._determine_ball_score(candidate)
            if candidate.distance >= 500:
                self.ball_candidates.append(candidate)

        self.ball_candidates.sort(key=lambda c: c.distance, reverse=True)
        return self.ball_candidates
