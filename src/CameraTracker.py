import cv2
import numpy as np

from enum import Enum
from Config import Config
from utils import do_intersect


def _find_intersections(vertical, horizontal):
    intersections = []
    for v_line in vertical:
        for h_line in horizontal:
            if do_intersect(v_line.ep1, v_line.ep2, h_line.ep1, h_line.ep2):
                x = (h_line.b - v_line.b) / (v_line.a - h_line.a)
                y = v_line.a * x + v_line.b
                intersections.append((int(x), int(y)))

    return intersections


class CameraTracker:
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
                y1 = self.a * x1 + self.b
                y2 = self.a * x2 + self.b
            else:
                dP = pixels if self.p1[1] < self.p2[1] else -pixels
                y1 = self.p1[1] - dP
                y2 = self.p2[1] + dP
                x1 = (y1 - self.b) / self.a
                x2 = (y2 - self.b) / self.a
            self.ep1 = (int(x1), int(y1))
            self.ep2 = (int(x2), int(y2))

            return self.ep1, self.ep2

        def get_r_theta_form(self):
            if self.a == 0:
                self.r = self.b
                self.theta = 0
            else:
                x = self.b / (-1 / self.a - self.a)
                y = self.a * x + self.b
                self.r = np.sqrt(y**2 + x**2)  # Maybe its computationally better to use abs(y + x)
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

    def __init__(self):
        self.original_frame = None
        self.workspace_frame = None

        self.video_resolution = (0, 0)
        self.Line.video_resolution = (0, 0)
        self.keypoints = []

        self.thresh = Config.get_pitch_lines_threshold()

    def set_video_resolution(self, resolution: tuple):
        self.video_resolution = resolution
        self.Line.video_resolution = resolution

    def extrude_pitch_lines(self):
        self.workspace_frame = cv2.cvtColor(self.workspace_frame, cv2.COLOR_BGR2HLS)
        self.workspace_frame = cv2.inRange(self.workspace_frame, self.thresh[0], self.thresh[1])
        return self.workspace_frame

    def detect_keypoints(self):
        pitch_lines_roughly = np.zeros_like(self.workspace_frame)
        horizontal, vertical = self._get_lines(self.workspace_frame)
        self.keypoints = _find_intersections(horizontal, vertical)

        for line in vertical:
            cv2.line(self.original_frame, line.ep1, line.ep2, (255, 0, 0), 1)
            cv2.line(self.original_frame, line.p1, line.p2, (0, 0, 255), 1)
        for line in horizontal:
            cv2.line(self.original_frame, line.ep1, line.ep2, (255, 0, 0), 1)
            cv2.line(self.original_frame, line.p1, line.p2, (0, 0, 255), 1)
        for point in self.keypoints:
            cv2.circle(self.original_frame, point, 10, (0, 255, 255), cv2.FILLED)

        cv2.imshow("wind2", pitch_lines_roughly)
        cv2.imshow("sdd", self.original_frame)

    def _get_lines(self, src):
        lines_points_form = cv2.HoughLinesP(src, 1, np.pi / 180, 50, None, 100, 50)
        horizontal = []
        vertical = []
        if lines_points_form is not None:
            for i in range(len(lines_points_form)):
                x1, y1, x2, y2 = lines_points_form[i][0]
                line = self.Line((x1, y1), (x2, y2))
                if line.is_horizontal():
                    horizontal.append(line)
                elif line.is_vertical():
                    vertical.append(line)

        return horizontal, vertical
