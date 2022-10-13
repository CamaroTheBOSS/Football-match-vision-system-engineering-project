import cv2


class FootballProjector:
    def __init__(self, path_to_background: str):
        self.pitch = cv2.imread(path_to_background)
        self.width, self.height = self.pitch.shape[:2]

        self.video_resolution = None
        self.footballers = []
        self.ball = None

    def _project_coordinates(self, coordinates: tuple):
        x = int(coordinates[0] * self.width // self.video_resolution[0])
        y = int(coordinates[1] * self.height // self.video_resolution[1])
        return x, y

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
        cv2.imshow("PITCH", frame_to_show)
