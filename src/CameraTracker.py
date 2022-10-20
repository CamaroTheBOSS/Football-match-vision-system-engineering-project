from operator import sub

import cv2
import numpy as np

from Config import Config
from Line import Line
from utils import do_intersect, plain_distance


def _find_intersections(vertical, horizontal):
    intersections = []
    for v_line in vertical:
        for h_line in horizontal:
            if do_intersect(v_line.ep1, v_line.ep2, h_line.ep1, h_line.ep2):
                x = (h_line.b - v_line.b) / (v_line.a - h_line.a)
                y = v_line.a * x + v_line.b
                intersections.append((x, y))

    return intersections


class CameraTracker:
    def __init__(self):
        self.original_frame = None
        self.workspace_frame = None

        self.video_resolution = (0, 0)
        Line.video_resolution = (0, 0)
        self.keypoints = []
        self.prev_keypoints = []

        self.thresh = Config.get_pitch_lines_threshold()

        self.motion = (0, 0)
        self.position = (0, 0)

    def set_video_resolution(self, resolution: tuple):
        self.video_resolution = resolution
        Line.video_resolution = resolution

    def extrude_pitch_lines(self):
        self.workspace_frame = cv2.cvtColor(self.workspace_frame, cv2.COLOR_BGR2HLS)
        self.workspace_frame = cv2.inRange(self.workspace_frame, self.thresh[0], self.thresh[1])
        return self.workspace_frame

    def detect_keypoints(self):
        horizontal, vertical = self._get_lines(self.workspace_frame)
        self.prev_keypoints = self.keypoints
        self.keypoints = _find_intersections(horizontal, vertical)
        self.keypoints = self._aggregate_keypoints()

        for line in vertical:
            cv2.line(self.original_frame, line.ep1, line.ep2, (255, 0, 0), 1)
            cv2.line(self.original_frame, line.p1, line.p2, (0, 0, 255), 1)
        for line in horizontal:
            cv2.line(self.original_frame, line.ep1, line.ep2, (255, 0, 0), 1)
            cv2.line(self.original_frame, line.p1, line.p2, (0, 0, 255), 1)
        for point in self.keypoints:
            cv2.circle(self.original_frame, tuple(map(int, point)), 10, (0, 255, 255), cv2.FILLED)
        for point in self.prev_keypoints:
            cv2.circle(self.original_frame, tuple(map(int, point)), 10, (0, 125, 255), cv2.FILLED)

        cv2.imshow("sdd", self.original_frame)

    def estimate_motion(self):
        self.motion = self._estimate_motion()

    def update(self):
        self.position = tuple(map(sum, zip(self.position, self.motion)))

    def _estimate_motion(self):
        if not len(self.prev_keypoints):
            return 0, 0

        motion_sum = (0, 0)
        n_points = 0
        for keypoint in self.keypoints:
            closest_previous_keypoints = min(self.prev_keypoints, key=lambda k: plain_distance(keypoint, k))
            d_coord = tuple(map(sub, closest_previous_keypoints, keypoint))
            if abs(d_coord[0]) + abs(d_coord[1]) < 50:
                n_points += 1
                motion_sum = tuple(map(sum, zip(motion_sum, d_coord)))

        if n_points:
            return tuple([coord / n_points for coord in motion_sum])
        else:
            return 0, 0

    def _aggregate_keypoints(self):
        aggregated_key_points = []
        while len(self.keypoints):
            selected_key_point = self.keypoints[0]
            keypoints_to_aggregate = [selected_key_point]

            # Collecting similar lines
            for point in self.keypoints:
                if abs(point[0] - selected_key_point[0]) + abs(point[1] - selected_key_point[1]) < 100:
                    keypoints_to_aggregate.append(point)

            # Aggregating collected similar lines
            n_points = len(keypoints_to_aggregate)
            if n_points > 1:
                point_sum = (0, 0)
                for point in keypoints_to_aggregate:
                    point_sum = tuple(map(sum, zip(point_sum, point)))

                point = tuple([coord / n_points for coord in point_sum])
                aggregated_key_points.append(point)

            # Deleting lines used for aggregation from main list with lines
            self.keypoints = [item for item in self.keypoints if item not in keypoints_to_aggregate]

        return aggregated_key_points

    def _get_lines(self, src):
        lines_points_form = cv2.HoughLinesP(src, 1, np.pi / 180, 50, None, 100, 50)
        horizontal = []
        vertical = []
        if lines_points_form is not None:
            for i in range(len(lines_points_form)):
                x1, y1, x2, y2 = lines_points_form[i][0]
                line = Line((x1, y1), (x2, y2))
                if line.is_horizontal():
                    horizontal.append(line)
                elif line.is_vertical():
                    vertical.append(line)

        return horizontal, vertical
