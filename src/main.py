import os
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
        print(f"Function took {round((time2 - time1) * 1000)}ms")
        return ret

    return wrap


def get_video_type(filename):
    VIDEO_TYPE = {'avi': cv2.VideoWriter_fourcc(*'XVID'),
                  'mp4': cv2.VideoWriter_fourcc(*'XVID')}

    filename, ext = os.path.splitext(filename)
    if ext in VIDEO_TYPE:
        return VIDEO_TYPE[ext]
    return VIDEO_TYPE['avi']


class Main:
    def __init__(self, filename: str = None):
        self.RELATIVE_OUTPUT_PATH = "../output/"
        self.WAIT_KEY_TIME = Config.get_FPS()

        self.projector = FootballProjector(Config.get_pitch_graphic())
        self.football_manager = FootballManager(self.projector)

        self.objects_detector = ObjectsDetector()
        self.camera_tracker = CameraTracker(self.projector)

        self.frame_distributor = FrameDistributor("../video/" + Config.get_video(), self.objects_detector,
                                                  self.camera_tracker, self.projector)
        self.output_file = filename
        if self.output_file is not None:
            self.writer_frame = cv2.VideoWriter(self.RELATIVE_OUTPUT_PATH + self.output_file,
                                                get_video_type(self.output_file), 30, (1920, 1080))
            self.writer_projection = cv2.VideoWriter(self.RELATIVE_OUTPUT_PATH + "projection_" + self.output_file,
                                                     get_video_type(self.output_file), 30, (1920, 1080))
            self.writer_frame_and_projection = cv2.VideoWriter(self.RELATIVE_OUTPUT_PATH + "frame_and_projection_" + self.output_file,
                                                               get_video_type(self.output_file), 30, (1920, 1080))

    def main(self):
        while True:
            if not self.frame_distributor.read():
                break

            self.loop()

            if self.output_file is not None:
                self.writer_frame.write(self.camera_tracker.original_frame)
                frame = cv2.resize(self.projector.frame_to_show, (1920, 1080))
                self.writer_projection.write(frame)
                self.camera_tracker.original_frame[720:, :640, :] = self.projector.frame_to_show
                self.writer_frame_and_projection.write(self.camera_tracker.original_frame)
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
        # FOOTBALLERS DETECTION
        # 1. Preprocess got frame and send it to detectors
        self.frame_distributor.cut_background()
        self.frame_distributor.cut_objects()
        self.frame_distributor.send_to_detectors()

        # 2. Detect footballers
        self.objects_detector.look_for_objects()
        candidates = self.objects_detector.prepare_candidates()
        self.football_manager.process_candidates(candidates)

        # 3. Detect ball
        self.objects_detector.look_for_ball()
        candidates = self.objects_detector.prepare_ball_candidates()
        self.football_manager.process_ball_candidates(candidates)

        # 4. Update objects
        self.football_manager.update()

        # 5. Draw objects on the frame
        self.football_manager.draw(self.frame_distributor.frame)

        # CAMERA ESTIMATION
        # 6. Detect keypoints on the pitch
        self.camera_tracker.extrude_pitch_lines()
        self.camera_tracker.detect_keypoints()

        # 7. Estimate camera motion
        self.camera_tracker.estimate_motion()
        motion = self.camera_tracker.update()

        # FOOTBALLERS AND BALL PROJECTION
        # 8. Send footballers to projector
        self.football_manager.send_objects_to_projector()

        # 9. Move camera with estimated motion and send detected keypoints to projector
        self.camera_tracker.send_keypoints_to_projector()
        self.projector.camera.move(motion)

        # 8. Project objects into 2D pitch
        self.projector.project()
        self.projector.show()


main = Main(Config.output_file)
main.main()
