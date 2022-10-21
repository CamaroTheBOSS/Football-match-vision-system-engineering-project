import time

import cv2
import keyboard

from CameraTracker import CameraTracker
from FootballProjector import FootballProjector
from FrameDistributor import FrameDistributor
from ObjectsDetector import ObjectsDetector
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
        self.camera_tracker.detect_keypoints()
        self.camera_tracker.estimate_motion()
        self.camera_tracker.update()
        # print(self.camera_tracker.position)


main = Main()
main.main()
