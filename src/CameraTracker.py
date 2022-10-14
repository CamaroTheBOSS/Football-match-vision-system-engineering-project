import cv2
import numpy as np

from enum import Enum
from Config import Config
from Points import IntersectPoint


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
            self.ip1 = None
            self.ip2 = None

            # r, theta form
            self.r = None
            self.theta = None

            self.orientation = self.Orientation.undefined

            self.get_analytic_form()
            self.get_border_form()
            self.get_r_theta_form()
            self.get_line_orientation()

        def get_analytic_form(self):
            x1, y1 = self.p1
            x2, y2 = self.p2
            self.a = (y2 - y1) / (x2 - x1) if (x2 != x1) else 10000
            self.b = y1 - self.a * x1
            return self.a, self.b

        def get_border_form(self):
            width, height = self.video_resolution
            intersect_points = []
            # Left edge intersection
            if 0 <= self.b <= height:
                intersect_points.append((0, int(self.b)))

            # Right edge intersection
            y = self.a * width + self.b
            if 0 <= y <= height:
                intersect_points.append((int(width), int(self.b)))

            if self.a != 0:
                # Upper edge intersection
                x = -self.b / self.a  # 0 = ax + b
                if 0 <= x <= width:
                    intersect_points.append((int(x), 0))

                # Bottom edge intersection
                x = (height - self.b) / self.a
                if 0 <= x <= width:
                    intersect_points.append((int(x), int(height)))

            self.ip1 = tuple(map(int, intersect_points[0]))
            self.ip2 = tuple(map(int, intersect_points[1]))
            return self.ip1, self.ip2

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

        self.thresh = Config.get_pitch_lines_threshold()

    def set_video_resolution(self, resolution: tuple):
        self.video_resolution = resolution
        self.Line.video_resolution = resolution

    def extrude_pitch_lines(self):
        self.workspace_frame = cv2.cvtColor(self.workspace_frame, cv2.COLOR_BGR2HLS)
        self.workspace_frame = cv2.inRange(self.workspace_frame, self.thresh[0], self.thresh[1])
        return self.workspace_frame

    def detect_pitch_lines(self):
        pitch_lines_roughly = np.zeros_like(self.workspace_frame)
        horizontal, vertical = self._get_lines(self.workspace_frame)
        # horizontal = self.aggregate_lines(horizontal)
        # vertical = self.aggregate_lines(vertical)

        for line in horizontal:
            cv2.line(pitch_lines_roughly, line.p1, line.p2, (255, 255, 255), 1)
            cv2.putText(pitch_lines_roughly, str(round(line.a, 1)), line.p1, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        for line in vertical:
            cv2.line(pitch_lines_roughly, line.p1, line.p2, (255, 255, 255), 1)
            cv2.putText(pitch_lines_roughly, str(round(line.theta, 1)), line.p1, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # pitch_lines_stable = cv2.Canny(pitch_lines_roughly, 254, 255)

        # verticalLines, horizontalLines = self.houghLines(pitch_lines_stable)  # Usual HoughLines is detecting lines more precisely
        # aggregatedVerticals = self.aggregateLines(verticalLines)
        # aggregatedHorizontals = self.aggregateLines(horizontalLines)
        # self.displayLines(aggregatedVerticals, pitch_lines_stable)
        # self.displayLines(aggregatedHorizontals, pitch_lines_stable)
        cv2.imshow("wind", self.workspace_frame)
        cv2.imshow("wind2", pitch_lines_roughly)

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

    def aggregate_lines(self, lines):
        # Aggregation algorithm
        aggregated_lines = []
        while len(lines):
            selected_line = lines[0]
            lines_to_aggregate = [selected_line]

            # Collecting similar lines
            for line in lines:
                if abs(selected_line.r - line.r) < 80 and abs(selected_line.theta - line.theta) < 0.15:
                    lines_to_aggregate.append(line)

            # Aggregating collected similar lines
            n_lines = len(lines_to_aggregate)
            if n_lines > 1:
                ip1_sum = (0, 0)
                ip2_sum = (0, 0)
                for line in lines_to_aggregate:
                    ip1_sum = tuple(map(sum, zip(ip1_sum, line.ip1)))
                    ip2_sum = tuple(map(sum, zip(ip2_sum, line.ip2)))

                ip1 = tuple([coord / n_lines for coord in ip1_sum])
                ip2 = tuple([coord / n_lines for coord in ip2_sum])
                aggregated_lines.append(self.Line(ip1, ip2))

            # Deleting lines used for aggregation from main list with lines
            lines = [item for item in lines if item not in lines_to_aggregate]

        return aggregated_lines

    def displayLines(self, lines, dst):
        # Display lines
        for r, theta in lines:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * r
            y0 = b * r
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * a))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * a))
            cv2.line(dst, pt1, pt2, (255, 255, 255), 3, cv2.LINE_AA)

    def convertPOLAR2CARTESIAN(self, lines):
        cartesian = []
        for r, theta in lines:
            a0 = np.cos(theta)
            b0 = np.sin(theta)

            # "Center" point of the line
            x0 = a0 * r
            y0 = b0 * r

            # Points of the line
            pt1 = (int(x0 - 1000 * b0), int(y0 + 1000 * a0))
            pt2 = (int(x0 + 1000 * b0), int(y0 - 1000 * a0))

            a = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0]) if (pt2[0] - pt1[0]) != 0 else 10000
            b = pt1[1] - a * pt1[0]
            cartesian.append([a, b])
        return cartesian

    def findIntersections(self, vertical, horizontal):
        intersections = []
        for av, bv in vertical:
            for ah, bh in horizontal:
                if av != ah:
                    x = (bh - bv) / (av - ah)
                    y = av * x + bv
                    intersections.append(IntersectPoint((int(x), int(y))))
        return intersections

    def displayPoints(self, points, dst):
        for point in points:
            cv2.circle(dst, point.coord, 10, (255, 0, 0), -1)


