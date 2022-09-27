import cv2
import numpy as np

from CameraTracker import CameraTracker
from ObjectsDetector import ObjectsDetector
from Config import Config


class FrameDistributor:
    def __init__(self, path: str, objects_detector: ObjectsDetector, camera_tracker: CameraTracker):
        self.object_detector = objects_detector
        self.camera_tracker = camera_tracker

        self.cap = cv2.VideoCapture(path)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 3600)

        self.frame = None
        self.preprocessed_frame = None

    def read(self):
        ret, self.frame = self.cap.read()
        if not ret:
            return False
        return True

    def _cut_background(self):
        kernel = np.ones((3, 3))
        out = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HLS)
        thresh = Config.get_cutting_background_threshold()
        out = cv2.inRange(out, thresh[0], thresh[1])
        out = cv2.morphologyEx(out, cv2.MORPH_OPEN, kernel=kernel, iterations=5)
        self.preprocessed_frame = cv2.morphologyEx(out, cv2.MORPH_CLOSE, kernel=kernel, iterations=7)

    def _cut_objects(self):
        # 1. Finding all the contours in specific frame
        _, thresh = cv2.threshold(self.preprocessed_frame, 1, 255, cv2.RETR_TREE)
        thresh = cv2.erode(thresh, np.ones((3, 3)), iterations=12)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        contours_on_img = sorted(contours, key=lambda cnt: cv2.contourArea(cnt), reverse=False)

        # 2. Looking for the best candidates (size criterion)
        candidate_contours = []
        for contour in contours_on_img:
            if cv2.contourArea(contour) < 10000:
                candidate_contours.append(contour)
            else:
                break

        self.preprocessed_frame = np.full_like(thresh, 255)
        cv2.drawContours(self.preprocessed_frame, candidate_contours, -1, (0, 0, 0), cv2.FILLED)

    def preprocess_frame(self):
        self._cut_background()
        self._cut_objects()

    def cut_background(self):
        self._cut_background()
        return self.preprocessed_frame.copy()

    def cut_objects(self):
        self._cut_objects()
        return self.preprocessed_frame.copy()

    def send_to_detectors(self):
        frame_with_pitch = cv2.bitwise_and(self.frame, self.frame, mask=self.preprocessed_frame)
        frame_with_footballers = cv2.bitwise_and(self.frame, self.frame, mask=np.invert(self.preprocessed_frame))

        self.object_detector.frame = frame_with_footballers
        self.camera_tracker.frame = frame_with_pitch

