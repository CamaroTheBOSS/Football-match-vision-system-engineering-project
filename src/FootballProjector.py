import cv2

from Camera import Camera


class FootballProjector:
    def __init__(self, path_to_background: str):
        self.pitch = cv2.imread(path_to_background)
        self.width, self.height = self.pitch.shape[:2]

        self.video_resolution = None
        self.footballers = []
        self.ball = None
        self.camera = Camera((280, 500), 0.95, 190, 460)

    def set_resolution(self, resolution: tuple[int, int]):
        self.video_resolution = resolution
        self.camera.set_resolution(resolution)

    def _project_coordinates(self, coordinates: tuple):
        coord = self.camera.image_coord_to_projected_coord_conversion(coordinates)
        return int(coord[0]), int(coord[1])

    # TODO Project and show for merging for loops?
    def project(self):
        for footballer in self.footballers:
            footballer.projected_center = self._project_coordinates(footballer.center)

        if self.ball is not None:
            self.ball.projected_center = self._project_coordinates(self.ball.center)

    def show(self):
        frame_to_show = self.pitch.copy()
        for footballer in self.footballers:
            footballer.project(frame_to_show, 20)
        if self.ball is not None:
            self.ball.project(frame_to_show, 10)

        self.camera.draw(frame_to_show)
        cv2.imshow("PITCH", frame_to_show)
