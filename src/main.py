import time

import cv2
import numpy as np
import keyboard

from CameraTracker import CameraTracker
from FootballProjector import FootballProjector
from FrameDistributor import FrameDistributor
from ObjectsDetector import ObjectsDetector
from Points import IntersectPoint
from FootballManager import FootballManager
from Config import Config


def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print(f"Function took {round((time2 - time1)*1000)}ms")
        return ret
    return wrap


class Main:
    def __init__(self):
        self.WAIT_KEY_TIME = Config.get_FPS()

        self.projector = FootballProjector(Config.get_pitch_graphic())
        self.football_manager = FootballManager(self.projector)

        self.objects_detector = ObjectsDetector()
        self.camera_tracker = CameraTracker()

        self.frame_distributor = FrameDistributor("../video/" + Config.get_video(), self.objects_detector,
                                                  self.camera_tracker, self.projector)

    def main(self):
        while True:
            # 1. Getting frame
            if not self.frame_distributor.read():
                break

            self.loop()

            if cv2.waitKey(self.WAIT_KEY_TIME) & 0xFF == ord('q'):
                break
            if keyboard.is_pressed("d"):
                self.frame_distributor.cap_forward()
            if keyboard.is_pressed("a"):
                self.frame_distributor.cap_rewind()

        self.frame_distributor.cap.release()
        cv2.destroyAllWindows()

    # @timing
    def loop(self):
        # 2. Preprocess got frame and send it to detectors
        self.frame_distributor.cut_background()
        self.frame_distributor.cut_objects()
        self.frame_distributor.send_to_detectors()

        # 3. Detect footballers
        self.objects_detector.look_for_objects()
        candidates = self.objects_detector.prepare_candidates()
        self.football_manager.process_candidates(candidates)

        # 4. Detect ball
        self.objects_detector.look_for_ball()
        candidates = self.objects_detector.prepare_ball_candidates()
        self.football_manager.process_ball_candidates(candidates)

        # 5. Update objects
        self.football_manager.update()

        # 6. Draw objects on the frame
        self.football_manager.draw(self.frame_distributor.frame)

        # 7. Project objects into 2D pitch
        self.football_manager.send_objects_to_projector()
        self.projector.project()
        self.projector.show()
        # cv2.imshow("win", self.frame_distributor.frame)

        # =============================================================================================================
        # CAMERA MOTION ESTIMATION
        # 1. Detect pitch lines
        self.camera_tracker.extrude_pitch_lines()
        self.camera_tracker.detect_pitch_lines()

        # 2.
        # cv2.imshow("win", camera_tracker.workspace_frame)

        # # 4. If we don't catch the lines we get lines by this step
        # output = preprocessingIdea1_EXTRUDING_PITCH_LINES(output)
        #
        # # 5. Detecting pitch lines
        # empty = np.zeros_like(output)
        # houghLinesP(output, empty)  # HoughLinesP is detecting lines roughly
        # empty2 = np.zeros_like(output)
        # canny = cv2.Canny(empty, 254, 255)
        # verticalLines, horizontalLines = houghLines(canny)  # Usual HoughLines is detecting lines more precisely
        # aggregatedVerticals = aggregateLines(verticalLines)
        # aggregatedHorizontals = aggregateLines(horizontalLines)
        # displayLines(aggregatedVerticals, empty2)
        # displayLines(aggregatedHorizontals, empty2)
        #
        # # 6. Finding intersections
        # cartesianVerticals = convertPOLAR2CARTESIAN(aggregatedVerticals)
        # cartesianHorizontals = convertPOLAR2CARTESIAN(aggregatedHorizontals)
        # intersectionPoints = findIntersections(cartesianVerticals, cartesianHorizontals)
        # displayPoints(intersectionPoints, frame)

        # X. Show windows
        # cv2.imshow("frame with pitch", frame_with_pitch)
        # cv2.imshow("frame with footballers", frame_with_footballers)
        # cv2.imshow("edges", canny)
        # cv2.imshow("final lines", empty2)


main = Main()
main.main()
