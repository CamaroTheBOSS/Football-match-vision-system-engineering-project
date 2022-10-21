import cv2

from Camera import Camera


class FootballProjector:
    def __init__(self, path_to_background: str):
        self.pitch = cv2.imread(path_to_background)
        self.frame_to_show = None
        self.width, self.height = self.pitch.shape[:2]

        self.video_resolution = None
        self.footballers = []
        self.ball = None
        self.camera = Camera((270, 420), 0.95, 170, 460)
        self.camera.projection_resolution = (self.width, self.height)
        self.projection_keypoints = [(23, 18), (319, 18), (614, 18), (23, 340), (319, 340), (614, 340),
                                     (23, 87), (127, 87), (614, 87), (510, 87),
                                     (23, 267), (127, 267), (614, 267), (510, 267),
                                     (23, 134), (70, 134), (614, 134), (567, 134),
                                     (23, 220), (70, 220), (614, 220), (567, 220), (319, 113), (319, 237)]
        self.visible_keypoints = []
        self.detected_keypoints = []

    def set_resolution(self, resolution: tuple[int, int]):
        self.video_resolution = resolution
        self.camera.set_resolution(resolution)

    def _project_coordinates(self, coordinates: tuple):
        coord = self.camera.image_coord_to_projected_coord_conversion(coordinates)
        return int(coord[0]), int(coord[1])

    def _get_visible_keypoints(self):
        self.visible_keypoints = []
        for keypoint in self.projection_keypoints:
            if keypoint[1] < self.camera.left_down_corner[1] + self.camera.offset[1]:
                if keypoint[1] > self.camera.left_up_corner[1] + self.camera.offset[1]:
                    if keypoint[1] - self.camera.offset[1] < self.camera.left.calculate_y(keypoint[0] - self.camera.offset[0]):
                        if keypoint[1] - self.camera.offset[1] < self.camera.right.calculate_y(keypoint[0] - self.camera.offset[0]):
                            self.visible_keypoints.append(keypoint)
        return self.visible_keypoints

    def _compare_detected_keypoints_with_visible(self):
        pass

    # TODO Project and show for merging for loops?
    def project(self):
        for footballer in self.footballers:
            footballer.projected_center = self._project_coordinates(footballer.center)

        if self.ball is not None:
            self.ball.projected_center = self._project_coordinates(self.ball.center)

    def show(self):
        self.frame_to_show = self.pitch.copy()
        for footballer in self.footballers:
            footballer.project(self.frame_to_show, 20)
        if self.ball is not None:
            self.ball.project(self.frame_to_show, 10)
        for keypoint in self._get_visible_keypoints():
            cv2.circle(self.frame_to_show, keypoint, 5, (0, 0, 255), cv2.FILLED)

        self.camera.draw(self.frame_to_show)
        cv2.imshow("PITCH", self.frame_to_show)
